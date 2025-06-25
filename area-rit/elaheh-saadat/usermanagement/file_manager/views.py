import h5py
import os
import io
import time
import numpy as np
import json
import traceback
import base64
import zipfile
from PIL import Image
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse, HttpResponse

METADATA_DIR = os.path.join(settings.BASE_DIR, "file_manager", "data")
LOCAL_STORAGE_DIR = os.path.join(settings.BASE_DIR, "local_storage")

def get_user_role(user):
    """Determine if the user is an admin or a regular user."""
    if user.groups.filter(name='admin user').exists():
        return 'admin'
    return 'regular'

def user_login(request):
    """Login view"""
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            user_role = get_user_role(user)

            # Redirect based on role
            if user_role == "admin":
                return redirect('admin_dashboard')
            else:
                return redirect('regular_dashboard')
        else:
            return render(request, 'file_manager/login.html', {'error': 'Invalid credentials'})

    return render(request, 'file_manager/login.html')

@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    return render(request, 'file_manager/admin_dashboard.html', {'username': request.user.username})

@login_required
def regular_dashboard(request):
    """Regular user dashboard view"""
    return render(request, 'file_manager/regular_dashboard.html', {'username': request.user.username})

def user_logout(request):
    """Logout view"""
    logout(request)
    return redirect('login')  # Redirect to login after logout

def homepage_view(request):
    return render(request, 'file_manager/homepage.html')

def load_metadata_schema(schema_filename):
    schema_path = os.path.join(METADATA_DIR, schema_filename)
    with open(schema_path, "r") as f:
        schema = json.load(f)
    return schema

def parse_hdr_file(file_path):
    instrument_data = {}
    with open(file_path, 'r') as f:
        current_section = None
        for line in f:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
            elif '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                full_key = f"{current_section}.{key}" if current_section else key
                instrument_data[full_key] = value
    return instrument_data

def create_nexus_file_from_schema(nexus_file_path, schema, instrument_data, image_paths=None):
    if image_paths is None:
        image_paths = []
    with h5py.File(nexus_file_path, 'w') as f:
        root_group = f.create_group("entry")
        root_group.attrs['NX_class'] = 'NXentry'

        apply_schema(root_group, schema, instrument_data)

        if image_paths:
            images_group = root_group.create_group("images")
            images_group.attrs["NX_class"] = "NXdata"
            for i, img_path in enumerate(image_paths):
                with open(img_path, 'rb') as img_file:
                    img_data = img_file.read()
                dataset_name = f"image_data_{i}"
                images_group.create_dataset(dataset_name, data=np.frombuffer(img_data, dtype=np.uint8))

    print(f"NeXus file '{nexus_file_path}' created with {len(image_paths)} image(s).")

def apply_schema(hdf_group, schema_node, instrument_data, node_name=None):
    if node_name is None:
        children = schema_node.get("children", {})
        for child_name, child_node in children.items():
            apply_schema(hdf_group, child_node, instrument_data, node_name=child_name)
        return

    status = schema_node.get("status", "optional")
    mapping = schema_node.get("mapping")
    children = schema_node.get("children", {})
    nx_class = schema_node.get("NX_class", "NXgroup")

    if not children:
        if mapping:
            if mapping in instrument_data:
                hdf_group.create_dataset(node_name, data=instrument_data[mapping])
            elif status == "required":
                raise ValueError(
                    f"Missing required field '{node_name}' (mapping: '{mapping}') in instrument data."
                )
            elif status == "recommended":
                print(
                    f"Warning: Recommended field '{node_name}' (mapping: '{mapping}') is missing in instrument data."
                )
        else:
            if status == "required":
                raise ValueError(
                    f"Missing required field '{node_name}' in schema. No mapping provided."
                )
            elif status == "recommended":
                print(f"Warning: Recommended field '{node_name}' has no mapping defined in schema.")
    else:
        child_group = hdf_group.create_group(node_name)
        child_group.attrs["NX_class"] = nx_class
        for child_name, child_node in children.items():
            apply_schema(child_group, child_node, instrument_data, node_name=child_name)

def new_experiment_view(request):
    if request.method == 'POST':
        experiment_type = request.POST.get('experiment_type', '')
        operator_name = request.POST.get('operator_name', '')
        description = request.POST.get('description', '')
        schema_file_name = request.POST.get('schema_file_name', '')

        material = request.POST.get('material', '')
        hypothetical_composition = request.POST.get('hypothetical_composition', '')
        initial_composition = request.POST.get('initial_composition', '')
        final_composition = request.POST.get('final_composition', '')


        # If "Other" is selected, get the custom material input
        if material == "Other":
            material = request.POST.get('custom_material', '')

        if not schema_file_name:
            return JsonResponse({"status": "error", "message": "No schema selected."}, status=400)

        hdr_file = request.FILES.get('hdr_file')
        if not hdr_file:
            return JsonResponse({"status": "error", "message": "HDR file missing."}, status=400)

        image_files = request.FILES.getlist('image_files')
        if not image_files:
            return JsonResponse({"status": "error", "message": "No image files uploaded."}, status=400)

        hdr_path = f"/tmp/{hdr_file.name}"
        with open(hdr_path, 'wb') as temp_hdr:
            for chunk in hdr_file.chunks():
                temp_hdr.write(chunk)

        image_paths = []
        for img in image_files:
            img_path = f"/tmp/{img.name}"
            with open(img_path, 'wb') as temp_img:
                for chunk in img.chunks():
                    temp_img.write(chunk)
            image_paths.append(img_path)

        try:
            instrument_data = parse_hdr_file(hdr_path)

            experiment_fields = {
                "experiment_type": experiment_type,
                "operator_name": operator_name,
                "description": description,
                "material": material,  # Add material to the experiment fields
                "hypothetical_composition": hypothetical_composition,
                "initial_composition": initial_composition,
                "final_composition": final_composition,
            }
            instrument_data.update(experiment_fields)

            schema = load_metadata_schema(schema_file_name)

            unique_filename = f"{experiment_type.replace(' ', '_')}_{int(time.time())}.nxs"
            nexus_file_path = f"/tmp/{unique_filename}"

            create_nexus_file_from_schema(nexus_file_path, schema, instrument_data, image_paths=image_paths)

            if not os.path.exists(nexus_file_path):
                raise FileNotFoundError(f"NeXus file '{nexus_file_path}' was not created.")

            destination_path = os.path.join(LOCAL_STORAGE_DIR, unique_filename)
            os.rename(nexus_file_path, destination_path)
            print("File saved to local storage:", destination_path)

        except Exception as e:
            print(f"Error during NeXus file creation or upload: {traceback.format_exc()}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

        finally:
            if os.path.exists(hdr_path):
                os.remove(hdr_path)
            for img_path in image_paths:
                if os.path.exists(img_path):
                    os.remove(img_path)

        return render(request, 'file_manager/upload_success.html', {'filename': unique_filename})

    else:
        schema_files = [f for f in os.listdir(METADATA_DIR) if f.endswith(".json")]
        materials = ["Suggestion 1", "Suggestion 2", "Suggestion 3" , "Other"]
        experiment_types = ["TEM", "SEM", "FIB-SEM"]
        return render(request, 'file_manager/new_experiment.html', {'schema_files': schema_files, 'materials': materials, 'experiment_types': experiment_types})

def list_metadata_files_view(request):
    files = [f for f in os.listdir(METADATA_DIR) if f.endswith(".json")]
    selected_file = request.GET.get("file_name")
    metadata = None

    if selected_file:
        file_path = os.path.join(METADATA_DIR, selected_file)
        with open(file_path, "r") as file:
            metadata = json.load(file)

    return render(request, "file_manager/list_metadata_files.html", {
        "files": files,
        "selected_file": selected_file,
        "metadata": json.dumps(metadata) if metadata else "null",
    })

def edit_metadata_view(request, file_name):
    file_path = os.path.join(METADATA_DIR, file_name)
    with open(file_path, "r") as file:
        metadata = json.load(file)

    return render(request, "file_manager/edit_metadata.html", {"metadata": metadata, "file_name": file_name})

def save_metadata_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        new_metadata = data.get("metadata", {})
        file_name = data.get("file_name", "new_metadata.json")
        overwrite = data.get("overwrite", False)

        file_path = os.path.join(METADATA_DIR, file_name)

        if not overwrite and os.path.exists(file_path):
            return JsonResponse({"status": "error", "message": f"File '{file_name}' already exists!"})

        with open(file_path, "w") as file:
            json.dump(new_metadata, file, indent=4)

        return JsonResponse({"status": "success", "message": f"Metadata saved to {file_name}!"})

    return JsonResponse({"status": "error", "message": "Invalid request!"})

def create_nexus_file(nexus_file, metadata_path, image_path):
    with open(metadata_path, 'r') as meta_file:
        metadata = meta_file.read()

    with h5py.File(nexus_file, 'w') as f:
        metadata_group = f.create_group("metadata")
        metadata_group.create_dataset("header", data=metadata)

        image_group = f.create_group("image")
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
        image_group.create_dataset("image_data", data=np.void(img_data))

    print(f"Nexus file '{nexus_file}' created.")

def list_files_view(request):
    try:
        files = [f for f in os.listdir(LOCAL_STORAGE_DIR) if f != ".gitkeep"]
    except FileNotFoundError:
        return HttpResponse("Local storage directory not found.", status=500)

    return render(request, 'file_manager/file_list.html', {'files': files})

@login_required
def view_file_view(request, file_name):
    file_path = os.path.join(LOCAL_STORAGE_DIR, file_name)

    if not os.path.exists(file_path):
        return HttpResponse(f"File '{file_name}' not found.", status=404)

    try:
        with open(file_path, "rb") as f:
            with h5py.File(f, "r") as h5_file:
                image_data_list = []

                if "entry/image/image_data" in h5_file:
                    image_data = bytes(h5_file["entry/image/image_data"][:])
                    image = Image.open(io.BytesIO(image_data))
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG")
                    buffer.seek(0)
                    image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    image_data_list.append(image_b64)

                elif "entry/images" in h5_file:
                    images_group = h5_file["entry/images"]
                    for ds_name in images_group:
                        img_data = bytes(images_group[ds_name][:])
                        image = Image.open(io.BytesIO(img_data))
                        buffer = io.BytesIO()
                        image.save(buffer, format="PNG")
                        buffer.seek(0)
                        image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        image_data_list.append(image_b64)
                else:
                    image_data_list = []

        return render(request, 'file_manager/view_file.html', {
            'file_name': file_name,
            'image_data_list': image_data_list,
        }, {'username': request.user.username})

    except KeyError as e:
        return HttpResponse(f"KeyError: {e}", status=500)
    except Exception as e:
        return HttpResponse(f"An unexpected error occurred: {e}", status=500)

def download_file_view(request, file_name):
    file_path = os.path.join(LOCAL_STORAGE_DIR, file_name)

    if not os.path.exists(file_path):
        return HttpResponse(f"File '{file_name}' not found.", status=404)

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()

        if request.GET.get("image") == "true":
            with h5py.File(io.BytesIO(file_data), "r") as h5_file:
                if "entry/image/image_data" in h5_file:
                    image_data = h5_file["entry/image/image_data"][()]
                    buffer = io.BytesIO()
                    image = Image.open(io.BytesIO(image_data))
                    image.save(buffer, format="PNG")
                    buffer.seek(0)
                    return FileResponse(buffer, as_attachment=True, filename="extracted_image.png")

                if "entry/images" in h5_file:
                    images_group = h5_file["entry/images"]
                    image_keys = list(images_group.keys())
                    if not image_keys:
                        return HttpResponse("No image datasets found in 'entry/images'.", status=404)

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for i, ds_name in enumerate(image_keys):
                            image_data = images_group[ds_name][()]
                            image = Image.open(io.BytesIO(image_data))
                            img_buffer = io.BytesIO()
                            image.save(img_buffer, format="PNG")
                            img_buffer.seek(0)
                            zipf.writestr(f"image_{i}.png", img_buffer.getvalue())

                    zip_buffer.seek(0)
                    return FileResponse(
                        zip_buffer,
                        as_attachment=True,
                        filename="all_images.zip"
                    )
                else:
                    return HttpResponse("No image data found in this Nexus file.", status=404)

        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=file_name)

    except Exception as e:
        return HttpResponse(f"An error occurred while processing the file: {e}", status=500)

def delete_file_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        file_name = data.get('file_name')
        file_path = os.path.join(METADATA_DIR, file_name)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return JsonResponse({'success': True, 'message': f'{file_name} has been deleted.'})
            else:
                return JsonResponse({'success': False, 'message': f'File {file_name} does not exist.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

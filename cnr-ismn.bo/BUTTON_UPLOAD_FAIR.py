import datetime
import platform
from pprint import pprint
from cams2nomad import cams2nomad
import API_collection as api
from pathlib import Path
from jam.db.db_modules import SQLITE
import json
from datetime import datetime, date, timezone
import shutil

'''
def copy_db(task):
    task.copy_database(SQLITE, '/home/jampy/cams/cleanroom.sqlite')
'''
def update_ids_file(entry_dict: dict, file_path: Path):
    """
    Update the IDs.json file with new entry_dict data following the given schema.
    If the file exists, it's updated; otherwise, it's created.
    """
    # Ensure the parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data from the file if it exists and is valid JSON
    if file_path.exists():
        try:
            existing_data = json.loads(file_path.read_text(encoding="utf-8"))
            if not isinstance(existing_data, dict):
                existing_data = {}  # Reset if the file content is not a dictionary
        except json.JSONDecodeError:
            existing_data = {}  # Reset if the file content is invalid JSON
    else:
        existing_data = {}

    # Extract the only key from entry_dict
    first_key = next(iter(entry_dict))

    # Prepare the new data structure
    new_data = {"upload_steps_id": entry_dict[first_key]}
    new_data.update(entry_dict)

    # Update the existing data with the new data
    existing_data.update(new_data)

    # Save the updated data back to the file
    file_path.write_text(json.dumps(existing_data, indent=4), encoding="utf-8")


def serialize_value(value):
    if isinstance(value, (datetime,)):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(value, (date,)):
        return value.strftime("%Y-%m-%d")
    return value

def get_step_type(item, step_type):
    st = item.task.step_type.copy()
    st.set_where(id=step_type)
    st.open()
    if st.rec_count:
        return st.step_type.value

def get_process_dict(run):
    """
    Given an open run, the function returns a standardized dict that gather all process params.
    The trailing 'steps' list will be filled in another function
    """
    return {
        "m_def": "fabrication_facilities.schema_packages.fabrication_utilities.FabricationProcess",
        "name": run.run_name.display_text,
        "id_proposal": run.pid.display_text,
        "project": run.project.display_text,
        #"workpackage": run.workpackage.display_text,
        "description": run.run_description.display_text,
        "author": run.author.display_text,
        "cost_model": run.cost_model.display_text,
        "affiliation": run.pnrr_project.display_text,
        "start_date": serialize_value(run.start_date.value),
        #"generated_on": serialize_value(datetime.now()),
        "steps": [],
    }
    
def get_base_step_dict(step):
    # step_number = step.step_number.display_text
    step_room_comments = step.room_comments.display_text
    step_important_notes = step.important.display_text
    step_comments_before = step.comments.display_text
    step_comments_after = step.comments_after.display_text
    all_comments = (
        f"<ul> <li>{step.important.field_caption}</li> </ul> <p>{step_important_notes}</p> "
        f"<ul> <li>{step.comments.field_caption}</li> </ul> <p>{step_comments_before}</p> "
        f"<ul> <li>{step.comments_after.field_caption}</li> </ul> <p>{step_comments_after}</p> "
        f"<ul> <li>{step.room_comments.field_caption}</li> </ul> <p>{step_room_comments}</p> "
    )
    # Convert to the desired format (ISO 8601 with microseconds and timezone)
    equipment_start_time, equipment_end_time = tuple(
        t.replace(tzinfo=timezone.utc).isoformat() if t is not None else None
        for t in (step.equipment_start_time.value, step.equipment_end_time.value)
    )
    return {
        "name" : step.description.display_text,
        "operator" : step.operator.display_text,
        "id_items_processed" : step.wafers.display_text, # IF A LIST OF STRING IS NEEDED : [id.strip() for id in step.wafers.display_text.split(',') if id.strip()]
        "room" : step.room.display_text,
        "start_date" : equipment_start_time,
        "end_date" : equipment_end_time,
        "step_type" : step.step_type.display_text,
        "notes" : all_comments,
    }
     
def enrich_step(item, s, step_data, exclude_list):
    
    print("Valore restituito da s.step_type.display_text:", s.step_type.display_text)

    step_type = get_step_type(s, s.step_type.value)
    step = s.task.item_by_ID(step_type).copy()
    step.set_where(id=s.step_rec_id.value)
    step.open()

    st = item.task.catalogs.step_type.copy()
    st.set_where(step_type=step_type)
    st.open()
    step_fieldlist = st.field_order.value.split(", ")[:-1]
    print(step_fieldlist)
    
    """ OLD DICT WITH THE KEY EQUAL TO THE CAPTION, THE NEW ONE HAS THE KEY EQUAL TO THE VARIABLE
    step_specific_info = {
        field.field_caption: field.lookup_text if field.lookup_text else field.value
        for field_name in step_fieldlist
        if (field := step.field_by_name(field_name))
        and not field.system_field()
        and field.field_name not in exclude_list
    }
    pprint(step_specific_info)
    print('\n\n')
    """
    step_specific_info = {
        field_name: field.lookup_text if field.lookup_text else field.value
        for field_name in step_fieldlist
        if (field := step.field_by_name(field_name))
        and not field.system_field()
        and field.field_name not in exclude_list
    }
    pprint(step_specific_info)
    print("\n\n")
    # put the 'note' or 'comment' field in the 'all_comments' var
    field = x if (x := step.field_by_name('note')) else step.field_by_name('comments')
    step_note = field.lookup_text if field.lookup_text else field.value
    step_note = f"<ul> <li>Step notes</li> </ul> <p>{step_note}</p> "
    step_data["notes"] = step_note + step_data["notes"]

    step_data["m_def"] = cams2nomad.get(s.step_type.display_text)["m_def"]
    return step_data, step_specific_info
    
def enrich_step2(item, s, step_data, exclude_list):
    step_type = get_step_type(s, s.step_type.value)
    step = s.task.item_by_ID(step_type).copy()
    step.set_where(id=s.step_rec_id.value)
    step.open()
    print(s.step_type.display_text)
    print(step_type)
    st = item.task.catalogs.step_type.copy()
    st.set_where(step_type=step_type)
    st.open()
    step_fieldlist = st.field_order.value.split(", ")[:-1]
    print(step_fieldlist)
    
    """ OLD DICT WITH THE KEY EQUAL TO THE CAPTION, THE NEW ONE HAS THE KEY EQUAL TO THE VARIABLE
    step_specific_info = {
        field.field_caption: field.lookup_text if field.lookup_text else field.value
        for field_name in step_fieldlist
        if (field := step.field_by_name(field_name))
        and not field.system_field()
        and field.field_name not in exclude_list
    }
    pprint(step_specific_info)
    print('\n\n')
    """
    step_specific_info = {
        field_name: field.field_caption
        for field_name in step_fieldlist
        if (field := step.field_by_name(field_name))
        and not field.system_field()
        and field.field_name not in exclude_list
    }
    pprint(step_specific_info)
    print('\n')
    # put the 'note' or 'comment' field in the 'all_comments' var
    field = x if (x := step.field_by_name('note')) else step.field_by_name('comments')
    step_note = field.lookup_text if field.lookup_text else field.value
    step_note = f"<ul> <li>Step notes</li> </ul> <p>{step_note}</p> "
    all_comments = step_note + step_data["notes"]
    step_data["notes"] = all_comments

    return step_data, step_specific_info

def transform_data(s, step_data, step_specific_info):
    # fetch the mapping for nomad names for this step type
    step_info = cams2nomad.get(s.step_type.display_text)
    if step_info is None:
        return None
    step_mapping = step_info["mapping"]
    # fetch the transformations needed for the parameters in this step_type, if exist
    step_transforms = step_info.get("transformations", {})

    for new_key, old_key in step_mapping.items():
        value = step_specific_info.get(old_key)
        # If a transformation exists for this key, apply it.
        if new_key in step_transforms:
            step_data[new_key] = step_transforms[new_key](value)
        else:
            # Otherwise, just assign the fetched value.
            step_data[new_key] = value
    
    return step_data

def upload_fair(item, run_id):
    print(f"Uploading FAIR data for run_id: {run_id}")
    upload = True
    main_path = Path('static') / 'FAIR'
    main_path.mkdir(parents=True, exist_ok=True)
    success_path = main_path / 'SUCCCESS'
    success_path.mkdir(parents=True, exist_ok=True)
    
    # Retrieve the run record
    run = item.task.run.copy()
    run.set_where(id=run_id)
    run.open()
    
    if not run.rec_count:
        print("Error: No data found for this run_id")
        return
    
    # Prepare the folder for this process only if it doesn't already exist in success_path
    process_name = run.run_name.display_text  # The name of the folder to be created
    process_path = main_path / process_name
    
    # Check if the folder already exists in the success_path
    if not (success_path / process_name).exists():
        process_path.mkdir(parents=True, exist_ok=True)
        print(f"Folder '{process_name}' created successfully in '{main_path}'.")
    else:
        print(f"Folder '{process_name}' already exists in '{success_path}', skipping creation and no uploading.")
        return
    
    # Prepare JSON data structure
    process_dict = get_process_dict(run)

    # Retrieve steps associated with the run
    steps = run.steps
    steps.open(order_by=['step_number'])
    
    
    exclude_list = ['note', 'comments']
    print(f"Chiavi disponibili in cams2nomad:\n{list(cams2nomad.keys())}\n")

    # Prepare the folder for the steps
    steps_path = process_path / f"{process_path.name}_steps"
    steps_path.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(steps):
        # Get the common parameters
        step_data = get_base_step_dict(s)
        # Get the specific parameters, and update the 'notes' field in 'step_data'
        step_data, step_specific_info = enrich_step(item, s, step_data, exclude_list)
        # just to get caption and variable name, TO BE DELETED
        #step_data, step_specific_info = enrich_step2(item, s, step_data, exclude_list)
        
        # Transform the params names to the NOMAD vocab, based on step type        
        step_data = transform_data(s, step_data, step_specific_info)
        if step_data is None:
            continue # i.e. the step_type is not mapped
        # CORRECTION TO AVOID ERRORS: remove nulls
        step_data = {k: v for k, v in step_data.items() if v is not None}

        # If we want just a single file report in static/report, simply put the 
        # step dict in the 'step' key of the process dict
        if not upload:
            process_dict["steps"].append(step_data)
            continue
        
        # format the data for NOMAD
        step_data = {"data": step_data}
        # save the dict in a dedicated file
        file_step = steps_path / f"{s.step_number.display_text}.archive.json"
        file_step.write_text(json.dumps(step_data, indent=4), encoding="utf-8")
        
        # DELETE THE NEXT LINE WHEN UPLOAD ID WILL BE FETCHED
        #process_dict["steps"].append(f"{s.step_number.display_text}.archive.json")

        #break # to work with just one step, for now.. 
    if not upload:    
        json_file_path = f'static/reports/{process_name}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S%f")}.json'
        with open(json_file_path, 'w') as json_file:
            json_file.write(json_output)
        
    # ---------------    UPLOAD STEP PHASE    ---------------
    print("\n\n ------ UPLOAD PHASE ------ \n\n")
    #create zip file to upload
    zip_file_name = process_path / f"{steps_path.name}_zpd" # name of the zip file (without the extension)
    #shutil.make_archive(str(zip_file_name), 'zip', root_dir=steps_path, base_dir=steps_path.name)
    shutil.make_archive(str(zip_file_name), 'zip', root_dir=steps_path.parent, base_dir=steps_path.name)
    zip_file_path = zip_file_name.with_suffix('.zip')

    if(entry_dict:=api.upload_file(zip_file_path, autodelete=False)) is None: 
        print('Some entries have bugs...')
        return

    print(entry_dict)
    ids_file = process_path / "IDs.json"
    update_ids_file(entry_dict, ids_file)
    # ---------------    UPDATE FATHER    ---------------
    print("\n\n ------ UPDATE FATHER ------ \n\n")
    process_dict["steps"] = [
        f"../uploads/{upload_id}/archive/{entry_id}#data"
        for upload_id, entries in entry_dict.items()
        for entry_id in entries.values()
    ]
    # format the data for NOMAD
    process_dict = {"data": process_dict}
    # save the dict in a dedicated file
    file_process = process_path / f"{process_name}.archive.json"
    file_process.write_text(json.dumps(process_dict, indent=4), encoding="utf-8")
    # ---------------    UPDLOAD FATHER    ---------------
    if(father_entry:=api.upload_file(file_process, autodelete=False)) is None: # -----------   IMPORT API COLLECTION!!!! E PASSARE ARGOMENTI
        print('Some entries have bugs...')
        return        
    update_ids_file(father_entry, ids_file)
    #---------------------  output file   -------------------------------
    # json_output = json.dumps(process_dict, indent=4, default=str)
    # print(f'\n\nJSON FILE PREVIEW:\n{json_output}')
    print('\n\n' + '*'*60 + f'\n*{" " * 15}THE UPLOAD PROCESS SUCCEEDED{" " * 15}*\n' + '*'*60 + '\n')
    return    


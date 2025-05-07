import h5py
import os
import html
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import webbrowser
import numpy as np
from PIL import Image


def format_attribute_value(val):
    try:
        if isinstance(val, bytes):
            val = val.decode('utf-8')
        elif isinstance(val, (np.ndarray, list, tuple)):
            val = list(val)
        elif isinstance(val, str):
            pass
        elif isinstance(val, (int, float)):
            pass
        else:
            val = str(val)
    except Exception:
        val = str(val)

    val_str = str(val)
    if val_str.startswith(("'", '"')) and val_str.endswith(("'", '"')):
        val_str = val_str[1:-1]
    return val_str


def get_attribute_type_description(attr_value, hdf5_file):
    if isinstance(attr_value, h5py.Reference):
        try:
            ref_obj = hdf5_file[attr_value]
            if isinstance(ref_obj, h5py.Group):
                return f"HDF5 object reference → Group '{ref_obj.name}'"
            elif isinstance(ref_obj, h5py.Dataset):
                return f"HDF5 object reference → Dataset '{ref_obj.name}'"
            else:
                return f"HDF5 object reference → Unknown object '{ref_obj.name}'"
        except (TypeError, KeyError):
            return "HDF5 object reference → <invalid reference>"

    py_type = type(attr_value)
    if hasattr(attr_value, 'dtype') and hasattr(attr_value, 'shape'):
        return "NumPy Array"
    if py_type is bytes:
        return "Bytes"
    elif py_type is str:
        return "String"
    elif py_type is int:
        return "Integer"
    elif py_type is float:
        return "Float"
    else:
        return py_type.__name__


def get_type_color(attr_type):
    return {
        "String": "#e377c2",
        "Integer": "#ff7f0e",
        "Float": "#17becf",
        "Bytes": "#8c564b",
        "NumPy Array": "#9467bd",
        "HDF5 object reference": "#d62728",
    }.get(attr_type, "#888888")


def explore_hdf5_tree(item):
    node = {'dtype': None, 'shape': None}

    if isinstance(item, h5py.Group):
        node['type'] = 'group'
        node['name'] = item.name
        attrs_info = []
        for attr_name, attr_value in item.attrs.items():
            attr_type_desc = get_attribute_type_description(attr_value, item.file)
            attrs_info.append({
                "attr_name": attr_name,
                "attr_value": format_attribute_value(attr_value),
                "attr_type": attr_type_desc
            })
        node['attributes'] = attrs_info
        children = [explore_hdf5_tree(item[key]) for key in item.keys()]
        node['children'] = children

    elif isinstance(item, h5py.Dataset):
        node['type'] = 'dataset'
        node['name'] = item.name
        attrs_info = []
        for attr_name, attr_value in item.attrs.items():
            attr_type_desc = get_attribute_type_description(attr_value, item.file)
            attrs_info.append({
                "attr_name": attr_name,
                "attr_value": format_attribute_value(attr_value),
                "attr_type": attr_type_desc
            })
        node['attributes'] = attrs_info
        node['dtype'] = str(item.dtype)
        try:
            data = item[()]
            node['shape'] = getattr(data, "shape", "?")
            if hasattr(data, "ndim") and data.ndim == 1:
                node['preview'] = data[:5].tolist()
        except Exception as e:
            node['preview_error'] = str(e)

    return node


def build_html_tree(node):
    name_escaped = html.escape(node['name'])
    node_type = node['type']
    node_color = "#1f77b4" if node_type == 'group' else "#2ca02c"
    title = f'<span class="node-title" style="color:{node_color}">{name_escaped}</span>'

    dtype_str = f"Type: {html.escape(str(node['dtype']))}" if node.get('dtype') else ""
    shape_str = f"Shape: {html.escape(str(node['shape']))}" if node.get('shape') else ""
    info_inline = f' <span class="dataset-info">— {" - ".join(filter(None, [shape_str, dtype_str]))}</span>' if (dtype_str or shape_str) else ""

    html_content = [f'<li><span class="toggle">+</span> {title}{info_inline}']
    html_content.append('<ul class="children">')

    attributes = node.get('attributes', [])
    if attributes:
        html_content.append('<li><span class="toggle">+</span> <span class="node-title">Attributes</span>')
        html_content.append('<ul class="attributes">')
        for attr in attributes:
            an = html.escape(str(attr['attr_name']))
            av = html.escape(str(attr['attr_value']))
            at = html.escape(str(attr['attr_type']))
            at_color = get_type_color(attr['attr_type'])
            html_content.append(
                f'<li><strong>{an}</strong>: {av}<br>'
                f'<small class="attr-type" style="color:{at_color}">Type: {at}</small></li>'
            )
        html_content.append('</ul></li>')

    if node_type == 'dataset' and 'preview' in node:
        preview = html.escape(str(node['preview']))
        html_content.append('<li><span class="toggle">+</span> <span class="node-title">Preview</span>')
        html_content.append(f'<ul class="dataset-preview"><li>{preview}</li></ul></li>')
    elif node_type == 'dataset' and 'preview_error' in node:
        err = html.escape(node['preview_error'])
        html_content.append('<li><span class="node-title">Error</span>')
        html_content.append(f'<ul class="dataset-preview error"><li>{err}</li></ul></li>')

    if node_type == 'group':
        for child in node.get('children', []):
            html_content.append(build_html_tree(child))

    html_content.append('</ul></li>')
    return ''.join(html_content)


def export_to_html_js(root_node, out_html, hdf5_filename):
    tree_html = f'<ul class="root">{build_html_tree(root_node)}</ul>'
    file_info = f"<p><strong>Analyzed file:</strong> {html.escape(hdf5_filename)}</p>"

    html_boilerplate = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Interactive HDF5 Structure</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        ul {{
            list-style-type: none;
            margin-left: 20px;
            padding-left: 0;
        }}
        li {{
            margin: 5px 0;
        }}
        .toggle {{
            display: inline-block;
            width: 1em;
            cursor: pointer;
            margin-right: 5px;
            font-weight: bold;
            color: #555;
        }}
        .node-title {{
            font-weight: bold;
        }}
        .children,
        .attributes,
        .dataset-preview {{
            display: none;
            margin-left: 20px;
        }}
        li.expanded > .children,
        li.expanded > ul {{
            display: block;
        }}
        .dataset-info {{
            font-style: italic;
            font-size: 90%;
            color: #666;
        }}
        .error {{
            color: red;
        }}
        .attr-type {{
            font-size: 90%;
        }}
    </style>
</head>
<body>

<h1>Interactive HDF5 File Analysis</h1>
{file_info}
{tree_html}

<script>
document.addEventListener('click', function(event) {{
    if (event.target.classList.contains('toggle')) {{
        const li = event.target.closest('li');
        li.classList.toggle('expanded');
        event.target.textContent = li.classList.contains('expanded') ? '−' : '+';
        event.stopPropagation();
    }}
}});
</script>

</body>
</html>
'''
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(html_boilerplate)


def extract_and_save_image(hdf5_file_path):
    with h5py.File(hdf5_file_path, 'r') as f:
        path_dataset = simpledialog.askstring("Dataset Path", "Enter the path of the dataset to convert to image (e.g., /image1):")
        if not path_dataset:
            return
        try:
            data = f[path_dataset][()]
        except Exception as e:
            messagebox.showerror("Error", f"Error accessing dataset:\n{str(e)}")
            return

        if data.ndim == 2:
            img_data = data
        elif data.ndim == 3 and data.shape[2] in [1, 3, 4]:
            img_data = data
        else:
            messagebox.showerror("Error", f"Dataset shape {data.shape} is not compatible with an image.")
            return

        try:
            if np.issubdtype(img_data.dtype, np.floating):
                img_data = np.clip(img_data, 0, 1) * 255
            img_data = img_data.astype(np.uint8)

            if img_data.ndim == 2 or img_data.shape[2] == 1:
                mode = "L"
                if img_data.ndim == 3:
                    img_data = img_data[:, :, 0]
            elif img_data.shape[2] == 3:
                mode = "RGB"
            elif img_data.shape[2] == 4:
                mode = "RGBA"
            else:
                messagebox.showerror("Error", "Unsupported image format.")
                return

            img = Image.fromarray(img_data, mode=mode)

            out_path = filedialog.asksaveasfilename(
                title="Save Extracted Image",
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")]
            )
            if out_path:
                img.save(out_path)
                messagebox.showinfo("Success", f"Image saved to:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error converting or saving image:\n{str(e)}")


def main():
    root = tk.Tk()
    root.withdraw()

    hdf5_file = filedialog.askopenfilename(
        title="Select the HDF5 file to analyze",
        filetypes=[("HDF5 Files", "*.hdf5 *.h5 *.ptir"), ("All Files", "*.*")]
    )
    if not hdf5_file:
        print("No file selected. Exiting.")
        return

    if not os.path.exists(hdf5_file):
        messagebox.showerror("Error", f"The file {hdf5_file} does not exist.")
        return

    file_base_name = os.path.splitext(os.path.basename(hdf5_file))[0]

    out_html = filedialog.asksaveasfilename(
        title="Save resulting HTML file",
        initialfile=f"{file_base_name}.html",
        defaultextension=".html",
        filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")]
    )
    if not out_html:
        print("Save canceled. Exiting.")
        return

    print(f"Analyzing HDF5 file: {hdf5_file}")
    with h5py.File(hdf5_file, 'r') as f:
        create  root_node = explore_hdf5_tree(f)

    print("Generating interactive HTML file...")
    export_to_html_js(root_node, out_html, os.path.basename(hdf5_file))
    print(f"HTML file successfully generated: {out_html}")

    if messagebox.askyesno("Open in browser?", "Do you want to open the newly d HTML file in your browser?"):
        webbrowser.open(f'file://{os.path.abspath(out_html)}')

    if messagebox.askyesno("Extract image", "Do you want to extract an image from a dataset?"):
        extract_and_save_image(hdf5_file)


if __name__ == '__main__':
    main()

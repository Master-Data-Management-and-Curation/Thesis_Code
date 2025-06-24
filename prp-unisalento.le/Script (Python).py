import os
import glob
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from ncempy.io import dm
import numpy as np
import json

# Updated list of search parameters
METADATA_KEYS = [
    "Device Name", "Formatted Voltage", "Exposure (s)", "Acquisition Date",
    "Acquisition Time", "Formatted Indicated Mag", "Pixel Size (um)", "PixelDepth",
    "Stage Alpha", "Stage Beta", "Stage X", "Stage Y", "Stage Z",
    "Active Size (pixels)"  # New parameter added
]

def find_metadata_values(metadata):
    """ It searches the metadata for the required parameters and extracts the value after the colon."""
    extracted_data = {key: "N/A" for key in METADATA_KEYS}  # initialise with N/A
   
    def recursive_search(data):
        """ Recursively search for keys in dictionaries and nested lists."""
        if isinstance(data, dict):
            for key, value in data.items():
                for target_key in METADATA_KEYS:
                    if target_key in key:  # If the key name contains the searched parameter
                        extracted_data[target_key] = convert_value(value)  # Converts data
                recursive_search(value)  # Continue searching in sub-dictionaries
        elif isinstance(data, list):
            for item in data:
                recursive_search(item)  # Search each item in the list

    recursive_search(metadata)
    return extracted_data

def convert_value(value):
    """ Converts NumPy types to standard Python types for JSON compatibility."""
    if isinstance(value, np.ndarray):
        return value.tolist()  # Convert NumPy array to Python list
    elif isinstance(value, (np.int64, np.uint64, np.int32, np.uint32)):
        return int(value)  # Convert NumPy integers to Python integers
    elif isinstance(value, (np.float64, np.float32)):
        return float(value)  # Convertire float NumPy in float Python
    return value  # Return the original value if already compatible

def extract_metadata(dm4_file):
    """ Extract ONLY the required metadata from a DM4 file."""
    try:
        dm4_data = dm.fileDM(dm4_file)
        metadata = dm4_data.allTags  # Extract all metadata
       
        # Search for parameters and values after the colon
        filtered_metadata = find_metadata_values(metadata)
        return filtered_metadata

    except Exception as e:
        return {"Error": f"Error reading {dm4_file}: {e}"}

def convert_to_text(metadata_dict):
    """ Converts metadata into a formatted string for the text file."""
    text_output = ""
    for file_name, metadata in metadata_dict.items():
        text_output += f"=== METADATA OF {file_name} ===\n\n"
        for key, value in metadata.items():
            text_output += f"{key}: {value}\n"
        text_output += "\n" + "=" * 50 + "\n\n"  # Inter-file separator
    return text_output

def save_results(folder_path, metadata_dict):
    """ Saves metadata in both TXT and JSON format."""
    output_txt = os.path.join(folder_path, "metadata_output.txt")
    output_json = os.path.join(folder_path, "metadata_output.json")

    try:
        # Saving in TXT
        with open(output_txt, "w", encoding="utf-8") as txt_file:
            txt_file.write(convert_to_text(metadata_dict))
       
        # Saving in JSON with automatic type conversion
        with open(output_json, "w", encoding="utf-8") as json_file:
            json.dump(metadata_dict, json_file, indent=4, ensure_ascii=False)

        messagebox.showinfo("Completed", f"Metadata saved successfully
 in:\n{output_txt}\n{output_json}")
        open_folder(folder_path)

    except Exception as e:
        messagebox.showerror("Error", f"Impossible to save files:\n{e}")

def process_dm4_files(folder_path):
    """ Reads the DM4 files in the folder and saves the metadata."""
    metadata_dict = {}
    dm4_files = glob.glob(os.path.join(folder_path, "*.dm4"))

    if not dm4_files:
        messagebox.showerror("Error", " No DM4 file found in the selected folder.")
        return

    for dm4_file in dm4_files:
        metadata = extract_metadata(dm4_file)
        metadata_dict[os.path.basename(dm4_file)] = metadata

    save_results(folder_path, metadata_dict)

def open_folder(path):
    """ Opens the results folder in File Explorer /Finder."""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(f'explorer "{path}"')
        elif os.name == 'posix':  # Mac/Linux
            subprocess.run(['xdg-open', path] if 'linux' in sys.platform else ['open', path])
    except Exception as e:
        messagebox.showerror("Error", f" Unable to open folder:\n{e}")

def select_folder():
    """ Opens the folder selection window and starts processing."""
    root = tk.Tk()
    root.withdraw()  # Hides the main window
    folder_selected = filedialog.askdirectory(title=" Select the folder with the DM4 files")

    if folder_selected:
        process_dm4_files(folder_selected)
    else:
        messagebox.showinfo("Info", " No folder selected. Operation aborted.")

# When double-clicked, it uses the script folder
if __name__ == "__main__":
    select_folder()
    input("\nPress ENTER to close...")  # Avoid immediate closure

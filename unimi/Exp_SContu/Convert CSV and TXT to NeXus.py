from datetime import datetime
import h5py
from nexusformat.nexus import *
import pandas as pd
from pathlib import Path

import tkinter as tk
from tkinter import filedialog
import subprocess
import traceback


output_file = ""

def parse_files(filename : str) -> str:
    input_file = str(Path(filename).parent/Path(filename).stem)
    output_dir = Path(filename).parent
    now_datetime = datetime.now()
    output_file = output_dir/Path(f"RAMAN_{now_datetime.strftime('%Y%m%d_%H%M%S')}.nxs")
    title = Path(filename).stem
    print(f"Title: {title}")

    # Extract data from the csv file
    filename = input_file + '.csv'
    print(f"CSV Input: {filename}")
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        status_label.config(text=f"ERROR: CSV file not found {filename}")
        return False
    except Exception:
        print(traceback.format_exc())
        status_label.config(text=f"ERROR on {filename}, check console")
        return False
    intensity = df[df.columns[4]].tolist()
    wavelength = df[df.columns[5]].tolist()
    status_label.config(text=f"CSV file: {filename}")

    # parsing of the txt metadata file
    sensor_types_str = ""
    txt_file_found = False
    try:
        filename = input_file + '.txt'
        file = open(filename, 'r', encoding='utf-8')
        txt_file_found = True
    except FileNotFoundError:
        pass
    except Exception:
        traceback.print_exc()
        status_label.config(text=f"ERROR on {filename}, check console")
        return False
    if not txt_file_found and search_also_info_txt_file.get():
        try:
            filename = input_file + '-info.txt'
            file = open(filename, 'r', encoding='utf-8')
            txt_file_found = True
        except FileNotFoundError:
            pass
        except Exception:
            traceback.print_exc()
            status_label.config(text=f"ERROR on {filename}, check console")
            return False
    
    if txt_file_found:
        print(f"TXT Input: {filename}")
        status_label.config(text=status_label.cget("text") + f"\nTXT file: {filename}")
        for line in file:
            if 'Sensor Type:' in line:
                parts = line.split('Sensor Type:') 
                if len(parts)>1:
                    sensor_type = parts[1].strip()
                    sensor_types_str += f"{sensor_type}\n" 
                    #sensor_types.append(sensor_type)
        file.close()
    else:
        print(f"TXT file not found")
        status_label.config(text=f"ERROR: TXT file not found {filename}")
        return False
    
    print(f"Output: {output_file}")
    print("")

    for sensor in sensor_types_str:
        print(f"Sensor Type: {sensor}")

    # build the nexus file
    f = h5py.File(output_file, "w")
    f.attrs['default'] = 'entry'

    # /entry
    f.create_group("entry")
    f['/entry'].attrs["NX_class"]= "NXentry"
    f['/entry'].attrs["default"] = "data"

    # /entry/definition
    f['/entry'].create_dataset('definition',data='NXraman')

    # /entry/version
    f['/entry/definition'].attrs["version"] = 'v2024.02'
    f['/entry/definition'].attrs["URL"] = 'https://github.com/FAIRmat-NFDI/nexus_definitions/blob/fd58c03d6c1be6469c2aff92ae7649fe5ad38a63/contributed_definitions/NXoptical_spectroscopy.nxdl.xml'

    # /entry/experiment_description
    f['/entry'].create_dataset('experiment_description',data='Raman Spectroscopy')
    f['/entry/experiment_description'].attrs["description"] = 'Technique'

    # /entry/experiment_type and sub_type
    f['/entry'].create_dataset('experiment_type', data='Raman Spectroscopy')
    f['/entry'].create_dataset('raman_experiment_type', data='other')

    # /entry/end_time
    f['/entry'].create_dataset('end_time',data=now_datetime.astimezone().isoformat())

    # /entry/title
    f['/entry'].create_dataset('title',data=title)

    # /entry/user
    f['/entry'].create_group("user")
    f['/entry/user'].attrs["NX_class"] = "NXuser"
    f['/entry/user'].create_dataset('name', data = 'Mario Rossi')
    f['/entry/user'].create_dataset('e-mail', data = 'mario.rossi@unimi.it')
    f['/entry/user'].create_dataset('affiliation', data = 'UNIMI') 

    # /entry/instrument
    f['/entry'].create_group("instrument")
    f['/entry/instrument'].attrs['NX_class'] = "NXinstrument"
    f['/entry/instrument'].create_dataset('scattering_configuration', data ='')
    f['/entry/instrument'].create_group('beam_laser')
    f['/entry/instrument/beam_laser'].attrs['NX_class'] = "NXbeam"
    f['/entry/instrument/beam_laser'].create_dataset('wavelength', data = 532)
    f['/entry/instrument/beam_laser'].create_dataset('parameter_reliability', data = 'nominal')
    #f['/entry/instrument'].create_dataset('beam_incident', data = '')
    #f['/entry/instrument/beam_laser'].create_dataset('wavelength', data = '')
    f['/entry/instrument/beam_laser/wavelength'].attrs["units"] = 'nm'

    # /entry/instrument/beam

    # /entry/instrument/source
    f['/entry/instrument'].create_group("source")
    f['/entry/instrument/source'].attrs["NX_class"] = "NXsource"
    f['/entry/instrument/source'].create_dataset('type',data='Laser')
    f['/entry/instrument/source'].create_dataset('wavelength', data = 532)
    f['/entry/instrument/source/wavelength'].attrs["units"] = "nm"

    # /entry/instrument/monochromator
    f['/entry/instrument'].create_group("monochromator")
    f['/entry/instrument/monochromator'].attrs["NX_class"] = "NXmonochromator"

    # /entry/instrument/detector
    f['/entry/instrument'].create_group("detector")
    f['/entry/instrument/detector'].attrs["NX_class"] = "NXdetector"
    f['/entry/instrument/detector'].create_dataset('detector_type', data = sensor_types_str)

    # /entry/sample
    f['/entry'].create_group("sample")
    f['/entry/sample'].attrs["NX_class"] = "NXsample"
    f['/entry/sample'].create_dataset('name', data='silicon')

    # /entry/data
    f['/entry'].create_group("data")
    f['/entry/data'].attrs['NX_class']= "NXdata"
    f['/entry/data'].create_dataset("intensity", data = intensity)
    f['/entry/data'].attrs["signal"] = "intensity" 
    f['/entry/data/intensity'].attrs["units"] = "counts"
    f['/entry/data'].create_dataset("wavelength", data = wavelength)
    #f['/entry/data'].attrs['axes'] = "wavelength"
    f['/entry/data/wavelength'].attrs["units"] = "nm"

    f.close()

    test=nxload(output_file)
    print(test.tree)

    status_label.config(text=status_label.cget("text") + f"\nExported to {output_file}")
    return str(output_file)


def browse_file():
    global output_file
    file_path = filedialog.askopenfilename(filetypes=[("CSV files",('*.csv'))])
    if file_path:
        output_file = parse_files(file_path)
        if output_file:
            reveal_button.config(state=tk.NORMAL)
        else:
            reveal_button.config(state=tk.DISABLED)


def reveal_file():
    subprocess.Popen(fr'explorer /select,"{output_file}"')


# Create the main window
window = tk.Tk()
window.title("Convert CSV and TXT to NeXus")

# Info labels
info_label = tk.Label(window, text="This script converts the .csv and .txt files to a .nxs file.\nSelect the CSV file and the script will automatically take the TXT file.\nThe two files must be in the same folder and must have the same name.")
info_label.pack(padx=10, pady=10)

search_also_info_txt_file = tk.BooleanVar(value=True)
checkbox1 = tk.Checkbutton(window, text='Search also for "*-info.txt" file', variable=search_also_info_txt_file)
checkbox1.pack()

# Create a button to trigger the file dialog
browse_button = tk.Button(window, text="Browse to .csv file", command=browse_file)
browse_button.pack(pady=10)

# Show some feedback
status_label = tk.Label(window, text="No file selected.\nBrowse to the .csv file to convert both .csv and .txt files.")
status_label.pack(padx=10, pady=10)

# Create a button to trigger the file dialog
reveal_button = tk.Button(window, text="Find the .nxs file in File Explorer", command=reveal_file)
reveal_button.config(state=tk.DISABLED)
reveal_button.pack(pady=10)

# Run the application
window.mainloop()
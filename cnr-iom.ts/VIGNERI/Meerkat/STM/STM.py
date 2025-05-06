import os
from PIL import Image
from PyQt5.QtCore import pyqtSignal, QThread
import json
import numpy as np

import spym
from tools import tools
from eLabFTW import eLabFTW_credentials
from App_Paths import app_paths

STM_prefix = app_paths.STM_prefix
png_prefix = app_paths.png_prefix

thumbnail_ext = ".png"
STM_ext = ".sm4"
metadata_ext = ".json"

""" --------------------------------------------------------------------
    --------------------------------------------------------------------
    Hi! I'm the STRAS Microscopy Image Refinement and Catalog Organizer.
    --------------------------------------------------------------------
    --------------------------------------------------------------------
"""

# Function to convert non-JSON-serializable types into serializable ones
def convert_to_serializable(obj):
    if isinstance(obj, (np.integer, int)):  # Manage NumPy o normal integer
        return int(obj)
    elif isinstance(obj, (np.floating, float)):  # Manage NumPy o normal float
        return float(obj)
    elif isinstance(obj, np.ndarray):  # Manage NumPy array
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable") # If there is a non-JSON-serializable type that is still not managed

class UpdateOverview(QThread):

    status = pyqtSignal(str)

    def __init__(self, experiment_id, date_str):
        QThread.__init__(self)
        self.datestr = date_str
        self.experimentid = experiment_id

    def __del__(self):
        self.wait()
    
    def run(self):
        
        # Initializing experiment_id string
        experiment_id = ""
        # Initializing date_str string
        date_str = ""

        date_str += self.datestr
        experiment_id += self.experimentid

        # Check if "STM data folder" field is filled in
        if not date_str:
            self.status.emit("Enter an STM data folder.")
            return

        STM_path = os.path.join(STM_prefix, date_str[0:4], date_str, "STM")

        # Check if directory with STM data exists
        if not os.path.exists(STM_path):
            self.status.emit("Folder " + STM_path + " does not exist!")
            return

        # Check if experiment_id field is filled in
        if not experiment_id:
            self.status.emit("Enter an experiment ID.")
            return

        # Check if experiment page with ID = experiment_id exists
        try:
            experiment_page= eLabFTW_credentials.elabftw_api.get_experiment(experiment_id)
        except Exception as e:
            self.status.emit("Experiment " + experiment_id + " does not exist!")
            return

        # Retrieve STM files list
        file_list = []

        for file in os.listdir(STM_path):
            if file.endswith(STM_ext) and "_IV" not in file and "_IZ" not in file and "_dIdV" not in file:
                file_list.append(file)
        if not file_list:
            self.status.emit("No STM files for " + date_str + " date!")
            return

        # Sort file list by name
        tools.natural_sort(file_list)

        # Create thumbnails folder
        png_path = os.path.join(png_prefix, date_str[0:4], date_str, "STM_thumbnails")
        if not os.path.exists(png_path):
            os.makedirs(png_path)

        # Create a list of all files that are already uploaded in the eLabFTW experiment page
        uploads_list = []
        for upload in experiment_page['uploads']:
            uploads_list.append(upload['real_name'])

        # Number of logged files
        num_log = 0

        for f in file_list:

            filepath = os.path.join(STM_path, f)
            filename = os.path.splitext(f)[0]
            png_file = os.path.join(png_path, filename + thumbnail_ext)
            metadata_jsonfile = os.path.join(png_path, filename + "_metadata" + metadata_ext)

            # Check if filename is already logged
            if (filename + thumbnail_ext) in uploads_list:
                self.status.emit("File " + filename + thumbnail_ext + " already logged.")
                continue
          
            # Increment number of logged files
            num_log += 1

            # Open file with spym
            f = spym.load(filepath)
            meta = ''
            try:
                tf = f.Topography_Forward
            except:
                continue

            # Create thumbnail and metadata
            title = tf.attrs['filename'] + '\n' + str(tf.attrs['bias']) + " " + tf.attrs['bias_units'] + ", " + str(tf.attrs['setpoint']) + " " + tf.attrs['setpoint_units'] 
            tf.spym.align()
            tf.spym.plane()
            tf.spym.fixzero()
            p = tf.spym.plot(title=title)
            f = p.get_figure()
            f.savefig(png_file)
            ax = p.axes
            meta = ax.get_title()
            # Read current thumbnail dimensions
            img = Image.open(png_file)
            width, height = img.size

            # Create image metadata.json file
            with open(metadata_jsonfile, 'w') as metajsonfile:
                # Write the metadata dictionary in the metadata_jsonfile in a JSON format
                imageMeta_dict = tf.attrs
                json.dump(imageMeta_dict, metajsonfile, indent=4, default=convert_to_serializable)  # indent=4 make the JSON format readable

            # Send file addition
            self.status.emit("Logging " + filename + ".")

            # Add image to eLabFTW
            # Let's add a new comment to our experiemnt body
            comment_text = "<p><i>" + title + "</i></p>"
            response = eLabFTW_credentials.elabftw_api.add_to_body_of_experiment(experiment_id, comment_text)

            # Let's add an image
            upload_width = 450
            upload_height = upload_width/width * height  
            comment = title

            response = eLabFTW_credentials.elabftw_api.add_image_to_experiment(experiment_id, png_file, upload_width, upload_height, comment)

            # Let's add a new empty line to our experiemnt body
            comment_text = "<p>\xa0</p>"
            response = eLabFTW_credentials.elabftw_api.add_to_body_of_experiment(experiment_id, comment_text)

        if num_log:
            self.status.emit("Logbook updated with " + str(num_log) + " file(s).")
        else:
            self.status.emit("Logbook already updated.")

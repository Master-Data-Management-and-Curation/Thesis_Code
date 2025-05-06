import os
from PIL import Image
from PyQt5.QtCore import pyqtSignal, QThread
import json
import numpy as np

import spym
from tools import tools
from STM import STM

thumbnail_ext = STM.thumbnail_ext
STM_ext = STM.STM_ext
metadata_ext = STM.metadata_ext

# Function to convert non-JSON-serializable types into serializable ones
def convert_to_serializable(obj):
    if isinstance(obj, (np.integer, int)):  # Manage NumPy o normal integer
        return int(obj)
    elif isinstance(obj, (np.floating, float)):  # Manage NumPy o normal float
        return float(obj)
    elif isinstance(obj, np.ndarray):  # Manage NumPy array
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable") # If there is a non-JSON-serializable type that is still not managed

class Updategallery(QThread):

    status = pyqtSignal(str)

    def __init__(self, STM_path, png_path):
        QThread.__init__(self)
        self.STMpath = STM_path
        self.pngpath = png_path

    def __del__(self):
        self.wait()
    
    def run(self):
        
        STM_path = self.STMpath
        png_path = self.pngpath

        # Retrieve STM files list
        file_list = []

        for file in os.listdir(STM_path):
            if file.endswith(STM_ext) and "_IV" not in file and "_IZ" not in file and "_dIdV" not in file:
                file_list.append(file)
        if not file_list:
            self.status.emit("No STM files in " + STM_path)
            return

        # Sort file list by name
        tools.natural_sort(file_list)

        # Initialize list of thumbnails
        gallery_list = []

        # Create thumbnails folder if it does not exist or if it exists, make a list of all files already present
        if not os.path.exists(png_path):
            os.makedirs(png_path)
        elif os.path.exists(png_path):
            gallery_list = [f for f in os.listdir(png_path) if os.path.isfile(os.path.join(png_path, f))]

        # Number of logged files
        num_log = 0

        for f in file_list:

            filepath = os.path.join(STM_path, f)
            filename = os.path.splitext(f)[0]
            png_file = os.path.join(png_path, filename + thumbnail_ext)
            metadata_jsonfile = os.path.join(png_path, filename + "_metadata" + metadata_ext)

            # Check if filename is already present in the thumbanails folder
            if (filename + thumbnail_ext) in gallery_list and (filename + "_metadata" + metadata_ext) in gallery_list:
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

            # Create image metadata.json file
            with open(metadata_jsonfile, 'w') as metajsonfile:
                # Write the metadata dictionary in the metadata_jsonfile in a JSON format
                imageMeta_dict = tf.attrs
                json.dump(imageMeta_dict, metajsonfile, indent=4, default=convert_to_serializable)  # indent=4 make the JSON format readable

            # Send file addition
            self.status.emit("Logging " + filename + ".")

        if num_log:
            self.status.emit("Gallery updated with " + str(num_log) + " file(s).")
        else:
            self.status.emit("Gallery already updated.")

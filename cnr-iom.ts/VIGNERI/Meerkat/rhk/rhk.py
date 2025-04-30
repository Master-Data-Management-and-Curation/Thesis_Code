import socket
import time
from PyQt5.QtCore import pyqtSignal, QThread
import datetime
import os

from App_Paths import app_paths

# Insert here the data for the PC where R9 software is installed
IP_Address_R9_PC = 'IP address ???'
TCP_Port_R9s = 'TCP Port ???'

BUFFER_SIZE = 1024

def send(command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP_Address_R9_PC, TCP_Port_R9s))

    # KEEP THE WAIT TIME BELOW, otherwise the R9 will ignore your first command
    time.sleep(0.1)

    print ("Connected to socket \n")
    #command = "GetSWSubItemParameter, Scan Area Window, MeasureSave, Default Comment"
    command += "\n"

    s.send(command.encode())
    print ("Command sent \n")

    output = s.recv(BUFFER_SIZE)
    print ("Output received \n")
    s.close()

    print ("Received output:", output)
    return output.decode()

def log_meta(meta_dict):
    """Retrieve some metadata for the logbook
    
    Args:
            meta_dict: dictionary of metadata
    
    Returns: string with selected metadata formatted
    
    """

    s_date = meta_dict["Date"][9:14]
    s_bias = "%.3f V" % (float(meta_dict["Bias"].split(" ")[0]))
    s_current = "%.3f nA" % (abs(float(meta_dict["Current"].split(" ")[0])*1E9))
    s_angle = meta_dict["Rotation angle"]
    s_xoff = str(float(meta_dict["X offset"].split(" ")[0])*1E9) + " nm"
    s_yoff = str(float(meta_dict["Y offset"].split(" ")[0])*1E9) + " nm"
    s_xsize = "%d" % (float(meta_dict["X size"])*abs(float(meta_dict["X scale"]))*1E9)
    s_ysize = "%d" % (float(meta_dict["Y size"])*abs(float(meta_dict["Y scale"]))*1E9)

    meta1 = ""
    meta1 += s_date
    meta1 += " "
    meta1 += "(" + s_bias + ", " + s_current + ") "
    meta1 += "(" + s_xsize + "x" + s_ysize + " nm) "
    meta1 += "\n"

    meta2 = "(" + s_xoff + ", " + s_yoff + ") " + s_angle
    meta2 += "\n"

    return meta1, meta2

class RHK_initialize(QThread):

    status = pyqtSignal(str)

    def __init__(self, sample_name):
        QThread.__init__(self)
        self.samplename = sample_name

    def __del__(self):
        self.wait()

    def run(self):

        sample_name = self.samplename

        now = datetime.datetime.now()
        yyyy = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")

        ## Save on server (folders are created automatically)
        save_path = os.path.join(app_paths.RHK_NAS_prefix, yyyy, yyyy + month + day, "STM")   #Save path (i.e. NAS path) on the PC where R9s is installed
        nas_path = os.path.join(app_paths.STM_prefix, yyyy, yyyy + month + day, "STM")   #NAS path on the PC where Little Helper is executed
        if not os.path.exists(nas_path):
            os.makedirs(nas_path)

        save_path_out = send("SetSWSubItemParameter, Scan Area Window, MeasureSave, Save Path, " + save_path)
        self.status.emit("Setting path: " + save_path_out)
        file_name_out_STM = send("SetSWSubItemParameter, Scan Area Window, MeasureSave, File Name, " + sample_name)
        self.status.emit("Setting STM file name: " + file_name_out_STM)
        file_name_out_IV = send("SetSWSubItemParameter, IV Spectroscopy, MeasureSave, File Name, " + sample_name + "_IV")
        self.status.emit("Setting IV file name: " + file_name_out_IV)
        file_name_out_IZ = send("SetSWSubItemParameter, IZ Spectroscopy, MeasureSave, File Name, " + sample_name + "_IZ")
        self.status.emit("Setting IZ file name: " + file_name_out_IZ)
        file_name_out_dIdV = send("SetSWSubItemParameter, dI/dV Spectroscopy, MeasureSave, File Name, " + sample_name + "_dIdV")
        self.status.emit("Setting dIdV file name: " + file_name_out_dIdV)

        if save_path_out == file_name_out_STM == file_name_out_IV == file_name_out_IZ == file_name_out_dIdV == "Done":
            self.status.emit("R9s initialization done.")
        else:
            self.status.emit("Error in R9s initialization!")
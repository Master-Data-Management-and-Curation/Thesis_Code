import datetime
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QLineEdit, QLabel, QAction, QFileDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QMessageBox, QComboBox, QGroupBox, QFrame, QTabWidget, QDialog, QTabBar, QInputDialog, QSlider
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import pyqtSignal, QThread, Qt, QMetaObject, pyqtSlot, QTimer
import os
import json
import re

from STM import STM
from rhk import rhk
from App_Paths import app_paths
from gallery import gallery
from eLabFTW import eLabFTW_credentials

# Create a main window
class Main(QMainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.initUi()

    def initUi(self):
        # Window properties
        self.setGeometry(500, 400, 680, 420)
        self.setMinimumSize(self.size())
        self.setWindowTitle("Meerkat")
        self.setWindowIcon(QIcon("./Icons/meerkat-icon.png"))

        # Create central widget
        self.centralWidget = Widget()
        self.setCentralWidget(self.centralWidget)

        # Create menu bar
        menubar = self.menuBar()

        # Tools menu
        ToolsMenu = menubar.addMenu("Tools")
        # eLabFTW menu
        eLabFTWMenu = menubar.addMenu("eLabFTW")

        # Create a tool: Gallery
        ToolsMenu_Gallery = QAction("Gallery", self)        
        ToolsMenu_Gallery.setStatusTip('Open the STM image gallery')
        ToolsMenu_Gallery.triggered.connect(self.centralWidget.open_GalleryWindow)

        ToolsMenu.addAction(ToolsMenu_Gallery)

        # Create an eLab tool: Create New Sample
        eLabFTWMenu_NewSample = QAction("Create New Sample", self)        
        eLabFTWMenu_NewSample.setStatusTip('Create new sample metadata on eLab')
        eLabFTWMenu_NewSample.triggered.connect(self.centralWidget.open_NewSampleWindow)

        eLabFTWMenu.addAction(eLabFTWMenu_NewSample)

        # Aesthetic customization
        self.setStyleSheet("""
            QMenuBar {
                background-color: #2E2E2E;
                color: white;
                font: bold 14px Arial;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QMenu {
                background-color: #2E2E2E;
                color: white;
                border: 1px solid #4CAF50;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        
        # Create statusbar
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Ready")
        self.centralWidget.status[str].connect(self.statusbar.showMessage)

        self.show()

        # Create a permanent label on the statusbar right side
        made_by_label = QLabel("Made with \U00002764 by Ste")
        self.statusbar.addPermanentWidget(made_by_label)

# Create a secondary window (gallery)
class GalleryWindow(QMainWindow):
    def __init__(self):
        super(GalleryWindow, self).__init__()
        self.initUi()

    def initUi(self):
        # Window properties
        self.setWindowTitle("Gallery")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(self.size())
        self.setWindowIcon(QIcon("./Icons/landscape2-icon.png"))

        # Create central widget
        self.gallery_central_widget = GalleryWidget()
        self.setCentralWidget(self.gallery_central_widget)

# Create a secondary window (Create New Sample)
class NewSampleWindow(QMainWindow):
    def __init__(self):
        super(NewSampleWindow, self).__init__()
        self.initUi()

    def initUi(self):
        # Window properties
        self.setWindowTitle("Create New Sample")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(self.size())

        # Create central widget
        self.NewSample_central_widget = NewSampleWidget()
        self.setCentralWidget(self.NewSample_central_widget)

class Widget(QWidget):

    status = pyqtSignal(str)

    fontSize_HeaderLabel = 16
    fontSize_sectionLabel = "16px"
    fontSize_body = "15px"


    def __init__(self):
        super(Widget, self).__init__()
        self.initUI()

    def initUI(self):

        # Create main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Create sub-layout
        self.sub_layout = QHBoxLayout()
        
        # Create fields-layout
        self.fields_layout = QVBoxLayout()

        # Create RHK-layout
        self.RHK_layout = QVBoxLayout()
        
        # Create RHK-sub-layout
        self.RHK_sub_layout = QHBoxLayout()

        # Create eLab-layout
        self.eLab_layout = QVBoxLayout()

        # Create eLab-sub-layout
        self.eLab_sub_layout = QHBoxLayout()

        # Create eLab-Left-sub-layout
        self.eLab_LeftSub_layout = QVBoxLayout()

        # Create eLab-Right-sub-layout
        self.eLab_RightSub_layout = QVBoxLayout()

        # Create eLab-Right-sub-sub-layout
        self.eLab_RightSub_Sub_layout = QHBoxLayout()

        # Create eLab-Bottom-sub-layout
        self.eLab_sub_bottom_layout = QHBoxLayout()

        # App Header
        Headerlabel = QLabel("Microscopy Image Refinement and Catalog Organizer", self)
        Headerlabel.setFont(QFont("Arial", self.fontSize_HeaderLabel, QFont.Bold))
        Headerlabel.setStyleSheet("color: #4F81BD;")
        Headerlabel.setAlignment(Qt.AlignCenter)

        # Attaching an image to the window
        img_label = QLabel(self)
        img_label.setPixmap(QPixmap("./Icons/meerkat-crop-icon.png").scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

#-----------------------------------------------------------------------------------------------

        # RHK Initialization Section
        RHKsectionlabel = QLabel("RHK Initialization", self)
        RHKsectionlabel.setStyleSheet("color: #4F81BD; font-weight: bold; font-size: " + self.fontSize_sectionLabel)
        self.RHK_layout.addWidget(RHKsectionlabel)

        # Sample textbox
        samplelabel = QLabel("Sample name:", self)
        samplelabel.setStyleSheet("font-size: " + self.fontSize_body)
        self.RHK_layout.addWidget(samplelabel)

        self.samplebox = QLineEdit(self)
        now = datetime.datetime.now()
        year = now.strftime("%y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        self.samplebox.setPlaceholderText("Enter sample name (e.g., "+"VT" + year + month + day + "_A1"+")")
        self.samplebox.setText("VT" + year + month + day + "_A1")
        self.samplebox.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #C2C2C2; font-size: " + self.fontSize_body)
        self.RHK_sub_layout.addWidget(self.samplebox)

        # Initialize RHK button
        self.InitializeRHK_btn = QPushButton('Initialize R9s', self)
        self.InitializeRHK_btn.setStyleSheet("background-color: #4F81BD; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + self.fontSize_body)
        self.InitializeRHK_btn.setToolTip('Update RHK save path and filenames.')
        self.RHK_sub_layout.addWidget(self.InitializeRHK_btn)
        self.InitializeRHK_btn.clicked.connect(self.RHK_init)

        self.RHK_layout.addLayout(self.RHK_sub_layout)
        
#-----------------------------------------------------------------------------------------------

        # eLabFTW Update Section
        eLabFTWsectionlabel = QLabel("eLabFTW Update", self)
        eLabFTWsectionlabel.setStyleSheet("color: #4F81BD; font-weight: bold; font-size: " + self.fontSize_sectionLabel)
        self.eLab_layout.addWidget(eLabFTWsectionlabel)

        # Experiment ID textbox
        experimentIDlabel = QLabel("Experiment ID:", self)
        experimentIDlabel.setStyleSheet("font-size: " + self.fontSize_body)
        self.eLab_LeftSub_layout.addWidget(experimentIDlabel)

        self.experimentIDbox = QLineEdit(self)
        self.experimentIDbox.setPlaceholderText("Enter Experiment ID")
        self.experimentIDbox.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #C2C2C2; font-size: " + self.fontSize_body)
        self.eLab_LeftSub_layout.addWidget(self.experimentIDbox)


        # STM data folder textbox
        dataFolderlabel = QLabel("Select STM data folder:", self)
        dataFolderlabel.setStyleSheet("font-size: " + self.fontSize_body)
        self.eLab_RightSub_layout.addWidget(dataFolderlabel)

        self.dataFolderbox = QLineEdit(self)
        now = datetime.datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        self.dataFolderbox.setPlaceholderText("e.g., " + year + month + day)
        self.dataFolderbox.setText(year + month + day)
        self.dataFolderbox.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #C2C2C2; font-size: " + self.fontSize_body)
        self.eLab_RightSub_Sub_layout.addWidget(self.dataFolderbox)

        # Browse button
        self.Browse_btn = QPushButton(' Browse', self)
        self.Browse_btn.setStyleSheet("background-color: #4F81BD; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + self.fontSize_body)
        self.Browse_btn.setIcon(QIcon("./Icons/folder-icon.svg"))  # Add a folder icon to the button
        self.Browse_btn.setToolTip('Select STM data folder to upload in eLabFTW')
        self.eLab_RightSub_Sub_layout.addWidget(self.Browse_btn)
        self.Browse_btn.clicked.connect(self.STM_log_folder)

        self.eLab_RightSub_layout.addLayout(self.eLab_RightSub_Sub_layout)

        # Update eLabFTW button
        self.UpdateLogbook_btn = QPushButton('Update eLabFTW', self)
        self.UpdateLogbook_btn.setStyleSheet("background-color: #32CD32; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + self.fontSize_sectionLabel)
        self.UpdateLogbook_btn.setToolTip('Update eLabFTW page with STM data in the selected folder')
        self.UpdateLogbook_btn.clicked.connect(self.UpdOverview)

        self.eLab_sub_layout.addLayout(self.eLab_LeftSub_layout,1)
        self.eLab_sub_layout.addLayout(self.eLab_RightSub_layout,1)

        self.eLab_sub_bottom_layout.addWidget(self.UpdateLogbook_btn,1)
        self.eLab_sub_bottom_layout.addStretch(1)

        self.eLab_layout.addLayout(self.eLab_sub_layout)
        self.eLab_layout.addLayout(self.eLab_sub_bottom_layout)

        self.fields_layout.addStretch(6)
        self.fields_layout.addLayout(self.RHK_layout,4)
        self.fields_layout.addStretch(6)
        self.fields_layout.addLayout(self.eLab_layout,6)
        self.fields_layout.addStretch(2)

        self.sub_layout.addLayout(self.fields_layout,10)
        self.sub_layout.addWidget(img_label,1)
        
        self.main_layout.addWidget(Headerlabel,2)
        self.main_layout.addLayout(self.sub_layout,8)

    def STM_log_folder(self):

        path = QFileDialog.getExistingDirectory(self,
                                                  "Select folder",
                                                  app_paths.STM_prefix,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                                                  )

        folder = os.path.basename(path)
        if len(folder) == 8:
            self.dataFolderbox.setText(folder)
        else:
            self.status.emit("Selected folder is not valid.")

    def UpdOverview(self):
        self.UpdOverview_thread = STM.UpdateOverview(self.experimentIDbox.text(), self.dataFolderbox.text())
        self.UpdOverview_thread.status.connect(self.UpdOverview_status)
        self.UpdOverview_thread.finished.connect(self.UpdOverview_finished)
        self.UpdOverview_thread.start()
        self.UpdateLogbook_btn.setStyleSheet("background-color: #1c751c; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + self.fontSize_sectionLabel)
        self.UpdateLogbook_btn.setEnabled(False)

    def UpdOverview_status(self, status):
        self.status.emit(status)

    def UpdOverview_finished(self):
        self.UpdateLogbook_btn.setEnabled(True)
        self.UpdateLogbook_btn.setStyleSheet("background-color: #32CD32; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + self.fontSize_sectionLabel)
    
    def RHK_init(self):
        self.RHK_init_thread = rhk.RHK_initialize(self.samplebox.text())
        self.RHK_init_thread.status.connect(self.RHK_init_status)
        self.RHK_init_thread.finished.connect(self.RHK_init_finished)
        self.RHK_init_thread.start()
        self.InitializeRHK_btn.setStyleSheet("background-color: #315178; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + self.fontSize_body)
        self.InitializeRHK_btn.setEnabled(False)

    def RHK_init_status(self, status):
        self.status.emit(status)

    def RHK_init_finished(self):
        self.InitializeRHK_btn.setEnabled(True)
        self.InitializeRHK_btn.setStyleSheet("background-color: #4F81BD; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + self.fontSize_body)

    def open_GalleryWindow(self):
        # Create and show the Gallery window
        self.gallery_window = GalleryWindow()
        self.gallery_window.show()
    
    def open_NewSampleWindow(self):
        # Create and show the New Sample window
        self.NewSample_window = NewSampleWindow()
        self.NewSample_window.show()

class GalleryWidget(QWidget):

    status = pyqtSignal(str)

    # Initialize variables
    image_list = []
    metadata_list = []
    current_index = -1

    def __init__(self):
        super(GalleryWidget, self).__init__()
        self.initUI()

    def initUI(self):
        
        # Create main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Create data visualization horizzontal layout
        datalayout = QHBoxLayout()

        # Image label
        self.image_label = QLabel("No images loaded")
        self.image_label.setStyleSheet("font-size: " + Widget.fontSize_body)
        self.image_label.setAlignment(Qt.AlignCenter)
        datalayout.addWidget(self.image_label,3)

        # Metadata section
        self.metadata_label = QLabel("No STM metadata loaded")
        self.metadata_label.setStyleSheet("font-size: " + Widget.fontSize_body)
        self.metadata_label.setAlignment(Qt.AlignCenter)
        # Create a Scrolling Area for metadata display
        metadata_scroll_area = QScrollArea(self)
        metadata_scroll_area.setWidget(self.metadata_label)  # Encapsulate metadata_label in the scrolling area
        metadata_scroll_area.setWidgetResizable(True)  # Make the widget resizable
        datalayout.addWidget(metadata_scroll_area, 2)

        # Encapsulate datalayout in the main vertical layout
        self.layout.addLayout(datalayout,4)

        # Status label
        self.status_label = QLabel("No images loaded")
        self.status_label.setStyleSheet("font-size: " + Widget.fontSize_body)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        # Navigation buttons
        button_layout = QHBoxLayout()

        self.browse_button = QPushButton("Browse Gallery")
        self.browse_button.setStyleSheet("background-color: #32CD32; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + Widget.fontSize_body)
        self.browse_button.setToolTip('Select STM data folder to show')
        self.browse_button.clicked.connect(self.browse_directory)
        button_layout.addWidget(self.browse_button,1)

        self.prev_button = QPushButton("< Previous")
        self.prev_button.setStyleSheet("background-color: #4F81BD; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + Widget.fontSize_sectionLabel)
        self.prev_button.setToolTip('Show previous image')
        self.prev_button.clicked.connect(self.previous_image)
        self.prev_button.setEnabled(False)
        button_layout.addWidget(self.prev_button,2)

        self.next_button = QPushButton("Next >")
        self.next_button.setStyleSheet("background-color: #4F81BD; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + Widget.fontSize_sectionLabel)
        self.next_button.setToolTip('Show next image')
        self.next_button.clicked.connect(self.next_image)
        self.next_button.setEnabled(False)
        button_layout.addWidget(self.next_button,2)

        # Add a slider to go through images
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)  # It will be updated when images are uploaded
        self.slider.setValue(0)
        self.slider.setEnabled(False)
        self.slider.setTickInterval(1)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self.slider_moved)
        self.layout.addWidget(self.slider)

        self.layout.addLayout(button_layout)

        # Allow to accept input from the keyboard
        self.setFocusPolicy(Qt.StrongFocus)

    def browse_directory(self):
        """Opens a file dialog to choose a directory and displays its content."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder", app_paths.STM_prefix)
        # Check if the selected folder is valid
        if not os.path.basename(os.path.normpath(folder_path))=="STM":
            #Create a notification window
            self.msg_box = QMessageBox()
            self.msg_box.setWindowTitle("Message")
            self.msg_box.setText("The selected folder is invalid.\n\nPlease select a folder in the format:\nYYYY/YYYYMMDD/STM.")
            self.msg_box.setIcon(QMessageBox.Information)
            self.msg_box.setStandardButtons(QMessageBox.Ok)
            self.msg_box.exec_()
            return

        self.thumbnail_path = os.path.join(app_paths.png_prefix, os.path.relpath(os.path.normpath(folder_path).removesuffix(os.path.normpath("/STM")), os.path.normpath(app_paths.STM_prefix)), "STM_thumbnails")


        if not os.path.exists(self.thumbnail_path):     
            #Create a notification window
            self.msg_box = QMessageBox()
            self.msg_box.setWindowTitle("Message")
            self.msg_text = "Gallery not found for this folder.\nCreating it now, please wait.\n\nStatus:\n"
            self.msg_box.setText(self.msg_text)
            self.msg_box.setIcon(QMessageBox.Information)
            self.msg_box.setStandardButtons(QMessageBox.NoButton)
            self.msg_box.show()

            self.UpdGallery_thread = gallery.Updategallery(folder_path, self.thumbnail_path)
            self.UpdGallery_thread.status.connect(self.UpdGallery_status)
            self.UpdGallery_thread.finished.connect(self.UpdGallery_finished, Qt.QueuedConnection)
            self.UpdGallery_thread.start()
        elif os.path.exists(self.thumbnail_path):
            # Number of STM .sm4 files
            STMfile_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(STM.STM_ext) and "_IV" not in f and "_IZ" not in f and "_dIdV" not in f])
            # Number of STM .png files
            img_count = len([f for f in os.listdir(self.thumbnail_path) if os.path.isfile(os.path.join(self.thumbnail_path, f))])
            if img_count<(2*STMfile_count):
                
                #Create a notification window
                self.msg_box = QMessageBox()
                self.msg_box.setWindowTitle("Message")
                self.msg_text = "The gallery for this folder is outdated.\nUpdating now, please wait.\n\nStatus:\n"
                self.msg_box.setText(self.msg_text)
                self.msg_box.setIcon(QMessageBox.Information)
                self.msg_box.setStandardButtons(QMessageBox.NoButton)
                self.msg_box.show()

                self.UpdGallery_thread = gallery.Updategallery(folder_path, self.thumbnail_path)
                self.UpdGallery_thread.status.connect(self.UpdGallery_status)
                self.UpdGallery_thread.finished.connect(self.UpdGallery_finished, Qt.QueuedConnection)
                self.UpdGallery_thread.start()
            else:
                self.load_images(self.thumbnail_path)

    def UpdGallery_status(self, status):
        """Update the message box with the current status."""
        if self.msg_box:
            self.msg_box.setText(f"{self.msg_text}{status}")
            self.lastGalleryStatus = status
            
    def UpdGallery_finished(self):
        QMetaObject.invokeMethod(self, "close_msg_box", Qt.QueuedConnection)
        #Create a notification window
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Message")
        msg_text = f"Gallery is ready!\n\nStatus:\n{self.lastGalleryStatus}"
        msg_box.setText(msg_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Ok)
        # Use exec_() to block and wait for user interaction
        if msg_box.exec_() == QMessageBox.Ok:
            # Once the message box is closed, proceed to load images
            QTimer.singleShot(0, lambda: self.load_images(self.thumbnail_path))
    
    @pyqtSlot()
    def close_msg_box(self):
        """Metod to close the notification window in the main thread"""
        if hasattr(self, 'msg_box') and self.msg_box is not None:
            self.msg_box.close()
            self.msg_box.deleteLater()

    def load_images(self, directory):
        """Loads images from the selected directory and its subdirectories."""
        self.image_list.clear()
        self.metadata_list.clear()
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(STM.thumbnail_ext):
                    self.image_list.append(os.path.join(root, file))

        # Initialize empty list for metadata of the same length of the image list 
        self.metadata_list = [""] * len(self.image_list)   

        for root, _, files in os.walk(directory):
            for file in files: 
                if file.lower().endswith((".json")) and os.path.join(root, file.removesuffix("_metadata.json")+STM.thumbnail_ext) in self.image_list:
                    img_index = self.image_list.index(os.path.join(root, file.removesuffix("_metadata.json")+STM.thumbnail_ext))
                    self.metadata_list[img_index]=os.path.join(root, file)
        
        if self.image_list:
            self.current_index = 0
            self.display_image(self.current_index)
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.slider.setMaximum(len(self.image_list) - 1)
            self.slider.setEnabled(True)
        else:
            self.image_label.setText("No images found")
            self.metadata_label.setText("No STM metadata found")
            self.status_label.setText("No images found")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.slider.setEnabled(False)
    
    # Method to update the image when the slider moves
    def slider_moved(self, value):
        self.current_index = value
        self.display_image(self.current_index)

    def keyPressEvent(self, event):
        """Manage the arrow buttons on the keyboard to go through the images."""
        if event.key() == Qt.Key_Right:  
            self.next_image()
        elif event.key() == Qt.Key_Left:  
            self.previous_image()

    def display_image(self, index):
        """Displays the image at the specified index in the image_list."""
        if 0 <= index < len(self.image_list):
            image_path = self.image_list[index]
            metadata_path = self.metadata_list[index]
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)
            if metadata_path:
                # Read JSON file
                with open(metadata_path, "r") as metadata_file:
                    metadata = json.load(metadata_file)
                # Display metadata
                metadata_text = ""
                for key, value in metadata.items():
                    metadata_text += f"{key}: {value}\n"

                self.metadata_label.setAlignment(Qt.AlignLeft)
                self.metadata_label.setText(metadata_text)

            else:
                self.metadata_label.setAlignment(Qt.AlignCenter)
                self.metadata_label.setText("No STM metadata found")
            self.status_label.setText(f"Image {index + 1} of {len(self.image_list)}\n{image_path}")

    def next_image(self):
        """Displays the next image in the image_list."""
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.display_image(self.current_index)
            self.slider.setValue(self.current_index)

    def previous_image(self):
        """Displays the previous image in the image_list."""
        if self.current_index > 0:
            self.current_index -= 1
            self.display_image(self.current_index)
            self.slider.setValue(self.current_index)
    
    def resizeEvent(self, event):
        # Handle the window resize event to adjust the pixmap
        if self.image_list and 0 <= self.current_index < len(self.image_list):
            pixmap = QPixmap(self.image_list[self.current_index])
            # Scale the pixmap based on the new label size
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)
        super().resizeEvent(event)

class NewSampleWidget(QWidget):
    status = pyqtSignal(str)

    def __init__(self):
        super(NewSampleWidget, self).__init__()
        self.initUI()

    def initUI(self):
        # Main vertical layout
        self.main_layout = QVBoxLayout(self)

        # Tab widget for managing tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)  # Enable tab closing
        self.tab_widget.tabCloseRequested.connect(self.remove_tab)
        self.main_layout.addWidget(self.tab_widget)

        add_tab_layout = QHBoxLayout()

        # Button to add new tabs
        self.add_tab_button = QPushButton("New section")
        self.add_tab_button.setStyleSheet("background-color: white; color: #4F81BD; padding: 8px; border-radius: 5px; border: 1px solid #D3D3D3; font-weight: bold; font-size: " + Widget.fontSize_body)
        self.add_tab_button.clicked.connect(self.add_tab)
        add_tab_layout.addStretch(3)
        add_tab_layout.addWidget(self.add_tab_button,1)
        self.main_layout.addLayout(add_tab_layout)
        
        # Save button for json file
        save_button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet("background-color: #32CD32; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: " + Widget.fontSize_body)
        self.save_button.setToolTip("Save the sample metadata on a JSON file and create a corresponding resource on eLabFTW")
        self.save_button.clicked.connect(self.save_data)
        save_button_layout.addStretch(4)
        save_button_layout.addWidget(self.save_button,2)
        save_button_layout.addStretch(4)
        self.main_layout.addLayout(save_button_layout)

        self.setLayout(self.main_layout)

    def add_tab(self):
        """Adds a new tab with a specific accordion"""
        tab_selection_dialog = TabSelectionDialog(self)
        tab_selection_dialog.setMinimumWidth(300)
        if tab_selection_dialog.exec_():
            tab_name, tab_type = tab_selection_dialog.get_selected_tab()
            new_tab = AccordionTab(tab_name, tab_type)
            index = self.tab_widget.addTab(new_tab, tab_name)
            
            close_button = QPushButton("×")
            close_button.setFixedSize(16, 16)
            close_button.clicked.connect(lambda _, idx=index: self.remove_tab(self.tab_widget.indexOf(new_tab)))
            
            # Wrapper for the tab title layout with a close button
            tab_widget = QWidget()
            tab_layout = QHBoxLayout(tab_widget)
            tab_layout.addWidget(QLabel(tab_name))
            tab_layout.addWidget(close_button)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.setSpacing(5)
            tab_widget.setLayout(tab_layout)
            
            self.tab_widget.setTabText(index, "")  # Hides the text to display the custom widget
            self.tab_widget.setTabBarAutoHide(False)
            self.tab_widget.tabBar().setTabButton(index, QTabBar.RightSide, tab_widget)

    def remove_tab(self, index):
        """Removes the tab at the specified position"""
        if index >= 0:
            self.tab_widget.removeTab(index)
    
    def save_data(self):
        data = {}  # Main dictionary

        for tab_index in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(tab_index)
            
            if isinstance(tab_widget, AccordionTab):
        
                tab_name = tab_widget.tab_name

                # Add a recursive index if the tab name already exists
                if tab_name in data:
                    tab_count = 2
                    new_tab_name = f"{tab_name} {tab_count}"
                    while new_tab_name in data:
                        tab_count += 1
                        new_tab_name = f"{tab_name} {tab_count}"
                    tab_name = new_tab_name

                data[tab_name] = tab_widget.get_data()  # Get tab data
        
        # Check for the presence of the sample name entry
        if not data["General properties"]["Sample ID"]["Sample name"]:
            QMessageBox.warning(self, "Error", "Sample name is missing.")
            return
        # Check for the presence of the sample Creation date entry
        if not data["General properties"]["Sample ID"]["Creation date"]:
            QMessageBox.warning(self, "Error", "Creation date is missing.")
            return
        # Check for the correct format (YYYY-MM-DD) and validity of the "Creation date" entry
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["General properties"]["Sample ID"]["Creation date"]):
            QMessageBox.warning(self, "Error", "'Creation date' invalid format.\nCorrect format: YYYY-MM-DD.")
            return
        else:
            # Check for the date validity
            try:
                datetime.datetime.strptime(data["General properties"]["Sample ID"]["Creation date"], "%Y-%m-%d")
            except ValueError:
                QMessageBox.warning(self, "Error", "'Creation date' is invalid.")
                return

        # Create the path for the sample metadata folder (for .json files)
        now = datetime.datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        samplemetadata_path = os.path.join(app_paths.sampleJSON_prefix, year, year+month+day, "Samples_metadata")

        # Create the path for the sample metadata JSON file
        samplemetadata_jsonfile = os.path.join(samplemetadata_path, data["General properties"]["Sample ID"]["Sample name"] + "_metadata.json")

        # Check to prevent the overwriting of files
        if os.path.exists(samplemetadata_jsonfile):
            response = QMessageBox.warning(self, 
                                "Warning", 
                                "Sample " + data["General properties"]["Sample ID"]["Sample name"] + " already exists. Do you want to overwrite the metadata file?", 
                                QMessageBox.Yes | QMessageBox.No, 
                                QMessageBox.No)
            if response == QMessageBox.Yes:
                pass
            else:
                return

        # Create sample metadata folder (for .json files)
        if not os.path.exists(samplemetadata_path):
            os.makedirs(samplemetadata_path)
               
        # Write the sample metadata JSON file
        with open(samplemetadata_jsonfile, "w", encoding="utf-8") as sampleJSONfile:
            json.dump(data, sampleJSONfile, indent=4, ensure_ascii=False)

        #Initialize the body text for eLabFTW item page
        eLabFTW_body_text_html = ""
        
        #Initialize the body text for sections
        section_html_text = ""
        for section in data:
            #Initialize the body text for subsections
            subsection_html_text = ""            
            for subsection in data[section]:
                #Initialize the body text for entries
                entry_html_text = ""
                for entry_label, entry_value in data[section][subsection].items():
                    entry_html_text += (
                       f"{entry_label} = {entry_value}\n"
                        "\u003Cbr\u003E\n"
                    )

                subsection_html_text += (
                    "\u003Cdetails\u003E\n"
                    "    \u003Csummary\u003E\n"
                    "    \u003Cspan style=\"color:rgb(112,112,112);\"\u003E\n"
                    "        \u003Cstrong\u003E\n"
                   f"            {subsection}\n"
                    "        \u003C/strong\u003E\n"
                    "        \u003C/span\u003E"
                    "    \u003C/summary\u003E\n"
                    "    \u003Cp style=\u0022padding-left:30px;\u0022\u003E\n"
                   f"        {entry_html_text}\n"
                    "    \u003C/p\u003E\n"
                    "\u003C/details\u003E"
                )

            section_html_text += (
                "\u003Cdetails\u003E\n"
                "    \u003Csummary\u003E\n"
                "        \u003Cspan style=\"font-size:15pt;\"\u003E\n"
                "        \u003Cstrong\u003E\n"
               f"            {section}\n"
                "        \u003C/strong\u003E\n"
                "        \u003C/span\u003E\n"
                "    \u003C/summary\u003E\n"
               f"        {subsection_html_text}\n"
                "    \u003Cp\u003E\n"
                "    \u003C/p\u003E\n"
                "\u003C/details\u003E"
            )

        eLabFTW_body_text_html += (
            "\u003Cdetails\u003E\n"
            "    \u003Csummary\u003E\n"
            "        \u003Cspan style=\"color:rgb(186,55,42);\"\u003E\n"
            "        \u003Cspan style=\"font-size:16pt;\"\u003E\n"
            "        \u003Cstrong\u003E\n"
           f"            Sample {data['General properties']['Sample ID']['Sample name']}\n"
            "        \u003C/strong\u003E\n"
            "        \u003C/span\u003E\n"
            "    \u003C/summary\u003E\n"
           f"        {section_html_text}\n"
            "    \u003Cp\u003E\n"
            "    \u003C/p\u003E\n"
            "\u003C/details\u003E"
        )

        eLabFTW_itemdata = {'title': data["General properties"]["Sample ID"]["Sample name"],
                            'date': data["General properties"]["Sample ID"]["Creation date"],
                            'body': eLabFTW_body_text_html
                    }

        #Initialize a list for eLabFTW tags
        tag_list = []
        # Add Substrate and Layers tags
        if "Sample composition/structure" in data["General properties"]:
            for entry in data["General properties"]["Sample composition/structure"]:
                if entry.split(" ")[0] == "Substrate" or entry.split(" ")[0] == "Layer":
                    if data["General properties"]["Sample composition/structure"][entry] and data["General properties"]["Sample composition/structure"][entry] not in tag_list:
                        tag_list.append(data["General properties"]["Sample composition/structure"][entry])
        # Add graphene and dosed gas (used for graphene growth) tags
        if "Graphene growth" in data:
            if "graphene" not in tag_list:
                tag_list.append("graphene")
            for subsection in data["Graphene growth"]:
                if "Dosed gas" in data["Graphene growth"][subsection]:
                    if data["Graphene growth"][subsection]["Dosed gas"] and data["Graphene growth"][subsection]["Dosed gas"] not in tag_list:
                        tag_list.append(data["Graphene growth"][subsection]["Dosed gas"])
        # Add others dosed gases tags
        if "Gas exposure" in data:
            for subsection in data["Gas exposure"]:
                if "Dosed gas" in data["Gas exposure"][subsection]:
                    if data["Gas exposure"][subsection]["Dosed gas"] and data["Gas exposure"][subsection]["Dosed gas"] not in tag_list:
                        tag_list.append(data["Gas exposure"][subsection]["Dosed gas"])

        # Create the Sample resource on eLabFTW (Sample --> category_ID = 53)
        item_ID = eLabFTW_credentials.elabftw_api.create_item(category_ID=53, data=eLabFTW_itemdata, tags=tag_list)

        # Dialog to update eLabFTW experiment page
        while True:
            experimentRequest_dialog = QInputDialog(self)
            experimentRequest_dialog.setWindowTitle("Update experiment page")
            experimentRequest_dialog.setLabelText("Do you also want to update your experiment page?\nEnter the experiment ID.")
            experimentRequest_dialog.resize(350, experimentRequest_dialog.sizeHint().height())

            ok = experimentRequest_dialog.exec_()
            experiment_ID = experimentRequest_dialog.textValue().strip()

            if not ok or not experiment_ID:
                QMessageBox.warning(self, "Message", "\"" + data["General properties"]["Sample ID"]["Sample name"] + "\"" + " metadata file successfully created.")
                return
            else:
                try:
                    # Update the experiment page body with resource metadata
                    eLabFTW_credentials.elabftw_api.add_to_body_of_experiment(experiment_ID, eLabFTW_body_text_html)
                    # Link the experiment page to the new resource
                    eLabFTW_credentials.elabftw_api.add_item_link(entity_type = "experiments", entity_id=experiment_ID, item_id=item_ID)
                    QMessageBox.warning(self, "Message", "\"" + data["General properties"]["Sample ID"]["Sample name"] + "\"" + " metadata file successfully created and \"experiment " + experiment_ID + "\" page updated.")
                    return
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"{str(e)}")
                                

"""
TO DO:

- aggiungere tags all'esperimento

- aggiungere link al campione genitore se ce n'è uno

--------------------------------------------
----------------------------------------------
-----------------------------------------------

"""


class TabSelectionDialog(QDialog):
    """Window to select the tab type"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Section selection")
        self.layout = QVBoxLayout(self)

        self.title_dropdown = QComboBox()
        self.title_dropdown.addItems(["General properties", "Cleaning", "Graphene growth", "Gas exposure", "Custom"])
        self.layout.addWidget(self.title_dropdown)

        self.title_edit = QLineEdit()
        self.title_edit.setStyleSheet("font-size: " + Widget.fontSize_body)
        self.title_edit.setPlaceholderText("Enter section name")
        self.title_edit.setVisible(False)
        self.layout.addWidget(self.title_edit)

        self.confirm_button = QPushButton("Ok")
        self.confirm_button.clicked.connect(self.accept)
        self.layout.addWidget(self.confirm_button)

        self.title_dropdown.currentIndexChanged.connect(
            lambda: self.title_edit.setVisible(self.title_dropdown.currentText() == "Custom")
        )

    def get_selected_tab(self):
        """Returns the name and type of the selected tab"""
        if self.title_dropdown.currentText() == "Custom":
            return self.title_edit.text() or "Custom", "Custom"
        return self.title_dropdown.currentText(), self.title_dropdown.currentText()

class AccordionTab(QWidget):
    """Manages a single tab page with accordions"""

    ACCORDION_OPTIONS = {
        "General properties": ["Sample composition/structure", "Problem", "Custom"],
        "Cleaning": ["Sputtering", "Annealing", "Problem", "Custom"],
        "Graphene growth": ["Initial step", "Intermediate step", "Final step", "Problem", "Custom"],
        "Gas exposure": ["Initial step", "Intermediate step", "Final step", "Problem", "Custom"],
        "Custom": ["Custom"]
    }

    OPTION_VALUES = {
        "Sample ID": ["Parent sample", "Comment", "Custom"],
        "Sample composition/structure": ["Substrate", "Layer", "Comment", "Custom"],
        "Layer": [],
        "Sputtering": ["Pressure", "Energy", "Ion current", "Duration", "Comment", "Custom"],
        "Annealing": ["Mode", "Temperature", "Heating rate", "Cooling rate", "Max pressure", "Voltage", "Current", "Duration", "Comment", "Custom"],
        "Initial step": ["Dosed gas", "Pressure", "Exp. duration", "Sample temperature", "Heating voltage", "Heating current", "No exp. duration", "No exp. sample temperature", "Cooling rate", "Start time", "End time", "Comment", "Custom"],
        "Intermediate step": ["Dosed gas", "Pressure", "Exp. duration", "Sample temperature", "Heating voltage", "Heating current", "No exp. duration", "No exp. sample temperature", "Cooling rate", "Start time", "End time", "Comment", "Custom"],
        "Final step": ["Dosed gas", "Pressure", "Exp. duration", "Sample temperature", "Heating voltage", "Heating current", "No exp. duration", "No exp. sample temperature", "Cooling rate", "Start time", "End time", "Comment", "Custom"],
        "Problem": ["Comment", "Custom"],
        "Custom": ["Comment", "Custom"]
    }

    DEFAULT_OPTION_VALUES = {
        "Sample ID": ["Sample name", "Creation date"],
        "Sample composition/structure": ["Substrate"],
        "Sputtering": ["Pressure", "Energy", "Ion current", "Duration"],
        "Annealing": ["Mode", "Temperature", "Heating rate", "Cooling rate", "Max pressure", "Voltage", "Current", "Duration"],
        "Initial step": ["Dosed gas", "Pressure", "Exp. duration", "Sample temperature", "Heating voltage", "Heating current", "Start time"],
        "Intermediate step": ["Dosed gas", "Pressure", "Exp. duration", "Sample temperature", "Heating voltage", "Heating current"],
        "Final step": ["No exp. duration", "No exp. sample temperature", "Heating voltage", "Heating current", "Cooling rate"],
        "Problem": ["Comment"],
        "Custom": []
    }

    def __init__(self, tab_name, tab_type):
        super().__init__()
        self.tab_name = tab_name
        self.tab_type = tab_type
        self.layer_counters = {}  # Dictionary to manage independent numbering for each accordion
        self.existing_accordions = set()  # Set to keep track of already created accordions
        self.initUI()

    def initUI(self):
        # Main vertcal layout
        self.main_layout = QVBoxLayout(self)
        # Section layout
        section_button_layout = QHBoxLayout(self)

        # Scrollable area to contain the accordions
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Container for the accordions
        self.accordion_container = QWidget()
        self.accordion_layout = QVBoxLayout(self.accordion_container)
        self.scroll_area.setWidget(self.accordion_container)

        self.main_layout.addWidget(self.scroll_area)

        # Dropdown menu to select available accordions
        self.accordion_dropdown = QComboBox()
        self.accordion_dropdown.setStyleSheet("padding: 6px; font-size: " + Widget.fontSize_body)
        self.accordion_dropdown.addItems(self.ACCORDION_OPTIONS.get(self.tab_type, []))

        # Add new section button
        self.add_section_button = QPushButton("Add subsection")
        self.add_section_button.setStyleSheet("background-color: #4F81BD; color: white; padding: 6px; border-radius: 5px; font-weight: bold; font-size: " + Widget.fontSize_body)
        self.add_section_button.clicked.connect(self.add_accordion)
        
        section_button_layout.addWidget(self.accordion_dropdown,1)
        section_button_layout.addWidget(self.add_section_button,1)
        section_button_layout.addStretch(4)

        self.setLayout(self.main_layout)  
        self.main_layout.addLayout(section_button_layout)

        if self.tab_type == "General properties":
            self.add_accordion(name="Sample ID")

    def add_accordion(self, name=None, options=None, default=True):
        selected_accordion = name if name else self.accordion_dropdown.currentText()

        if selected_accordion == "Custom" and not name:
            custom_dialog = QInputDialog(self)
            custom_dialog.setWindowTitle("Custom subsection")
            custom_dialog.setLabelText("Enter subsection name")
            custom_dialog.resize(300, custom_dialog.sizeHint().height())

            ok = custom_dialog.exec_()
            text = custom_dialog.textValue()

            if not ok or not text.strip():
                return
            selected_accordion = text.strip()

        # Avoid adding more than one "Sample composition/structure"
        if selected_accordion == "Sample composition/structure" and selected_accordion in self.existing_accordions:
            QMessageBox.warning(self, "Error", "Section 'Sample composition/structure' already exist.")
            return
        # Avoid adding more than one "Sample ID"
        if selected_accordion == "Sample ID" and selected_accordion in self.existing_accordions:
            QMessageBox.warning(self, "Error", "Section 'Sample ID' already exist.")
            return

        accordion_widget = QWidget()
        accordion_layout = QVBoxLayout(accordion_widget)

        accordion = QGroupBox(f"{selected_accordion}")
        accordion.setCheckable(True)
        accordion.setChecked(False)
        accordion.setLayout(QVBoxLayout())

        close_button = QPushButton("×")
        close_button.setFixedSize(32, 32)
        close_button.setStyleSheet("font-weight: bold; color: red; font-size: " + Widget.fontSize_body)
        close_button.setToolTip('Delete')
        close_button.clicked.connect(lambda: self.remove_accordion(accordion_widget, selected_accordion))

        duplicate_button = QPushButton("⧉")
        duplicate_button.setFixedSize(32, 32)
        duplicate_button.setStyleSheet("font-weight: bold; color: blue; font-size: " + Widget.fontSize_body)
        duplicate_button.setToolTip('Duplicate')
        duplicate_button.clicked.connect(lambda: self.duplicate_accordion(selected_accordion, accordion))

        header_layout = QHBoxLayout()
        header_layout.addWidget(accordion)
        #Add the 'delete' and 'duplicate' buttons only if the section is not "Sample ID"
        if selected_accordion != "Sample ID":
            header_layout.addWidget(duplicate_button)
            header_layout.addWidget(close_button)

        select_entry_layout = QHBoxLayout()

        accordion.layout().addLayout(select_entry_layout)
        select_entry_layout.addStretch(4)

        if selected_accordion in self.OPTION_VALUES:
            option_dropdown = QComboBox()
            option_dropdown.setStyleSheet("padding: 4px; font-size: " + Widget.fontSize_body)
            option_dropdown.addItems(self.OPTION_VALUES[selected_accordion])
            select_entry_layout.addWidget(option_dropdown, 1)

            add_option_button = QPushButton("Add entry")
            add_option_button.setStyleSheet("background-color: white; color: #4F81BD; padding: 4px; border-radius: 5px; border: 1px solid #D3D3D3; font-size: " + Widget.fontSize_body)
            add_option_button.clicked.connect(lambda: self.add_option(accordion, option_dropdown.currentText(), selected_accordion))
            select_entry_layout.addWidget(add_option_button, 1)

            # If there are predefined options (for duplication), it adds them
            if options:
                for option_text, value in options:
                    self.add_option(accordion, option_text, selected_accordion, value)

        elif selected_accordion not in self.OPTION_VALUES:
            option_dropdown = QComboBox()
            option_dropdown.setStyleSheet("padding: 4px; font-size: " + Widget.fontSize_body)
            option_dropdown.addItems(self.OPTION_VALUES["Custom"])
            select_entry_layout.addWidget(option_dropdown, 1)

            add_option_button = QPushButton("Add entry")
            add_option_button.setStyleSheet("background-color: white; color: #4F81BD; padding: 4px; border-radius: 5px; border: 1px solid #D3D3D3; font-size: " + Widget.fontSize_body)
            add_option_button.clicked.connect(lambda: self.add_option(accordion, option_dropdown.currentText(), selected_accordion))
            select_entry_layout.addWidget(add_option_button, 1)

            # If there are predefined options (for duplication), it adds them
            if options:
                for option_text, value in options:
                    self.add_option(accordion, option_text, selected_accordion, value)

        # Set default entries for the sections
        if default:
            if selected_accordion in self.DEFAULT_OPTION_VALUES:
                for entry in self.DEFAULT_OPTION_VALUES[selected_accordion]:
                    self.add_option(accordion, entry, selected_accordion)
            elif selected_accordion not in self.DEFAULT_OPTION_VALUES:
                for entry in self.DEFAULT_OPTION_VALUES["Custom"]:
                    self.add_option(accordion, entry, selected_accordion)

        # If 'Sample composition/structure' or 'Sample ID', mark it as existing and disable it in the menu
        if selected_accordion == "Sample composition/structure" or "Sample ID":
            self.existing_accordions.add(selected_accordion)
            self.update_dropdown_state()

        self.layer_counters[selected_accordion] = set()  # Use a set to track the layers of this accordion
        accordion_layout.addLayout(header_layout)
        self.accordion_layout.addWidget(accordion_widget)

    def add_option(self, accordion, option_text, accordion_name, value=""):
        option_widget = QWidget()
        option_layout = QHBoxLayout(option_widget)

        if option_text == "Custom":
            text, ok = QInputDialog.getText(self, "Custom entry", "Enter the entry label")
            if not ok or not text.strip():
                return
            option_text = text.strip()
        
        if option_text == "Layer":
            # Find the first available number only in this accordion
            layer_index = 1
            while layer_index in self.layer_counters[accordion_name]:
                layer_index += 1
            self.layer_counters[accordion_name].add(layer_index)
            option_text = f"Layer {layer_index}"

        # Set a default text for the "Creation date" entry
        if option_text == "Creation date":
            now = datetime.datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%m")
            day = now.strftime("%d")

            value = year + '-' + month + '-' + day
            
        option_label = QLabel(option_text)
        option_label.setStyleSheet("font-size: " + Widget.fontSize_body)

        if option_text != "Mode":
            value_input = QLineEdit()
            value_input.setStyleSheet("font-size: " + Widget.fontSize_body)
            if option_text != "Creation date":
                value_input.setPlaceholderText("Enter value")
            else:
                value_input.setPlaceholderText("e.g., " + year + '-' + month + '-' + day)
            value_input.setText(value)
        elif option_text == "Mode":
            value_input = QComboBox()
            value_input.setStyleSheet("padding: 4px; font-size: " + Widget.fontSize_body)
            value_input.addItems(["auto", "man"])

            # If a value is provided, set the selected value
            if value in ["auto", "man"]:
                value_input.setCurrentText(value)

        remove_button = QPushButton("×")
        remove_button.setFixedSize(25, 25)
        remove_button.setToolTip("Delete")
        remove_button.setStyleSheet("font-weight: bold; color: red; font-size: " + Widget.fontSize_body)
        remove_button.clicked.connect(lambda: self.remove_option(option_widget, option_text, accordion_name))

        option_layout.addWidget(option_label, 5)
        option_layout.addWidget(value_input, 4)
        # Add the "delete" button only if the entry is not "Sample name" or "Creation date" 
        if option_text != "Sample name" and option_text != "Creation date":
            remove_button_layout = QHBoxLayout()
            remove_button_layout.addWidget(remove_button)
            remove_button_layout.addStretch()
            option_layout.addLayout(remove_button_layout,5)
        else:
            option_layout.addStretch(5)

        option_widget.setLayout(option_layout)
        accordion.layout().addWidget(option_widget)

    def remove_option(self, option_widget, option_text, accordion_name):
        if option_text.startswith("Layer "):
            layer_index = int(option_text.split(" ")[1])
            if layer_index in self.layer_counters[accordion_name]:
                self.layer_counters[accordion_name].remove(layer_index)  # Remove the number from the set

        option_widget.setParent(None)
        option_widget.deleteLater()

    def remove_accordion(self, widget, accordion_name):
        # If the removed accordion is 'Sample composition/structure' or 'Sample ID', we re-enable it in the menu
        if accordion_name == "Sample composition/structure" or "Sample ID":
            self.existing_accordions.discard(accordion_name)
            self.update_dropdown_state()

        if accordion_name in self.layer_counters:
            del self.layer_counters[accordion_name]  # Delete the layers of the accordion
        widget.setParent(None)
        widget.deleteLater()
    
    def update_dropdown_state(self):
        """Disable 'Sample composition/structure' and 'Sample ID' if already present, otherwise re-enable them."""
        for item_name in ["Sample composition/structure", "Sample ID"]:
            index = self.accordion_dropdown.findText(item_name)
            if index != -1:
                self.accordion_dropdown.model().item(index).setEnabled(item_name not in self.existing_accordions)
    
    def duplicate_accordion(self, accordion_name, original_accordion):
        options = []
        
        for i in range(original_accordion.layout().count()):
            widget = original_accordion.layout().itemAt(i).widget()
            if isinstance(widget, QWidget):  # Verify it is a widget
                layout = widget.layout()
                if layout and layout.count() > 1:
                    label = layout.itemAt(0).widget()
                    value_widget = layout.itemAt(1).widget()
                    
                    if isinstance(label, QLabel):
                        option_text = label.text()
                        
                        # Check if the input is a QLineEdit or a QComboBox
                        if isinstance(value_widget, QLineEdit):
                            value = value_widget.text()
                        elif isinstance(value_widget, QComboBox):
                            value = value_widget.currentText()  # Get the selected value
                        
                        options.append((option_text, value))
        
        # Create a new accordion with the same options
        self.add_accordion(name=accordion_name, options=options, default=False)

    def get_data(self):
        tab_data = {}

        for i in range(self.accordion_layout.count()):
            widget = self.accordion_layout.itemAt(i).widget()
            if isinstance(widget, QWidget):
                group_box = widget.findChild(QGroupBox)  # find group box (accordion)
                if group_box:
                    section_name = group_box.title()
                    
                    # Add a recursive index if the section name already exists
                    if section_name in tab_data:
                        count = 2
                        new_section_name = f"{section_name} {count}"
                        while new_section_name in tab_data:
                            count += 1
                            new_section_name = f"{section_name} {count}"
                        section_name = new_section_name

                    tab_data[section_name] = {}

                    for j in range(group_box.layout().count()):
                        entry_widget = group_box.layout().itemAt(j).widget()
                        if isinstance(entry_widget, QWidget):
                            entry_layout = entry_widget.layout()
                            if entry_layout and entry_layout.count() > 1:
                                label = entry_layout.itemAt(0).widget()
                                value_widget = entry_layout.itemAt(1).widget()

                                if isinstance(label, QLabel):
                                    entry_name = label.text()

                                    # Add a recursive index if the label already exists
                                    if entry_name in tab_data[section_name]:
                                        entry_count = 2
                                        new_entry_name = f"{entry_name} {entry_count}"
                                        while new_entry_name in tab_data[section_name]:
                                            entry_count += 1
                                            new_entry_name = f"{entry_name} {entry_count}"
                                        entry_name = new_entry_name

                                    if isinstance(value_widget, QLineEdit):
                                        entry_value = value_widget.text()
                                    elif isinstance(value_widget, QComboBox):
                                        entry_value = value_widget.currentText()

                                    tab_data[section_name][entry_name] = entry_value

        return tab_data






// Import the required libraries
importClass(Packages.ij.IJ);
importClass(Packages.ij.io.OpenDialog);
importClass(Packages.ij.WindowManager);
importClass(Packages.ij.text.TextWindow);
importClass(javax.swing.JFileChooser);
importClass(javax.swing.filechooser.FileNameExtensionFilter);
importClass(java.io.File);

try {
    // --- STEP 1: Select multiple .dm4 files ---
    var fileChooser = new JFileChooser();
    fileChooser.setMultiSelectionEnabled(true);
    fileChooser.setFileFilter(new FileNameExtensionFilter("DM4 Files", "dm4"));

    var returnValue = fileChooser.showOpenDialog(null);
    if (returnValue != JFileChooser.APPROVE_OPTION) {
        IJ.log("No file selected.");
        throw new Error("Files not selected ");
    }

    var selectedFiles = fileChooser.getSelectedFiles();
    IJ.log("Number of files selected: " + selectedFiles.length);

    // --- Loop through selected files ---
    for (var f = 0; f < selectedFiles.length; f++) {
        var filePath = selectedFiles[f].getAbsolutePath();
        IJ.log("\n--- File processing: " + filePath + " ---");

        // --- STEP 2: Open ONLY the metadata with Bio-Formats, without loading the image ---
        IJ.run("Bio-Formats Importer", "open=[" + filePath + "] display_metadata only no_open");

        // --- STEP 3: Wait for the metadata window ---
        var maxWaitTime = 5000;  // Maximum waiting time (5 seconds)
        var waitTime = 0;
        var win = null;

        while (waitTime < maxWaitTime) {
            IJ.wait(500);  // Wait half a second
            var windowTitles = WindowManager.getNonImageTitles();
           
            for (var i = 0; i < windowTitles.length; i++) {
                if (windowTitles[i].startsWith("Original Metadata")) {
                    win = WindowManager.getFrame(windowTitles[i]);
                    break;
                }
            }
           
            if (win != null && win instanceof TextWindow) {
                break;
            }
           
            waitTime += 500;
        }

        if (win == null || !(win instanceof TextWindow)) {
            IJ.log("Error: the metadata window was not found for the file: " + filePath);
            continue;  // Skip this file and move on to the next one
        }

        IJ.log("Metadata window found: " + win.getTitle());

        // --- STEP 4: Read the contents of the metadata window ---
        var textPanel = win.getTextPanel();
        var metadataText = textPanel.getText();

        // --- STEP 5: Filter required metadata (Tabella Key-Value) ---
        var lines = metadataText.split("\n");
        var extractedMetadata = {
            "Device Name": "Not found",
            "Formatted Voltage": " Not found ",
            "Exposure (s)": " Not found ",
            "SizeX": " Not found ",
            "SizeZ": " Not found ",
            "Acquisition Date": " Not found ",
            "Acquisition Time": " Not found ",
            "Formatted Indicated Mag": " Not found ",
            "Pixel Size (um)": " Not found ",
            "PixelDepth": " Not found ",
            "Stage Alpha": " Not found ",
            "Stage Beta": " Not found ",
            "Stage X": " Not found ",
            "Stage Y": " Not found ",
            "Stage Z": " Not found "
        };

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            var lineParts = line.split(/\t+/);  // Use tabulation to separate columns

            if (lineParts.length == 2) {
                var key = lineParts[0].trim().toLowerCase();
                var value = lineParts[1].trim();

                if (key === "device name") extractedMetadata["Device Name"] = value;
                if (key === "formatted voltage") extractedMetadata["Formatted Voltage"] = value;
                if (key === "exposure (s)") extractedMetadata["Exposure (s)"] = value;
                if (key === "sizex") extractedMetadata["SizeX"] = value;
                if (key === "sizez") extractedMetadata["SizeZ"] = value;
                if (key === "acquisition date") extractedMetadata["Acquisition Date"] = value;
                if (key === "acquisition time") extractedMetadata["Acquisition Time"] = value;
                if (key === "formatted indicated mag") extractedMetadata["Formatted Indicated Mag"] = value;
                if (key === "pixel size (um)") extractedMetadata["Pixel Size (um)"] = value;
                if (key === "pixeldepth") extractedMetadata["PixelDepth"] = value;
                if (key === "stage alpha") extractedMetadata["Stage Alpha"] = value;
                if (key === "stage beta") extractedMetadata["Stage Beta"] = value;
                if (key === "stage x") extractedMetadata["Stage X"] = value;
                if (key === "stage y") extractedMetadata["Stage Y"] = value;
                if (key === "stage z") extractedMetadata["Stage Z"] = value;
            }
        }

        // --- STEP 6: Show extracted metadata ---
        IJ.log("----- EXTRACTED METADATA FOR: " + filePath + " -----");
        for (var key in extractedMetadata) {
            IJ.log(key + ": " + extractedMetadata[key]);
        }
        IJ.log("----- METADATA END -----");
    }

} catch (e) {
    IJ.log("Error Reading Metadata: " + e);
}

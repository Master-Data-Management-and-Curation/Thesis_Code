// Importa le librerie necessarie
importClass(Packages.ij.IJ);
importClass(Packages.ij.io.OpenDialog);
importClass(Packages.ij.WindowManager);
importClass(Packages.ij.text.TextWindow);
importClass(javax.swing.JFileChooser);
importClass(javax.swing.filechooser.FileNameExtensionFilter);
importClass(java.io.File);

try {
    // --- STEP 1: Seleziona più file .dm4 ---
    var fileChooser = new JFileChooser();
    fileChooser.setMultiSelectionEnabled(true);
    fileChooser.setFileFilter(new FileNameExtensionFilter("DM4 Files", "dm4"));

    var returnValue = fileChooser.showOpenDialog(null);
    if (returnValue != JFileChooser.APPROVE_OPTION) {
        IJ.log("Nessun file selezionato.");
        throw new Error("File non selezionati");
    }

    var selectedFiles = fileChooser.getSelectedFiles();
    IJ.log("Numero di file selezionati: " + selectedFiles.length);

    // --- Loop attraverso i file selezionati ---
    for (var f = 0; f < selectedFiles.length; f++) {
        var filePath = selectedFiles[f].getAbsolutePath();
        IJ.log("\n--- Elaborazione file: " + filePath + " ---");

        // --- STEP 2: Apri SOLO i metadati con Bio-Formats, senza caricare l'immagine ---
        IJ.run("Bio-Formats Importer", "open=[" + filePath + "] display_metadata only no_open");

        // --- STEP 3: Aspetta la finestra dei metadati ---
        var maxWaitTime = 5000;  // Tempo massimo di attesa (5 secondi)
        var waitTime = 0;
        var win = null;

        while (waitTime < maxWaitTime) {
            IJ.wait(500);  // Aspetta mezzo secondo
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
            IJ.log("Errore: la finestra dei metadati non è stata trovata per il file: " + filePath);
            continue;  // Salta questo file e passa al successivo
        }

        IJ.log("Finestra dei metadati trovata: " + win.getTitle());

        // --- STEP 4: Leggi il contenuto della finestra dei metadati ---
        var textPanel = win.getTextPanel();
        var metadataText = textPanel.getText();

        // --- STEP 5: Filtra i metadati richiesti (Tabella Key-Value) ---
        var lines = metadataText.split("\n");
        var extractedMetadata = {
            "Device Name": "Non trovato",
            "Formatted Voltage": "Non trovato",
            "Exposure (s)": "Non trovato",
            "SizeX": "Non trovato",
            "SizeZ": "Non trovato",
            "Acquisition Date": "Non trovato",
            "Acquisition Time": "Non trovato",
            "Formatted Indicated Mag": "Non trovato",
            "Pixel Size (um)": "Non trovato",
            "PixelDepth": "Non trovato",
            "Stage Alpha": "Non trovato",
            "Stage Beta": "Non trovato",
            "Stage X": "Non trovato",
            "Stage Y": "Non trovato",
            "Stage Z": "Non trovato"
        };

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            var lineParts = line.split(/\t+/);  // Usa la tabulazione per separare le colonne

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

        // --- STEP 6: Mostra i metadati estratti ---
        IJ.log("----- METADATI ESTRATTI PER: " + filePath + " -----");
        for (var key in extractedMetadata) {
            IJ.log(key + ": " + extractedMetadata[key]);
        }
        IJ.log("----- FINE METADATI -----");
    }

} catch (e) {
    IJ.log("Errore nella lettura dei metadati: " + e);
}

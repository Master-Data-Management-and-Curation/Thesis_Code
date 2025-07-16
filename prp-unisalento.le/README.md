# TEM Metadata Extraction and Integration Pipeline

This repository documents a pipeline developed for the FAIR-compliant extraction, transformation, and integration of TEM `.dm4` metadata into structured formats and Electronic Lab Notebooks (ELNs) like ElabFTW.

It includes the following tools:

- `extract_dm4_fiji.js`: Interactive JavaScript script for ImageJ (Fiji) to extract and display metadata from multiple `.dm4` files.
- `extract_dm4_metadata.py`: Python script for automatic batch extraction of metadata from `.dm4` files and saving in `.json` and `.txt`.
- `elabftw_integration.ipynb`: Python notebook to create or update experiments and items in ElabFTW via API using the previously extracted metadata.

This workflow supports the systematic management of data generated with Gatan Digital Micrograph from a JEOL JEM ARM 200F Neoarm microscope, as described in the thesis.

## Directory Structure

```
/input_dm4/
    *.dm4
/output_metadata/
    metadata_output.json
    metadata_output.txt
/notebooks/
    elabftw_integration.ipynb
/scripts/
    extract_dm4_fiji.js
    extract_dm4_metadata.py
```

---

## Script Descriptions

### 1. `extract_dm4_fiji.js`

**Purpose**:  
Allows interactive selection and metadata extraction from multiple `.dm4` files using ImageJ and Bio-Formats plugin.

**Input**:
- User-selected `.dm4` files via a graphical dialog in Fiji.

**Output**:
- Metadata printed in the ImageJ Log window (one per file).

**Instructions**:
- Open Fiji.
- Go to `Plugins > New > Script`, paste the code, set language to JavaScript.
- Run.

**Extracted Fields**:
- Device Name
- Formatted Voltage
- Exposure Time
- Pixel Size
- Acquisition Date and Time
- Magnification
- Stage X/Y/Z, Alpha, Beta, etc.

---

### 2. `extract_dm4_metadata.py`

**Purpose**:  
Automates the batch extraction of key metadata from `.dm4` files using the `ncempy` Python library and saves the results.

**Input**:
- Folder containing `.dm4` files.

**Output**:
- `metadata_output.json`: Structured metadata in machine-readable format.
- `metadata_output.txt`: Human-readable version for validation.

**Instructions**:
Update:
```python
# Run the script and choose folder interactively
python extract_dm4_metadata.py
```

**Features**:
- Uses recursive search to handle nested metadata structure.
- Converts NumPy types to native Python.
- Saves results in both JSON and TXT.
- Handles missing metadata gracefully.

---

### 3. `elabftw_integration.ipynb`

**Purpose**:  
Uses ElabFTW’s REST API to create or update Experiments and Items based on extracted metadata.

**Instructions**:
- Open the notebook with Google Colab.
- Provide API Key and Base URL.
- Use functions like `create_experiment`, `get_items`, `update_experiment` to interact with ElabFTW.

**Capabilities**:
- GET/POST/PATCH for both experiments and resources (items).
- Automatic tagging and linking between metadata and lab entries.
- Error handling and status verification for each API call.

---

## Workflow Summary

1. **Extract Metadata via Fiji (interactive)**  
   ➤ `extract_dm4_fiji.js`

2. **Batch Export Metadata to Files (automated)**  
   ➤ `extract_dm4_metadata.py`

3. **Upload Structured Data to ELN**  
   ➤ `elabftw_integration.ipynb`

---

## Requirements

Install necessary packages:
```bash
pip install numpy ncempy requests
```
Fiji must be installed separately for `.js` script.

---

## Notes

- All tools follow FAIR principles by ensuring metadata is structured, reusable, and linked to experiments.
- The `.dm4` structure is parsed using open-source tools, ensuring transparency and reproducibility.
- ElabFTW serves as the centralized metadata repository and documentation tool, enabling automation and collaboration.


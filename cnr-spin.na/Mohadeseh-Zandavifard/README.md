
# NeXus Converter for MODA XPS

This folder contains two files:

- `NeXus_converter_for_MODA_XPS.py`: the main Python script to convert XPS `.vms` data files into NeXus `.nxs` format using metadata.
- `MODA_config.json`: the configuration file used to define the structure of the output NeXus file.


---

## How to Use

### 1. Download the Files

Download both `NeXus_converter_for_MODA_XPS.py` and `MODA_config.json` to the same folder on your computer.

### 2. Install Required Packages

Open a terminal (or command prompt) and run the following commands to install the necessary Python packages:

```bash
pip install pynxtools[xps]
pip install pyyaml
```

### 3. Run the Script

In the terminal, navigate to the folder where the files are saved and run:

```bash
python NeXus_converter_for_MODA_XPS.py
```

### 4. Follow the Prompts

- The script will show a list of `.vms` files in the folder. Choose the one you want to convert.
- It will ask if you want to use an existing `eln.yaml` metadata file or create a new one.
- The output will be a NeXus `.nxs` file, saved in the same folder. If a file with the same name already exists, it will add `_1`, `_2`, etc.

---

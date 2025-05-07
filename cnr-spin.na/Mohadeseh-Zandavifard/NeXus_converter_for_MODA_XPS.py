import os
import subprocess
import sys
import time
import glob
import yaml
import json
from datetime import datetime
import importlib

# ✅ Pre-check dependencies and required files
REQUIRED_FILES = ["MODA_config.json"]
REQUIRED_PACKAGES = ["pynxtools","yaml"]

for req in REQUIRED_FILES:
    if not os.path.isfile(req):
        print(f"\033[91m❌ Required file '{req}' is missing. Please add it to this folder.\033[0m")
        sys.exit(1)


# ✅ Check for required packages
REQUIRED_MODULES = {
    "pynxtools": "pip install git+https://github.com/FAIRmat-NFDI/pynxtools-xps.git@main",
    "yaml": "pip install pyyaml",
    "pandas": "pip install pandas",
    "numpy": "pip install numpy",
    "matplotlib": "pip install matplotlib",
    "scipy": "pip install scipy"
}

missing = []

for module, install_cmd in REQUIRED_MODULES.items():
    try:
        importlib.import_module(module)
    except ImportError:
        missing.append((module, install_cmd))

if missing:
    print("\n\033[91m❌ Missing required packages:\033[0m")
    for module, install_cmd in missing:
        print(f" - {module}: {install_cmd}")
    print("\n👉 Please install the missing packages above and re-run the script.")
    sys.exit(1)

# Function to choose a .vms file
def choose_vms_file():
    vms_files = glob.glob("*.vms")
    if not vms_files:
        print("\033[91m❌ No .vms files found in this directory.\033[0m")
        sys.exit(1)
    print("\n\033[94m📂 Available .vms files:\033[0m")
    for i, f in enumerate(vms_files):
        print(f"[{i+1}] {f}")
    while True:
        choice = input("\nEnter the number of the .vms file to use: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(vms_files):
            return vms_files[int(choice) - 1]
        print("\033[91mInvalid choice. Please select a valid number from the list.\033[0m")

# Function to choose or create ELN YAML
def choose_or_create_eln():
    yaml_files = glob.glob("*.yaml")
    print("\n\033[94m📄 Available YAML metadata files:\033[0m")
    for i, f in enumerate(yaml_files):
        print(f"[{i+1}] {f}")
    print("[N] ➕ Create a new ELN YAML file")

    while True:
        choice = input("\nChoose a file by number or 'N' to create new: ").strip().lower()
        if choice == 'n':
            return create_eln_yaml()
        if choice.isdigit() and 1 <= int(choice) <= len(yaml_files):
            return yaml_files[int(choice) - 1]
        print("\033[91mInvalid choice. Please select a valid number or 'N'.\033[0m")

# Option selection helper
def ask_from_list(prompt, options, default):
    print(f"\n{prompt} \033[90m(default: {default})\033[0m")
    for i, opt in enumerate(options):
        print(f"[{i+1}] {opt}")
    while True:
        choice = input("Enter number or press Enter for default: ").strip()
        if not choice:
            return default
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("\033[91mInvalid choice. Try again.\033[0m")

# Prompt input with required value
def ask(prompt, default=None):
    while True:
        val = input(f"{prompt} " + (f"[default: {default}]: " if default else ": "))
        val = val.strip() or default
        if val:
            return val
        print("\033[91mThis field is required. Please enter a value.\033[0m")

# Create a new ELN YAML file
def create_eln_yaml():
    print("\n\033[92m✏️ Creating ELN metadata for the XPS experiment...\033[0m")

    source_probe_types = [
        'Synchrotron X-ray Source', 'Rotating Anode X-ray', 'Fixed Tube X-ray', 'UV Laser',
        'Free-Electron Laser', 'Optical Laser', 'UV Plasma Source', 'Metal Jet X-ray',
        'HHG laser', 'UV lamp', 'Monochromatized electron source']
    collectioncolumn_schemes = [
        'angular dispersive', 'spatial dispersive', 'momentum dispersive', 'non-dispersive']
    energydispersion_schemes = [
        'tof', 'hemispherical', 'double hemispherical', 'cylindrical mirror',
        'display mirror', 'retarding grid']

    eln = {
        'title': ask("📌 Experiment title", "XPS Experiment"),
        'user': {
            'name': ask("👤 User name"),
            'affiliation': ask("🏛️ Affiliation")
        },
        'instrument': {
            'vendor': ask("🏷️ Instrument vendor", "Scienta Omicron"),
            'model': ask("🎚️ Instrument model", "OMICRON model"),
            'source_probe': {
                'type': ask_from_list("💡 Source probe type", source_probe_types, "Fixed Tube X-ray")
            },
            'electronanalyzer': {
                'collectioncolumn': {
                    'scheme': ask_from_list("📐 Collection column scheme", collectioncolumn_schemes, "angular dispersive")
                },
                'energydispersion': {
                    'scheme': ask_from_list("📏 Energy dispersion scheme", energydispersion_schemes, "hemispherical")
                }
            }
        },
        'sample': {
            'name': ask("🔬 Sample name", "SPIN-Napoli-sample-name"),
            'identifier': ask("🧾 Sample identifier", "Napoli-sample-identifier")
        }
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    eln_filename = f"eln_{timestamp}.yaml"
    with open(eln_filename, 'w') as f:
        yaml.dump(eln, f, sort_keys=False)
    print(f"\n\033[92m✅ ELN file saved as: {eln_filename}\033[0m\n")
    return eln_filename

# Generate unique output filename
def get_output_filename(input_file):
    base = os.path.splitext(input_file)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = f"{base}_converted_{timestamp}.nxs"
    count = 1
    while os.path.exists(output):
        output = f"{base}_converted_{timestamp}_{count}.nxs"
        count += 1
    return output

# Main execution
def main():
    CONFIG_FILE = "MODA_config.json"
    vms_file = choose_vms_file()
    eln_file = choose_or_create_eln()
    output_file = get_output_filename(vms_file)

    cmd = [
        "dataconverter",
        vms_file,
        eln_file,
        "-c", CONFIG_FILE,
        "--nxdl", "NXxps",
        "--reader", "xps",
        "--ignore-undocumented",
        "--output", output_file
    ]

    print("\n\033[96m⚙️  Running conversion...\033[0m")
    print(" ".join(cmd))
    subprocess.run(cmd)

    print("\n\033[95m📋 Summary:\033[0m")
    print(f"- Input VMS file: {vms_file}")
    print(f"- ELN metadata : {eln_file}")
    print(f"- Config file  : {CONFIG_FILE}")
    if os.path.isfile(output_file):
        print(f"- Output NeXus : {output_file}")
        print("\n\033[92m🎉 Conversion successful!\033[0m")
        
    else:
        print("\033[91m❌ Conversion failed. No NeXus file was generated.\033[0m")

if __name__ == "__main__":
    main()

# Tecan File Uploader to ElabFTW

This script (`update.py`) automates the process of scanning Tecan result files from a specific folder (based on the current date), parses the content into an HTML table, and uploads it to a new experiment in [ElabFTW](https://www.elabftw.net/).

## Features

- Scans the daily directory `tecan_files/YYYY-MM-DD` for `.txt` files
- Parses each file (expecting a two-line format: header and data)
- Converts the parsed data into an HTML table
- Automatically creates a new experiment in ElabFTW
- Attaches the HTML table to the experiment body

## File Format Expected

Each `.txt` file must have the following format:
Column1;Column2;Column3
Value1;Value2;Value3


## Prerequisites

- Python 3.x
- `decos_elabftw` module
- A valid ElabFTW API key and base URL
- Install dependencies:

```bash
pip3 install requests
```
## Configuration
Edit the following section in update.py if necessary:

```
elab = ElabFTWAPI(
    base_url='https://your-elab-url',
    api_key='your-api-key'
)
```
Ensure your directory structure is as follows:
```
project_root/
└── tecan_files/
    └── YYYY-MM-DD/
        ├── result1.txt
        └── result2.txt
```
The Fluent Control software will generate a folder as follow:

Look in tecan_files/YYYY-MM-DD

and will create one experiment for each `.txt` file found

## Installation & Usage

1. Clone this repository or copy the script.
2. Then simply run:

```
python3 Fluent_control_to_elabFTW.py
```


## Security Warning
⚠️ Never commit your actual API key to a public repository!
It's highly recommended to load your API key and base URL from environment variables or a configuration file.

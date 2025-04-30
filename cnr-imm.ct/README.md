## NOMAD Plugin QuTiP

This repository contains a NOMAD plugin designed to integrate simulation data generated using the QuTiP (Quantum Toolbox in Python) library into your NOMAD Oasis instance. It provides the necessary schemas and tools to parse and visualize QuTiP simulation results within the NOMAD framework.

## Prerequisites

Before installing this plugin, please ensure you have:

1.  A running NOMAD Oasis instance.
2.  The `NOMAD-simulations` plugin installed and enabled in your NOMAD Oasis setup, as this plugin depends on it.

## Installation

To add this plugin to your NOMAD Oasis installation, follow these steps:

1.  Navigate to the root directory of your NOMAD Oasis installation.
2.  Add this plugin repository as a git submodule using the following command:

    ```bash
    git submodule add https://github.com/GiovanniCastorina/nomad-plugin-qutip packages/nomad-plugin-qutip
    ```

3.  After adding the submodule, you might need to rebuild or restart your NOMAD Oasis instance for the changes to take effect (follow the standard procedures for your specific NOMAD setup).

## Workflow

The intended workflow for getting your QuTiP simulation data into NOMAD using this plugin is as follows:

1.  **Generate Simulation Data:** Perform your quantum simulation using QuTiP.
2.  **Format Output:** Use the provided `json_writer.py` library. This library contains helper functions specifically designed to structure your simulation results (inputs, outputs, system details, etc.) into a JSON format that adheres to the schemas defined by this plugin.
3.  **Save JSON File:** Ensure the output JSON file containing your structured data is saved with the specific file extension: `.qutip.json`. This extension allows NOMAD to identify the file and process it using this plugin's parser.
4.  **Upload to NOMAD:** Upload the generated `.qutip.json` file to your NOMAD Oasis instance through the upload interface. NOMAD will automatically parse the file using this plugin and make the data available.

## Example

An example Jupyter Notebook, `Example.ipynb`, is included in this repository.

* **Content:** It demonstrates a simple simulation of a spin-1/2 system using QuTiP.
* **Purpose:** The notebook shows how to use the functions within `json_writer.py` to automatically generate a NOMAD-compatible `.qutip.json` file from the simulation results.

This serves as a practical guide to understand how to structure your own data using the provided tools.

## License

Both the `json_writer.py` library and the `Example.ipynb` notebook are open-source code released under the **MIT License**.

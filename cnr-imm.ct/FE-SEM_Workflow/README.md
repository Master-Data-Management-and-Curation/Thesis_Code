# FAIR Data Parser for MulSKIPS PVD Simulations

This repository contains a unified Python parser that automates the execution, analysis, and FAIR data export of Physical Vapor Deposition (PVD) simulations using the MulSKIPS atomistic simulation environment. The parser is designed to produce NeXus files compliant with the FAIRmat `NXmicrostructure_imm_config` and `NXmicrostructure_imm_results` schema definitions.

---

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/fair-pvd-parser
   cd fair-pvd-parser
   ```

2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

Dependencies include:
- `h5py`
- `numpy`
- `pymulskips` (custom module)
- `nexusformat`
- `matplotlib` (optional, for visualization)

---

## ▶️ How to Use

You can run the parser as a script:
```bash
python Parser.py --input config.yaml
```

Or use the Jupyter notebook version:
```bash
jupyter notebook Parser_30_04_25.ipynb
```

The parser will:
- Run a MulSKIPS PVD simulation using `run_PVD_SiC.py`
- Analyze the results via `analyze_PVD_SiC.py`
- Extract simulation metadata and results
- Export a structured `.nxs` file compatible with FAIRmat

---

## 🔄 Workflow

```
[User Input (YAML)]
        ↓
[Run Simulation (MulSKIPS)]
        ↓
[Analyze Results (growth rate, etc.)]
        ↓
[Export Metadata + Results]
        ↓
[Write NeXus File (NXmicrostructure_imm_*)]
        ↓
[Publish to NOMAD / Zenodo]
```

---

## 🧬 Metadata Structure

The NeXus output file (`SiC_sample_XXX.nxs`) includes:

### NXmicrostructure_imm_config
- `simulation_code`: "MulSKIPS"
- `substrate_material`: e.g. "3C-SiC"
- `deposition_method`: "PVD"
- `growth_direction`: [0, 0, 1]
- `parameters`: deposition flux, temperature, time, etc.

### NXmicrostructure_imm_results
- `growth_rate`: float (e.g. nm/s)
- `final_thickness`: float (e.g. nm)
- `vacancy_density`: float or array
- `surface_height_profile`: array (optional)
- `trajectory_file`: optional `.xyz` or inlined string

For schema compliance:
- [`NXmicrostructure_imm_config`](https://fairmat-nfdi.github.io/nexus_definitions/classes/contributed_definitions/NXmicrostructure_imm_config.html)
- [`NXmicrostructure_imm_results`](https://fairmat-nfdi.github.io/nexus_definitions/classes/contributed_definitions/NXmicrostructure_imm_results.html)

---

## 📁 Project Structure

```
├── run_PVD_SiC.py                # Runs the MulSKIPS simulation
├── analyze_PVD_SiC.py            # Post-processes simulation output
├── Parser_30_04_25.ipynb         # Unified notebook parser
├── SiC_sample_153.nxs            # Example NeXus file output
├── utils/
│   └── nexus_writer.py           # NeXus file generation helper
├── data/
│   ├── input_config.yaml         # Example input configuration
│   └── output/                   # Contains raw and processed results
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 📚 References

This tool is part of the Master's thesis:

> Filippo Ruberto,  
> "FAIR Data Management of the Results from the MulSKIPS Atomistic Simulation Environment for PVD, CVD, and Laser Annealing"  
> Master in Data Management and Curation – SISSA, 2025

Developed at:  
CNR-IMM@CT (Supervisor: Antonino La Magna)  
with support from AREA (Supervisor: Matteo Biagetti)  
and in the context of the NFFA-DI project.

Uses and cites:
- MulSKIPS simulation framework [https://github.com/MulSKIPS](https://github.com/MulSKIPS)
- FAIRmat NeXus definitions [https://fairmat-nfdi.github.io/nexus_definitions/](https://fairmat-nfdi.github.io/nexus_definitions/)
- NOMAD and Zenodo as FAIR repositories

---

## 🧪 License and Acknowledgments

This work is intended for educational and research purposes under the FAIR principles.  
Please cite the thesis or contact the author if used in academic work.


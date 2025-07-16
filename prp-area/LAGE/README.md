In this folder we can find the ont_integrated_analyzer.py file. The file is a script used during my thesis work to run a detailed analysis of the outputs from the Oxford Nanopore Tech sequencing runs. It is a Python script. 

The code does:
  1 - validate data copleteness
  2 - extract quality metrics
  3 - assess sequencing performance
  4 - enhance dataset documentation for reproducibility and reuse

# usage
python ont_integrated_analyzer.py /path/to/nanopore_data_directory

# outputs
 1 - terminal report: analysis summary
 2 - README.md: human-readable documentation
 3 - metadata.json: machine-readable metadata
 4 - checksums.md5: for data integrity verification

# requirements
Dependencies: pandas, numpy, matplotlib
Oxford Nanopore sequencing data directory containing:
 - POD5 files (raw signal data)
 - FASTQ files (basecalled sequences)
 - Summary files (run metrics)

This repository contains a suite of Jupyter notebooks originally developed and tested in Google Colab for analyzing image quality in Scanning Electron Microscope (SEM) datasets. The toolkit combines no-reference image quality metrics (BRISQUE, NIQE) with image metadata for quality assessment, clustering, and statistical analysis.
Notebooks Overview:
Full_Factorial_Design.ipynb
Implements a factorial design experiment using the extracted features.

All_Metadata_Extraction.ipynb
Extracts metadata from SEM image files using tools like ExifTool.

Standardized_File_Naming_.ipynb
Renames image files using a standardized convention for better traceability.

Filtering_the_metadata.ipynb
Filters and refines the metadata for quality control and relevance.

brisque_scores_with_metadata.ipynb
Computes BRISQUE scores and appends them to the corresponding metadata.

niqe_scores_with_metadata.ipynb
Computes NIQE scores and appends them to the corresponding metadata.

SEM_Dataset.ipynb
Loads and previews the SEM image dataset used throughout the notebooks.

clustring_with_NIQE.ipynb
Clusters SEM images based on their NIQE scores.

clustring_with_BRISQUE.ipynb
Clusters SEM images based on their BRISQUE scores.

surface_regression_with_NIQE.ipynb
Builds regression models using NIQE scores to analyze surface quality and trends.

Surface_Regression_with_BRISQUE.ipynb
Predicts surface characteristics using regression models trained on BRISQUE scores.

Dependencies:
These notebooks are designed for Google Colab, which includes most common packages. For local execution, ensure the following packages are installed:

pip install numpy pandas scikit-image scikit-learn opencv-python matplotlib seaborn image-quality pyexiftool

Based on referee feedback, a single consolidated notebook named sem_quality_analysis_combined.ipynb has been added. It contains clean, PEP 8-compliant code with clear inline comments, combining all analysis steps for SEM image quality evaluation.


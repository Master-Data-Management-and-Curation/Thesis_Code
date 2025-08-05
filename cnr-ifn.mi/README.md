# Giovanni Gallerani

This repository contains the software developed during the internship at CNR-IFN@MI, specifically for the UDynI research group. The work focused on creating tools to improve data management and accessibility within the lab. Two key software components were developed:

-   **udyninexus**: This Python package streamlines the creation of NeXus-compliant data files. By providing a straightforward interface, `udyninexus` aims to facilitate the adoption of the standardized NeXus data format within the existing data acquisition workflows of the beamlines. This ensures better data integration and interoperability.

-   **LabLogbook**: Integrated within the existing UdyniManagement Django project, LabLogbook is a web-based application designed for efficient experiment and sample management, coupled with a comprehensive digital logbook. Furthermore, it exposes RESTful APIs, laying the groundwork for the future development of a robust FAIR (Findable, Accessible, Interoperable, Reusable) data infrastructure within the UDynI laboratories.

    **Important Note**: LabLogbook is not a standalone application. To run it, it is necessary to set up the UdyniManagement project first by following the instructions provided below.


## UdyniManagement Setup

The following steps outline how to set up the UdyniManagement project, which includes the LabLogbook application.

### Prerequisites (Install Development Files)

Before installing the Python requirements, ensure the following development libraries are present on your system:

```bash
sudo apt update
sudo apt install libfreetype6-dev
sudo apt install libldap2-dev
sudo apt install libsasl2-dev
```

### Installation

1.  **Create a Virtual Environment:** It's highly recommended to use a virtual environment to isolate project dependencies.

    ```bash
    python3 -m venv venv
    ```

2.  **Activate the Virtual Environment:**

    ```bash
    . venv/bin/activate
    ```

3.  **Install Requirements:** Install the necessary Python packages listed in the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

### Django Project Configuration

1.  **Apply Migrations:** These commands ensure your database schema is up to date with the project's models.

    ```bash
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```

2.  **Create a Superuser:** This account will grant you administrative access to the web interface.

    ```bash
    python3 manage.py createsuperuser
    ```

    Follow the prompts to create your username, email address, and password.

3.  **Start the Development Server:** This command launches the Django development server.

    ```bash
    python3 manage.py runserver
    ```

4.  **Access UdyniManagement:** Open the provided link (usually `http://127.0.0.1:8000/`) in your web browser and log in using the superuser credentials you just created.

5.  **Explore LabLogbook:** Once logged in, navigate to the "Lab Logbook" section. This is the module developed during this internship, and you are welcome to explore its features for managing experiments and samples.
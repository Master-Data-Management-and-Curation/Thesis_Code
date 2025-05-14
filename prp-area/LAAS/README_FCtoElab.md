Import Libraries:
    - requests is used to make HTTP requests to the elabFTW API.
    - json is used to handle JSON data, which is the format elabFTW uses for data exchange.
    - pandas is used to read the csv file and convert it into a dictionary.
    
elabFTW Configuration:
    - ELABFTW_URL: You MUST replace "your_elabftw_instance_url" with the actual URL of your elabFTW installation (e.g., https://my-elabftw.university.edu).
    - ELABFTW_TOKEN: You MUST replace "your_elabftw_api_token" with your personal API token from elabFTW. You can generate this in your elabFTW user settings. Keep this token secret!
    
create_experiment(title, description) Function:
    - Takes an experiment title and description as input.
    - Constructs the API endpoint URL for creating experiments.
    - Sets the necessary headers, including the authorization token and content type.
    - Creates a JSON payload with the title and description.
    - Sends a POST request to the elabFTW API to create the experiment.
    - Handles potential errors during the API request (e.g., network issues, invalid token).
    - Returns the id of the newly created experiment if successful, otherwise returns None.
    
upload_data_to_experiment(experiment_id, data, filename="tecan_data.json") 
Function:
    - Takes the experiment ID, the data to upload, and an optional filename as input.
    - Constructs the API endpoint URL for uploading data to a specific experiment.
    - Sets the headers, including the authorization token.
    - Creates a payload with the data (converted to a JSON string) and the desired filename.
    - Sends a POST request to the elabFTW API to upload the data.
    - Handles potential errors during the upload.
    
load_tecan_data(filepath) 
Function:
    - Takes the filepath of the TECAN data file as input.
    - Uses pandas to read the CSV file. Important: This assumes your TECAN data is in a CSV-like format where the first row is a header, and values are separated by semicolons (;). You might need to adjust the sep argument in pd.read_csv() if your delimiter is different (e.g., comma, tab).
    - Converts the pandas DataFrame to a list of dictionaries, which is a convenient format for JSON serialization.
    - Handles FileNotFoundError if the file doesn't exist.
    - Includes a general Exception handler to catch other potential errors during file loading.
if __name__ == '__main__': Block:
    This block of code runs when you execute the Python script.
    - Loads TECAN data: Calls load_tecan_data() to read your data file. You MUST replace "VariabiliCelero.txt" with the actual path to your TECAN output file. If loading fails, the script exits.
    - Creates the elabFTW experiment: Calls create_experiment() to create a new experiment in elabFTW. You can customize the experiment_title and experiment_description. If experiment creation fails, the script exits.
    - Uploads data to elabFTW: Calls upload_data_to_experiment() to upload the loaded TECAN data to the newly created experiment. The data is uploaded as a JSON file named "celero_data.json". You can change the filename if needed.
    
Before Running:

Install Libraries:
Bash
    pip install requests pandas

Configure elabFTW Details:
    - Replace placeholders: Edit the script and replace "your_elabftw_instance_url" and "your_elabftw_api_token" with your actual elabFTW URL and API token.
    - Set the correct file path: Change "VariabiliCelero.txt" to the correct path to your TECAN data file.
    
Adjust for Your Data Format (If Necessary):
    - If your TECAN output is not a standard CSV with semicolons as separators, you'll need to modify the load_tecan_data() function to parse it correctly. Pandas is very flexible and can handle many different file formats (e.g., TSV, Excel).

To Run:
    Save the code as a Python file (e.g., fluent_control_to_elabftw.py).
    Open a terminal or command prompt.
    Navigate to the directory where you saved the file.
    Execute the script: python fluent_control_to_elabftw.py
    
Important Considerations:
    - Error Handling: The code includes basic error handling (e.g., try-except blocks). You might want to add more robust error logging or handling depending on your needs.
    - Data Mapping: This script uploads the TECAN data as a single JSON file. If you need to map specific TECAN data fields to particular fields or sections within your elabFTW experiment, you'll need to modify the upload_data_to_experiment() function to structure the payload accordingly. You might need to use elabFTW's metadata features or custom fields.
    - File Formats: The script currently reads CSV data. If you have different TECAN output formats (e.g., Excel files), you'll need to adjust the load_tecan_data() function to handle those formats using pandas or other appropriate libraries.
    - Security: Never hardcode your elabFTW API token directly into your script if you're sharing it! Consider using environment variables or a configuration file to store sensitive information.
    - elabFTW API Documentation: Refer to the official elabFTW API documentation for the most up-to-date information on API endpoints, authentication, and data structures: https://www.google.com/search?q=https://doc.elabftw.net/developer/api/

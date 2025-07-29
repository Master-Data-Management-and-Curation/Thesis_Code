import os
import requests

import time
from functools import wraps

def delayed_call(delay_seconds):
    """Decorator that delays the call to the wrapped function by delay_seconds."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(delay_seconds)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# def get_authentication_token(nomad_url):
#     '''Get the token for accessing your NOMAD unpublished uploads remotely'''
#     username = 'mmarella@sissa.it' # USER E PW VANNO O CRIPTATI O MESSI VARIABILI D'AMBIENTE CON EXPORT
#     password =  'jezz09112000'
#     try:
#         response = requests.get(
#             nomad_url + 'auth/token', params=dict(username=username, password=password), timeout=10)
#         token = response.json().get('access_token')
#         if token:
#             return token, True

#         print('response is missing token: ')
#         print(response.json())
#         return None, False
#     except Exception as e:
#         print(f'something went wrong trying to get authentication token:\n{e}')
#         return None, False
def get_authentication_token(nomad_url):
    '''Get the token for accessing your NOMAD unpublished uploads remotely'''
    #username = 'mmarella@sissa.it'  # Consider moving to environment variables
    #password = 'jezz09112000'      # Consider moving to environment variables
    username = 'mattia.mare'  # Consider moving to environment variables
    password = 'Jezz09112000?'      # Consider moving to environment variables

    try:
        response = requests.get(
            nomad_url + 'auth/token', 
            params=dict(username=username, password=password), 
            timeout=10
        )
        response.raise_for_status()  # Explicitly check HTTP status

        token = response.json().get('access_token')
        if token:
            return token, True

        print('Response is missing token:', response.json())
        return None, False

    except requests.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err} - Response: {response.text}')
        raise Exception(f"HTTP error: {http_err}")  # Raise an exception for HTTP errors
        #return None, False

    except requests.RequestException as req_err:
        print(f'Request error occurred: {req_err}')
        raise Exception(f"Request error: {req_err}")  # Raise an exception for request errors
        #return None, False

    except Exception as e:
        print(f'Unexpected error trying to get authentication token:\n{e}')
        raise Exception(f"Unexpected error to get token: {e}")  # Raise an exception for unexpected errors
        #return None, False


# @delayed_call(delay_seconds=5)  # waits 5 seconds before execution
# def upload_to_NOMAD(nomad_url, token, upload_file):
#     '''Upload a single file as a new NOMAD upload. Compressed zip/tar files are
#     automatically decompressed.
#     '''
#     with open(upload_file, 'rb') as f:
#         try:
#             response = requests.post(
#                 f'{nomad_url}uploads?file_name={os.path.basename(upload_file)}',
#                 headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'},
#                 data=f, timeout=30)
#             upload_id = response.json().get('upload_id')
#             if upload_id:
#                 return upload_id, response

#             print('response is missing upload_id: ')
#             print(response.json())
#             return
#         except Exception as e:
#             print(f'something went wrong uploading to NOMAD:\n{e}')
#             return
@delayed_call(delay_seconds=5)  # waits 5 seconds before execution
def upload_to_NOMAD(nomad_url, token, upload_file):
    '''Upload a single file as a new NOMAD upload. Compressed zip/tar files are automatically decompressed.'''
    with open(upload_file, 'rb') as f:
        try:
            response = requests.post(
                f'{nomad_url}uploads?file_name={os.path.basename(upload_file)}',
                headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'},
                data=f,
                timeout=30
            )
            response.raise_for_status()  # Explicitly check HTTP status code

            upload_id = response.json().get('upload_id')
            if upload_id:
                return upload_id, True  # Return a success flag

            print('Response is missing upload_id:', response.json())
            return None, False

        except requests.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise Exception(f"HTTP error: {http_err} - Response: {response.text}")  # Raise an exception for HTTP errors
            #return None, False

        except requests.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            raise Exception(f"Request error: {req_err}")
            #return None, False

        except Exception as e:
            print(f"Unexpected error uploading to NOMAD:\n{e}")
            raise Exception(f"Unexpected error in upload: {e}")
            #return None, False

# def check_upload_status(nomad_url, token, upload_id):
#     '''
#     # upload success => returns 'Process publish_upload completed successfully'
#     # publish success => 'Process publish_upload completed successfully'
#     '''
#     try:
#         response = requests.get(
#             nomad_url + 'uploads/' + upload_id,
#             headers={'Authorization': f'Bearer {token}'}, timeout=30)
#         status_message = response.json().get('data').get('last_status_message')
#         if status_message:
#             return status_message

#         print('response is missing status_message: ')
#         print(response.json())
#         return
#     except Exception as e:
#         print('something went wrong trying to check the status of upload' + upload_id)
#         print(e)
#         # upload gets deleted from the upload staging area once published...or in this case something went wrong
#         return
def check_upload_status(nomad_url, token, upload_id):
    '''
    Check the status of a NOMAD upload by its ID.
    Returns the status message if successful, otherwise returns None.
    '''
    try:
        response = requests.get(
            f'{nomad_url}uploads/{upload_id}',
            headers={'Authorization': f'Bearer {token}'},
            timeout=30
        )
        response.raise_for_status()  # Check if the request was successful

        status_message = response.json().get('data', {}).get('last_status_message')
        if status_message:
            return status_message, True  # Return status and success flag

        print('Response is missing status_message:', response.json())
        return None, False

    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise Exception(f"HTTP error: {http_err} - Response: {response.text}")  # Raise an exception for HTTP errors
        #return None, False

    except requests.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        raise Exception(f"Request error: {req_err}")  # Raise an exception for request errors
        #return None, False

    except Exception as e:
        print(f"Unexpected error checking upload status:\n{e}")
        raise Exception(f"Unexpected error in status check: {e}")
        #return None, False

# @delayed_call(delay_seconds=2)  # waits 2 seconds before execution  
# def wait_for_upload_completion(nomad_url, token, upload_id, interval=5, timeout=30):
#     '''
#     Waits for NOMAD upload to complete by polling every 'interval' seconds,
#     until 'timeout' seconds have passed.

#     Returns the final status message if successful, or raises TimeoutError.
#     '''
#     start_time = time.time()
#     while True:
#         try:
#             status_message = check_upload_status(nomad_url, token, upload_id)
#             if status_message is None:
#                 print('No status message returned, retrying...')
#             elif status_message == 'Process process_upload completed successfully':
#                 print('Upload completed successfully!')
#                 return status_message
#             else: 
#                 print(f"Current status: {status_message}. Waiting...")
#         except Exception as e:
#             raise

#         if time.time() - start_time > timeout:
#             raise TimeoutError("Timeout reached before upload completion.")

#         time.sleep(interval)

@delayed_call(delay_seconds=2)  # waits 2 seconds before execution  
def wait_for_upload_completion(nomad_url, token, upload_id, interval=5, timeout=50):
    '''
    Waits for NOMAD upload to complete by polling every 'interval' seconds,
    until 'timeout' seconds have passed.

    Returns the final status message if successful, or returns None if it fails.
    '''
    try:
        start_time = time.time()
        while True:
            # Check if the timeout is reached
            if time.time() - start_time > timeout:
                print("Timeout reached before upload completion.")
                return None

            # Checking upload status
            status_message, success = check_upload_status(nomad_url, token, upload_id)

            if not success:
                print("Failed to retrieve upload status. Retrying...")
                time.sleep(interval)
                continue  # Retry instead of raising an exception

            if status_message == 'Process process_upload completed successfully':
                print('Upload completed successfully!')
                return status_message  # Successfully completed
            if status_message == 'Process publish_upload completed successfully':
                print('Publish completed successfully!')
                return status_message  # Successfully completed
            # Still processing, keep waiting
            print(f"Current status: {status_message}. Waiting...")
            time.sleep(interval)
    except Exception as e:
        print(f"Unexpected error while waiting for upload completion: {e}")
        raise e

# def get_upload_entries(nomad_url, token, upload_id):
#     """
#     Fetch entries for a given NOMAD upload ID.

#     Args:
#         nomad_url (str): Base URL of the NOMAD API.
#         token (str): Bearer authentication token.
#         upload_id (str): Upload ID to fetch entries for.

#     Returns:
#         dict: JSON data of the response if successful.

#     Raises:
#         requests.HTTPError: If the HTTP request returns an unsuccessful status code.
#         requests.RequestException: For other errors in the request.
#     """
#     url = f"{nomad_url}uploads/{upload_id}/entries"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Accept": "application/json"
#     }

#     try:
#         response = requests.get(url, headers=headers, timeout=30)
#         response.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
#         data = response.json()
#         print("Successfully fetched entries")
#         #print(data)
#         return data

#     except requests.HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err} - Response: {response.text}")
#         raise

#     except requests.RequestException as err:
#         print(f"Request error occurred: {err}")
#         raise


def get_upload_entries(nomad_url, token, upload_id):
    """
    Fetch entries for a given NOMAD upload ID.

    Args:
        nomad_url (str): Base URL of the NOMAD API.
        token (str): Bearer authentication token.
        upload_id (str): Upload ID to fetch entries for.

    Returns:
        tuple: (data, success) where:
            - data (dict or None): JSON data of the response if successful.
            - success (bool): True if successful, False otherwise.
    """
    url = f"{nomad_url}uploads/{upload_id}/entries?page_size=200"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()
        if data:
            print("Successfully fetched entries, let's check for processing failures...")
            return data, True  # Success case

        print("No data returned by the request.")
        return None, False

    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise Exception(f"HTTP error: {http_err} - Response: {response.text}")  # Raise an exception for HTTP errors
        #return None, False

    except requests.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        raise Exception(f"Request error: {req_err}")
        #return None, False

    except Exception as e:
        print(f"Unexpected error fetching upload entries: {e}")
        raise Exception(f"Unexpected error in fetching entries: {e}")
        #return None, False
    

# def delete_upload(nomad_url, token, upload_id):
#     """
#     Delete a NOMAD upload given its ID.

#     Args:
#         nomad_url (str): Base URL of the NOMAD API.
#         token (str): Bearer authentication token.
#         upload_id (str): Upload ID to delete.

#     Returns:
#         dict: JSON data of the response if successful.

#     Raises:
#         requests.HTTPError: If the HTTP request returns an unsuccessful status code.
#         requests.RequestException: For other errors in the request.
#     """
#     url = f"{nomad_url}uploads/{upload_id}"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Accept": "application/json"
#     }

#     try:
#         response = requests.delete(url, headers=headers, timeout=30)
#         response.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
#         data = response.json()
#         print("Successfully deleted upload:")
#         #print(data)
#         return data

#     except requests.HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err} - Response: {response.text}")
#         raise

#     except requests.RequestException as err:
#         print(f"Request error occurred: {err}")
#         raise

def delete_upload(nomad_url, token, upload_id):
    """
    Delete a NOMAD upload given its ID.

    Args:
        nomad_url (str): Base URL of the NOMAD API.
        token (str): Bearer authentication token.
        upload_id (str): Upload ID to delete.

    Returns:
        tuple: (data, success) where:
            - data (dict or None): JSON data of the response if successful.
            - success (bool): True if successful, False otherwise.
    """
    url = f"{nomad_url}uploads/{upload_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()
        print("Successfully deleted upload.")
        return data, True

    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise Exception(f"HTTP error: {http_err} - Response: {response.text}")  # Raise an exception for HTTP errors
        #return None, False

    except requests.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        raise Exception(f"Request error: {req_err}")
        #return None, False

    except Exception as e:
        print(f"Unexpected error occurred while deleting upload: {e}")
        raise Exception(f"Unexpected error in deleting upload: {e}")
        #return None, False

def get_entry_archive(nomad_url, token, entry_id):
    """
    Fetch the full archive (including logs, warnings, errors, and parsed data)
    for a given entry ID from NOMAD.

    Args:
        nomad_url (str): Base URL of the NOMAD API (must end with '/api/v1/').
        token (str): Bearer authentication token.
        entry_id (str): The entry ID whose archive is requested.

    Returns:
        tuple: (archive_dict, success) where:
            - archive_dict (dict or None): Parsed archive data if successful.
            - success (bool): True if successful, False otherwise.
    """
    url = f"{nomad_url}entries/{entry_id}/archive"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        #print(f"GET {url} → {response.status_code}")
        response.raise_for_status()

        archive = response.json()
        return archive, True

    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise Exception(f"HTTP error: {http_err} - Response: {response.text}")  # Raise an exception for HTTP errors
    except requests.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        raise Exception(f"Request error: {req_err}")  # Raise an exception for request errors
    except Exception as e:
        print(f"Unexpected error occurred while fetching entry archive: {e}")
        raise Exception(f"Unexpected error in fetching entry archive: {e}")

    return None, False

def publish_file(nomad_url, token, upload_id, to_central_nomad=False):
    """
    Publish a NOMAD upload.

    Args:
        nomad_url (str): Base URL of the NOMAD API (must end with '/api/v1/').
        token (str): Bearer authentication token.
        upload_id (str): ID of the upload to publish.
        to_central_nomad (bool): Whether to publish to central NOMAD.

    Returns:
        tuple: (response_data, success) where:
            - response_data (dict or None): JSON response from the server.
            - success (bool): True if published successfully, False otherwise.
    """
    url = f"{nomad_url}uploads/{upload_id}/action/publish?to_central_nomad={str(to_central_nomad).lower()}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"Successfully published upload {upload_id}.")
        return response.json(), True

    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise Exception(f"HTTP error: {http_err} - Response: {response.text}")

    except requests.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        raise Exception(f"Request error: {req_err}")

    except Exception as e:
        print(f"Unexpected error publishing upload: {e}")
        raise Exception(f"Unexpected error in publish: {e}")


def upload_file(file_path = 'nomuploads/PicoTCDv3/PicoTCDv3_steps.zip', autodelete = False):
    #nomad_url = 'http://192.167.170.104:8000/fairdi/nomad/latest/api/v1/'
    nomad_url = 'http://192.167.170.104:4080/nomad-oasis/api/v1/'
    token = upload_id = None
    try:
        print('getting authentication token...')
        token, success = get_authentication_token(nomad_url)
        # if not success:
        #     print("Failed to get authentication token. Aborting upload.")
        #     return None

        print('starting upload...')
        upload_id, success = upload_to_NOMAD(nomad_url, token, file_path)
        # if not success:
        #     print("Failed to upload to NOMAD. Aborting.")
        #     return None
        print(f'UPLOAD ID: {upload_id}')

        last_status_message = wait_for_upload_completion(nomad_url, token, upload_id)
        if last_status_message is None:
            print("Upload process did not complete successfully. Aborting.")
            return None
        print(last_status_message)

        data, success = get_upload_entries(nomad_url, token, upload_id)
        if not success or data is None:
            print("Failed to fetch entries. Aborting.")
            return None
        print('Fetching entries...')
        my_entries = {}
        logs = []
        for entry in data.get('data', []):
            entry_id = entry.get('entry_id')
            filename = entry.get('mainfile')
            if entry_id and filename:
                my_entries[filename] = entry_id
            log, ok = get_entry_archive(nomad_url, token, entry_id)
            if ok:
                logs.append(log)
        my_entries = {upload_id : my_entries}
        print('Entries fetched successfully:')
        print(f"Entry processing failed: {(fails := data['processing_failed'])}")
        if fails == 0:
            print('starting publish procedure...')
            publish_response, success = publish_file(nomad_url, token, upload_id)
            last_status_message = wait_for_upload_completion(nomad_url, token, upload_id)
            if last_status_message is None:
                print("Upload process did not complete successfully. Aborting.")
                return None
            print(last_status_message)
            
            return my_entries  # Successfully fetched entries

        # Something went wrong with processing, return None
        err_msg = f""
        for i, entry in enumerate(logs):
            if not entry["data"]["archive"]["metadata"]["processed"]: # false if parsing err
                generic_err = entry["data"]["archive"]["processing_logs"][1]["errors"]
                specific_err = entry["data"]["archive"]["processing_logs"][1]["error"]
                filename = entry["data"]["archive"]["metadata"]["mainfile"]

                err_msg += f"File: {filename}\nGeneric error: {generic_err}\nSpecific error: {specific_err}\n\n"
        print(err_msg)
        raise Exception(f"SOME ENTRIES HAVE BUGS!\n Processing failed for {fails} entries. Check the logs for details:\n{err_msg}")
    except Exception as e:
        # If autodelete is enabled, attempt to delete the upload
        if autodelete and upload_id and token:
            print('\nDeleting upload due to processing failures...')
            del_log, success = delete_upload(nomad_url, token, upload_id)
            # if not success:
            #     print("Failed to delete the upload. Check the server logs.")

        print(f"Rilancio l'eccezione: ")
        raise        


if __name__ == '__main__': 
    # if upload_steps succeded, go on with other publish, else exit the function
    #if (upload_dict:=upload_file('nomuploads/isopillar/isopillar_steps.zip')) is None:
    if (upload_dict:=upload_file('bestmesa.zip')) is None:
        print('Some entries have bugs.\n')
        print('retry with a well formatted file.\n')
        #return
    # write the json dict in a file in the process_path with pathlib,
    # translate the dict entries in the step list of the father, RENAMEM OUTPUT LIST WITH THE RIGHT NAME
""" output_list = [
        f"../uploads/{upload_id}/archive/{entry_id}#data"
        for upload_id, entries in upload_dict.items()
        for entry_id in entries.values()
]"""
    

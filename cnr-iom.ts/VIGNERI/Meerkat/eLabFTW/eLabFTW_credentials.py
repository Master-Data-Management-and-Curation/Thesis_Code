from eLabFTW import eLabFTW_APIs

# Insert here your credentials to access eLabFTW
# base_url: The base URL of the ElabFTW instance.
# api_key: Your eLabFTW API key for authentication, r/w permission is required

base_url = 'The base URL of the ElabFTW instance'
api_key = ('Your eLabFTW API key for authentication, r/w permission is required') 

elabftw_api = eLabFTW_APIs.ElabFTWAPI(base_url,api_key)
This repo contains the code written during the MDMC internship.

official.py contains the program used to compile and modify json files in a user friendly way.
It is also the only python file that may run standalone, since all of the following are part of a greater ecosystem, and are here only for sharing purposes.

cams2nomad.py is the the dictionary containing the mapping between the CAMS parameters and the NOMAD keys. It facilitates the name conversion, and keeps the logic code clean.

BUTTON_UPLOAD_FAIR.py contains the functions in the backend of CAMS, the CNR-ISMN's LIMS that make possible to extract all the data froma a process and send it to NOMAD. 

API_collection.py gathers a series of function for the real upload of a file to NOMAD. It manages data exchanging between a client and the NOMAD server, exploiting its APIs.

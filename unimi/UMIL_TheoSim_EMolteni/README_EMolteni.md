This repo contains the contributions related to E. Molteni's MDMC internship work 
on adding functionalities to some NOMAD parsers for electronic structure codes.

In particular:

parser.py (from https://github.com/emolteni/electronic-parsers/tree/develop/electronicparsers/yambo): 
modified NOMAD Yambo parser where I have fixed an issue about a mismatch between 
total number of coordinates and total number of atoms.

/CH4_db_minimal (from https://github.com/emolteni/electronic-parsers/tree/develop/tests/data/yambo): 
test folder for the NOMAD electronic-parsers/test/data/yambo folder, 
for the above-mentioned implementation regarding atom coordinates

test_yamboparser.py (from https://github.com/emolteni/electronic-parsers/tree/develop/tests):
file for running all the NOMAD yambo tests present in https://github.com/emolteni/electronic-parsers/tree/develop/tests/data/yambo,
where I have added the part regarding our test folder /CH4_db_minimal


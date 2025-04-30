This repo contains the contributions related to E. Molteni's MDMC internship work 
on adding functionalities to some NOMAD parsers for electronic structure codes.

In particular:

# /Yambo_atom_coords: Fixing NOMAD issues in the parsing and writing/displaying of chemical composition, 
# atom coordinates, simulation cell

New information, pointing to the need of having a ns.db file within a /SAVE subfolder 
in Yambo uploads in order for NOMAD to be able to parse and display chemical composition, atom coordinates, simulation cell:
a) NOMAD GitHub, in the Issues section for electronic-parsers: https://github.com/nomad-coe/electronic-parsers/issues:
  Issues: "Add warning to yambo parser when ns.db file is not present", "Add search for ns.db file in Yambo when not in default folder"
b) my detailed Discord thread on this subject, to which (a) is pointing: https://discord.com/channels/1201445470485106719/1208029192881442866/threads/1351201658440519761

parser.py (from https://github.com/emolteni/electronic-parsers/tree/develop/electronicparsers/yambo): 
modified NOMAD Yambo parser where I have fixed an issue about a mismatch between 
total number of coordinates and total number of atoms, due to NOMAD incorrectly using the Yambo 
max_n_atoms variable (maximum of the numbers of atoms of all the chemical species present in the system)
instead of the n_atoms one (actual number of atoms of a given chemical species) for allocating
the number of lines for the atom coordinates of each chemical species

/CH4_db_minimal (from https://github.com/emolteni/electronic-parsers/tree/develop/tests/data/yambo): 
test folder for the NOMAD electronic-parsers/test/data/yambo folder, 
for the above-mentioned implementation regarding atom coordinates

test_yamboparser.py (from https://github.com/emolteni/electronic-parsers/tree/develop/tests):
file for running all the NOMAD yambo tests present in https://github.com/emolteni/electronic-parsers/tree/develop/tests/data/yambo,
where I have added the part regarding our test folder /CH4_db_minimal


# /Yambo_spectra: adding spectra parsing functionality in the NOMAD Yambo parser 

Spectra_plotting_EMvers_forgithubrepo.ipynb: our local parser for Yambo spectra only.
This version works on jupyterlab;  the corresponding adapted version does not work yet in our Oasis 

o-R_methylox_TDLDA.alpha_q1_slepc_alda_bse: Yambo spectrum file to be parsed




This repo contains the contributions related to E. Molteni's MDMC internship work 
on adding functionalities to some NOMAD parsers for electronic structure codes.

In particular:

# /Yambo_atom_coords: Fixing NOMAD issues in the parsing and writing/displaying of chemical composition, 
# atom coordinates, simulation cell

For this implementation, we have made a Pull Request on the NOMAD github repo:
https://github.com/nomad-coe/electronic-parsers/pull/286

* New information, added by the FAIRmat team after our pointing out this issue, related to the need of having a ns.db file within a /SAVE subfolder 
in Yambo uploads in order for NOMAD to be able to parse and display chemical composition, atom coordinates, simulation cell:
a) NOMAD GitHub, in the Issues section for electronic-parsers: https://github.com/nomad-coe/electronic-parsers/issues:
  Issues: "Add warning to yambo parser when ns.db file is not present", "Add search for ns.db file in Yambo when not in default folder"
b) my detailed Discord thread on this subject, to which (a) is pointing: https://discord.com/channels/1201445470485106719/1208029192881442866/threads/1351201658440519761

* parser.py (from https://github.com/emolteni/electronic-parsers/tree/develop/electronicparsers/yambo): 
modified NOMAD Yambo parser where I have fixed an issue about a mismatch between 
total number of coordinates and total number of atoms, due to NOMAD incorrectly using the Yambo 
max_n_atoms variable (maximum of the numbers of atoms of all the chemical species present in the system)
instead of the n_atoms one (actual number of atoms of a given chemical species) for allocating
the number of lines for the atom coordinates of each chemical species

* /CH4_db_minimal (from https://github.com/emolteni/electronic-parsers/tree/develop/tests/data/yambo): 
"minimal" test folder (containing also a ns.db file within a /SAVE subfolder) for the NOMAD electronic-parsers/test/data/yambo folder, 
for the above-mentioned implementation regarding atom coordinates; r_setup is the yambo mainfile.

* test_yamboparser.py (from https://github.com/emolteni/electronic-parsers/tree/develop/tests):
file for running all the NOMAD yambo tests present in https://github.com/emolteni/electronic-parsers/tree/develop/tests/data/yambo,
where I have added the part (test_5) regarding our test folder /CH4_db_minimal


# /Yambo_spectra: adding spectra parsing (and plotting) functionality in the NOMAD Yambo parser 

* Spectra_plotting_EMvers_forgithubrepo.ipynb: our local parser for Yambo spectra only.
Allows for yambo spectra files as o* files with either 3 or 5 columns of data,
using a regular expression such as to match the various possible formats of spectra headers, i.e.:
E/ev[1]            ALPHA-Im[2]        ALPHA-Re[3]        (ALPHAo-Im[4]       ALPHAo-Re[5])
or
E/ev[1]            EPS-Im[2]          EPS-Re[3]          (EPS-Im[4]          EPS-Re[5])
where I have indicated with (.....)  those columns which are not always present.

The columns to be plotted are the first (column 0 according to python, excitation energies) 
and the second (column 1 according to python,  intensities).
This version works on jupyterlab;  the corresponding adapted version does not work yet in our Oasis 
(no warning, no error messages, yet no spectra plotted), possibly due to issues on which subparser to use
in order to parse the correct file, which is a o* file, not a r* mainfile.
The fact that our local version of the parser works should ensure that the part about 
matching the specific formats of the headers and columns of data in the file are correct. 

* o-R_methylox_TDLDA.alpha_q1_slepc_alda_bse: test Yambo spectrum file to be parsed


# /Siesta_DOS: adding electronic Density of States (DOS) parsing (and plotting) functionality in the NOMAD Siesta parser 
This implementation already works on our Oasis; we have not made a Pull Request yet on the NOMAD github repo,
since we are planning to implement the plotting of Siesta band structures too.

* parser.py:  modified NOMAD Siesta parser, implementing the parsing of DOS outputs

* /Siesta_DOS_bands_data: test folder with a Siesta DOS + band structure run:
  siesta.out is the Siesta mainfile;  dos is the DOS file.
  As explained in my thesis, with our parser the DOS parsing and plotting is working, although
  not being yet able to find the Fermi energy value.
  We are using a folder with band structure data also (which currently are not plotted),
  mainly in view of using it later to test our planned implementation of band structure parsing too. 






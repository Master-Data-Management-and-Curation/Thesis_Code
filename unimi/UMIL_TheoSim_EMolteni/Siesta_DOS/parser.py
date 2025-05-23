#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD.
# See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import logging
import numpy as np
from datetime import datetime

from nomad.units import ureg
from nomad.parsing.file_parser import TextParser, Quantity
from runschema.run import Run, Program, TimeRun
from runschema.method import (
    Method,
    DFT,
    XCFunctional,
    Functional,
    BasisSet,
    BasisSetContainer,
    Electronic,
)
from runschema.system import System, Atoms
from runschema.calculation import (
    Calculation,
    Energy,
    EnergyEntry,
    ScfIteration,
    Forces,
    ForcesEntry,
    Stress,
    StressEntry,
    Multipoles,
    MultipolesEntry,
    Charges,
    ChargesValue,
    Dos,
    DosValues,
)
from simulationworkflowschema import GeometryOptimization, SinglePoint


re_n = r'[\n\r]'
re_f = r'[-+]?\d+\.\d*(?:[DdEe][-+]\d+)?'


class FDFParser(TextParser):
    def init_quantities(self):
        def to_parameter(val_in):
            key, val = val_in.strip().split(' ', 1)
            if val[0].isdecimal() or val[0] == '-':
                val = val.split()[0]
            elif val.lower() in ['true', 'false']:
                val = val == 'true'
            return [key, val]

        def to_block(val_in):
            key, val = val_in.strip().split(' ', 1)
            return [key, [v.strip().split() for v in val.strip().splitlines()]]

        self._quantities = [
            Quantity(
                'parameter',
                rf'([A-Za-z][\w\.]+) +([ \w\.\/]+?)(?:\#|{re_n})',
                repeats=True,
                str_operation=to_parameter,
            ),
            Quantity(
                'block',
                rf'\%block ([A-Za-z][\w\.]+)\s+([\s\S]+?)\%endblock',
                repeats=True,
                str_operation=to_block,
            ),
        ]

    def parse(self, key=None):
        super().parse(key)

        # add atoms info
        species, coordinates, lattice_vectors = None, None, None
        parameters = {key: val for key, val in self._results.get('parameter', [])}
        self._results['parameters'] = parameters

        # scaling of the lattice vectors
        lattice_constant = parameters.get('LatticeConstant', 1.0) * ureg.angstrom
        #units of the atomic coordinates
        coordinates_format = parameters.get('AtomicCoordinatesFormat')

        for block in self._results.get('block', []):
            if block[0] == 'ChemicalSpeciesLabel':
                species = [b[2] for b in block[1]]
            elif block[0] == 'LatticeVectors':
                lattice_vectors = block[1] * lattice_constant
            elif block[0] == 'AtomicCoordinatesAndAtomicSpecies':
                coordinates = np.array([b[0:3] for b in block[1]], dtype=np.float64)

        self._results['positions'] = coordinates
        self._results['labels'] = species
        self._results['lattice_vectors'] = lattice_vectors
        self._results['coordinates_format'] = coordinates_format


class OutParser(TextParser):
    def init_quantities(self):
        def to_stress_tensor(val_in):
            val = val_in.strip().split()
            stress = np.zeros((3, 3))
            stress[0][0] = val[0]
            stress[1][1] = val[1]
            stress[2][2] = val[2]
            stress[0][1] = stress[1][0] = val[3]
            stress[1][2] = stress[2][1] = val[4]
            stress[0][2] = stress[2][0] = val[5]
            return stress * ureg.kbar

        def extract_xc_check_from_output(text):
            import re
            matches = re.findall(r'xc_check:\s+(?:GGA|LDA)?\s*(\w+)', text)
            if len(matches) >= 2:
                return matches[1].lower()
            return None

        calc_quantities = [
            Quantity(
                'x_siesta_number_of_atoms',
                r'initatomlists:\s+Number of atoms, orbitals, and projectors:\s+(\d+)',
                dtype=np.int32,
            ),
            Quantity(
                'nspin',
                r'Number of spin components\s*=\s*(\d+)',
                dtype=int
            ),
            Quantity(
                'lattice_vectors',
                r'outcell\: Unit cell vectors \(Ang\)\:\s+([\s\d\.\-]+)',
                shape=(3, 3),
                dtype=np.dtype(np.float64),
                unit=ureg.angstrom,
            ),

            Quantity(
                'atoms',
                r'outcoor: Atomic coordinates(.+[\s\w\.\-]+)',
                sub_parser=TextParser(
                    quantities=[
                        Quantity('coordinates_format', r'\((\S+)\)', dtype=str),
                        Quantity('labels', r' +([A-Z][a-z]*)', repeats=True, dtype=str),
                        Quantity(
                            'positions',
                            rf'({re_f} +{re_f} +{re_f})',
                            repeats=True,
                            dtype=np.dtype(np.float64),
                        ),
                    ]
                ),
            ),
            Quantity(
                'energy',
                rf'Program\'s energy decomposition \(eV\)\:([\s\S]+?){re_n} *{re_n}',
                sub_parser=TextParser(
                    quantities=[
                        Quantity(
                            'contribution',
                            rf'siesta\: +(\S+) *= *({re_f})',
                            repeats=True,
                        )
                    ]
                ),
            ),
            Quantity(
                'scf',
                rf'scf\: iscf +Eharris\(eV\).+([\s\S]+?){re_n} *{re_n}',
                sub_parser=TextParser(
                    quantities=[
                        Quantity(
                            'step',
                            rf'scf\: +\d+ +({re_f} +{re_f} +{re_f} +{re_f} +{re_f})',
                            repeats=True,
                            dtype=np.dtype(np.float64),
                        )
                    ]
                ),
            ),
            Quantity(
                'energy_total',
                rf'siesta\: E_KS\(eV\) = +({re_f})',
                dtype=np.float64,
                unit=ureg.eV,
            ),
            Quantity(
                'energy',
                rf'Final energy \(eV\)\:([\s\S]+?Total.+)',
                sub_parser=TextParser(
                    quantities=[
                        Quantity(
                            'contribution',
                            rf'siesta: +([ \w\.\-]+?) *= *({re_f})',
                            repeats=True,
                            str_operation=lambda x: [
                                v.strip() for v in x.rsplit(' ', 1)
                            ],
                        )
                    ]
                ),
            ),
            Quantity(
                'forces',
                r'siesta\: Atomic forces \(eV/Ang\)\:([\s\S]+?Tot.+)',
                sub_parser=TextParser(
                    quantities=[
                        Quantity(
                            'atomic',
                            rf'\d+ +({re_f} +{re_f} +{re_f})',
                            repeats=True,
                            dtype=np.dtype(np.float64),
                        )
                    ]
                ),
            ),
            Quantity(
                'fermi_energy',
                r'siesta:\s*Fermi\s*=\s*(-?\d+\.\d+)',
                dtype=np.float64,
            ),

            Quantity(
                'stress_tensor',
                rf'Stress\-tensor\-Voigt \(kbar\)\: +({re_f} +{re_f} +{re_f} +{re_f} +{re_f} +{re_f})',
                str_operation=to_stress_tensor,
            ),
            Quantity(
                'stress_tensor',
                rf'Stress tensor \(static\) \(eV/Ang\*\*3\)\:([\s\S]+?){re_n} *{re_n}',
                str_operation=lambda x: [
                    v.strip().split()[1:4] for v in x.strip().splitlines()
                ],
                dtype=np.dtype(np.float64),
                unit=ureg.eV / ureg.angstrom**3,
            ),
            Quantity(
                'electric_dipole',
                rf'Electric dipole \(Debye\) += +({re_f} +{re_f} +{re_f})',
                dtype=np.dtype(np.float64),
            ),
            Quantity(
                'mulliken',
                r'mulliken\: Atomic and Orbital Populations\:([\s\S]+?)siesta\:',
                sub_parser=TextParser(
                    quantities=[
                        Quantity(
                            'atom',
                            rf'(Species\:[\s\S]+?){re_n} *{re_n}',
                            repeats=True,
                            sub_parser=TextParser(
                                quantities=[
                                    Quantity('label', r'Species\: *(\S+)', dtype=str),
                                    Quantity(
                                        'orbital',
                                        r'(\d[spdSPD]\S*) ',
                                        dtype=str,
                                        repeats=True,
                                    ),
                                    Quantity(
                                        'values',
                                        rf'(\d+ +{re_f} +{re_f}[\d\.\-\s]+)',
                                        dtype=np.dtype(np.float64),
                                    ),
                                ]
                            ),
                        ),
                        Quantity('spin', r'(Spin DOWN)', str_operation=lambda x: 2),
                        Quantity(
                            'q_tot',
                            rf'Qtot = +({re_f})',
                            repeats=True,
                            dtype=np.float64,
                        ),
                    ]
                ),
            ),
        ]

        self._quantities = [
            Quantity(
                'header',
                r'(S[\s\S]+?)\*',
                sub_parser=TextParser(
                    quantities=[
                        Quantity(
                            'program_version',
                            r'(?:SIESTA|Siesta Version:) *(.+)',
                            flatten=False,
                            dtype=str,
                        ),
                        Quantity(
                            'x_siesta_arch',
                            r'Architecture *: +(.+)',
                            flatten=False,
                            dtype=str,
                        ),
                        Quantity(
                            'x_siesta_compiler_flags',
                            r'Compiler flags *: +(.+)',
                            flatten=False,
                            dtype=str,
                        ),
                        Quantity(
                            'x_siesta_parallel',
                            r'(PARALLEL) version',
                            str_operation=lambda x: True,
                        ),
                    ]
                ),
            ),
            Quantity(
                'input_data_file',
                r'(Dump of input data file.+[\s\S]+?End of input data file)',
                flatten=False,
                dtype=str,
            ),
            Quantity(
                'simulation_parameters',
                r'Simulation parameters.+([\s\S]+?)\*{10}',
                sub_parser=TextParser(
                    quantities=[
                        Quantity(
                            'redata',
                            r'redata\: (.+?= +\S+)',
                            str_operation=lambda x: [v.strip() for v in x.rsplit('=')],
                            repeats=True,
                        )
                    ]
                ),
            ),
            Quantity('x_siesta_n_nodes', r'Running on +(\d+) nodes', dtype=np.int32),
            Quantity(
                'run_start',
                r'Start of run: +(\d+-[A-Z]+-\d+) +(\d+:\d+:\d+)',
                flatten=False,
                dtype=str,
            ),
            Quantity(
                'run_end',
                r'End of run: +(\d+-[A-Z]+-\d+) +(\d+:\d+:\d+)',
                flatten=False,
                dtype=str,
            ),
            Quantity(
                'single_point',
                r'(Single\-point calculation[\s\S]+?Target enthalpy.+)',
                sub_parser=TextParser(quantities=calc_quantities),
            ),
            Quantity(
                'geometry_optimization',
                r'\={5}\s+(Begin[\s\S]+?)outcoor\: Re',
                sub_parser=TextParser(
                    quantities=[
                        Quantity(
                            'step',
                            r'(Begin.+?opt\. move += +\d+[\s\S]+?Target enthalpy.+)',
                            repeats=True,
                            sub_parser=TextParser(quantities=calc_quantities),
                        )
                    ]
                ),
            ),
        ] + calc_quantities


class SiestaParser:
    def __init__(self):
        self.out_parser = OutParser()
        self.fdf_parser = FDFParser()
        self._xc_map = {
            'ca': ('LDA_X', 'LDA_C_PZ'),
            'pz': ('LDA_X', 'LDA_C_PZ'),
            'pw92': ('LDA_X', 'LDA_C_PW'),
            # TODO 'PW91': '',
            'pbe': ('GGA_X_PBE', 'GGA_C_PBE'),
            'revpbe': ('GGA_X_PBE_R', 'GGA_C_PBE'),
            'rpbe': ('GGA_X_RPBE', 'GGA_C_PBE'),
            # TODO 'WC': ('GGA_X_WC', ),
            'am05': ('GGA_X_AM05', 'GGA_C_AM05'),
            'pbesol': ('GGA_X_PBE_SOL', 'GGA_C_PBE_SOL'),
            'blyp': ('GGA_X_B88', 'GGA_C_LYP'),
            'df1': ('gga_x_pbe_r', 'vdw_c_df1'),
            'drsll': ('gga_x_pbe_r', 'vdw_c_df1'),
            'lmkll': ('gga_x_rpw86', 'vdw_c_df2'),
            'df2': ('gga_x_rpw86', 'vdw_c_df2'),
            'kbm': ('GGA_X_OPTB88_VDW', 'vdw_c_df1'),
            'c09': ('GGA_X_C09X', 'vdw_c_df1'),
            'bh': ('GGA_X_LV_RPW86', 'vdw_c_df1'),
        }
        self._metainfo_map = {
            'Etot': 'total',
            'FreeEng': 'free',
            'Exc': 'xc',
            'Hartree': 'electrostatic',
            'Exch.-corr.': 'xc',
            'Ion-ion': 'nuclear_repulsion',
            'Total': 'total',
        }
    
    def init_parser(self):
        self.out_parser.mainfile = self.filepath
        self.out_parser.logger = self.logger
        self.fdf_parser.logger = self.logger
        self._files = os.listdir(self.maindir)

    def parse(self, filepath, archive, logger):
        self.filepath = os.path.abspath(filepath)
        self.archive = archive
        self.logger = logging.getLogger(__name__) if logger is None else logger
        self.maindir = os.path.dirname(self.filepath)
        self.init_parser()

        sec_run = Run()
        archive.run.append(sec_run)
        header = self.out_parser.get('header')
        if header is not None:
            sec_run.program = Program(name='Siesta', version=header.program_version)
            for key, val in header.items():
                if key.startswith('x_siesta'):
                    setattr(sec_run, key, val)

        for key, val in self.out_parser.items():
            if key.startswith('x_siesta'):
                setattr(sec_run, key, val)

        def get_date(time):
            if time is None:
                return
            return datetime.strptime(time, '%d-%b-%Y %H:%M:%S').timestamp()

        sec_run.time_run = TimeRun(
            date_start=get_date(self.out_parser.run_start),
            date_end=get_date(self.out_parser.run_end),
        )

        # input parameters from data file
        self.fdf_parser.mainfile = self.out_parser.mainfile
        if self.out_parser.input_data_file is not None:
            self.fdf_parser._file_handler = self.out_parser.input_data_file.encode()

        sec_method = Method()
        sec_run.method.append(sec_method)
        parameters = {}
        parameters = self.fdf_parser.get('parameters')
        sec_method.x_siesta_input_parameters = parameters
        sec_method.x_siesta_simulation_parameters = {
            key: val
            for key, val in self.out_parser.get('simulation_parameters', {}).get(
                'redata', []
            )
        }

        sec_method.dft = DFT(xc_functional=XCFunctional())
        parameters = parameters or {}

        xc_label = parameters.get('xc.authors') or parameters.get('xc_check')

        if not xc_label:
            try:
                with open(self.out_parser.mainfile, 'r') as f:
                    content = f.read()
                    import re
                    matches = re.findall(r'xc_check:\s+(?:GGA|LDA)?\s*(\w+)', content)
                    if len(matches) >= 2:
                        xc_label = matches[1].lower()
            except Exception as e:
                self.logger.warning(f"Could not extract xc_label from output file: {e}")


        if xc_label:
            for xc_functional in self._xc_map.get(xc_label.lower(), []):
                if '_X_' in xc_functional:
                    sec_method.dft.xc_functional.exchange.append(Functional(name=xc_functional))
                elif '_C_' in xc_functional:
                    sec_method.dft.xc_functional.correlation.append(Functional(name=xc_functional))
                elif '_HYB_' in xc_functional:
                    sec_method.dft.xc_functional.hybrid.append(Functional(name=xc_functional))
                else:
                    sec_method.dft.xc_functional.contributions.append(Functional(name=xc_functional))
        else:
            self.logger.warning("Could not find any XC functional label in FDF or output.")



        sec_method.electrons_representation = [
            BasisSetContainer(
                type='atom-centered orbitals',
                scope=['wavefunction'],
                basis_set=[
                    BasisSet(
                        type='numeric AOs',
                        scope=['full-election'],
                    )
                ],
            )
        ]
       
        def parse_system(source):
            sec_system = System()
            sec_run.system.append(sec_system)
            lattice_vectors = source.get('lattice_vectors')
            atoms = source.get('atoms')
            source = atoms if atoms is not None else source
            positions = source.get('positions')
            if positions is not None:
                coordinates_format = source.get('coordinates_format', 'Ang').lower()
                if coordinates_format == 'ang':
                    positions = positions * ureg.angstrom
                elif coordinates_format in ['fractional', 'scaledcartesian']:
                    if lattice_vectors is not None:
                        positions = np.dot(
                            positions, lattice_vectors.magnitude
                        ) * lattice_vectors.units
            labels = source.get('labels')
            if not labels and self.out_parser.get('x_siesta_number_of_atoms'):
                n_atoms = self.out_parser.get('x_siesta_number_of_atoms')
                labels = ['X'] * n_atoms
                positions = [[0.0, 0.0, 0.0]] * n_atoms

            sec_system.atoms = Atoms(
                positions=positions,
                labels=source.get('labels'),
                lattice_vectors=lattice_vectors,
            )
            sec_system.is_representative = True
            return sec_system

        def parse_calculation(source):
            sec_calc = Calculation()
            sec_run.calculation.append(sec_calc)
            sec_system = parse_system(source)
            sec_run.calculation[-1]
            nspin = self.out_parser.get('nspin', 1)
            print("Found spin channels:", nspin)
            fermi = self.out_parser.get('fermi_energy')
            print("DEBUG - Fermi parsed from output:", fermi)

            if not sec_system.atoms and self.out_parser.get('x_siesta_number_of_atoms'):
                n_atoms = self.out_parser.get('x_siesta_number_of_atoms')
                sec_system.atoms = Atoms(
                    labels=['X'] * n_atoms,
                    positions=[[0.0, 0.0, 0.0]] * n_atoms
                )

            sec_calc.system_ref = sec_system

            dos = Dos()
           
            if nspin == 2:
                dos.spin_polarized = True
                dos_path = os.path.join(self.maindir, "dos")
                if os.path.exists(dos_path):
                    try:
                        data = np.loadtxt(dos_path)
                    except Exception as e:
                        self.logger.warning(f"Could not read DOS file: {e}")
                        return
                    if data.shape[1] < 4:
                        self.logger.warning(f"DOS file {dos_file} does not have 4 columns as expected.")
                        return

                    energies = data[:, 0]
                    dos_up = data[:, 1]
                    dos_down = data[:, 2]
                    dos_total = data[:, 3]

                    # spin-up
                    sec_dos_up = Dos()
                    sec_dos_up.spin_channel = 0
                    sec_dos_up.energies = energies * ureg.eV
                    sec_dos_val_up = DosValues(value=dos_up / ureg.eV)
                    sec_dos_up.total = [sec_dos_val_up]
                    sec_run.calculation[-1].dos_electronic.append(sec_dos_up)

                    # spin-down
                    sec_dos_down = Dos()
                    sec_dos_down.spin_channel = 1
                    sec_dos_down.energies = energies * ureg.eV
                    sec_dos_val_down = DosValues(value=dos_down / ureg.eV)
                    sec_dos_down.total = [sec_dos_val_down]
                    sec_run.calculation[-1].dos_electronic.append(sec_dos_down)

                    #  total
                    sec_dos_total = Dos()
                    sec_dos_total.energies = energies * ureg.eV
                    sec_dos_val_total = DosValues(value=dos_total / ureg.eV)
                    sec_dos_total.total = [sec_dos_val_total]
                    sec_run.calculation[-1].dos_electronic.append(sec_dos_total)

            elif nspin == 1:
                dos_path = os.path.join(self.maindir, "dos")
                if os.path.exists(dos_path):
                    try:
                        data = np.loadtxt(dos_path)
                    except Exception as e:
                        self.logger.warning(f"Could not read DOS file: {e}")
                        return

                    if data.shape[1] < 2:
                        self.logger.warning("DOS file does not have at least 2 columns (energy, total)")
                        return

                    energies = data[:, 0]
                    dos_total = data[:, 1]

                    sec_dos_total = Dos()
                    sec_dos_total.energies = energies * ureg.eV
                    sec_dos_total.spin_polarized = False
                    sec_dos_val_total = DosValues(value=dos_total / ureg.eV)
                    sec_dos_total.total = [sec_dos_val_total]

                    sec_run.calculation[-1].dos_electronic = [sec_dos_total]


            
            # energy
            sec_energy = Energy()
            sec_calc.energy = sec_energy
            for key, val in source.get('energy', {}).get('contribution', []):
                if key in self._metainfo_map:
                    setattr(
                        sec_energy,
                        self._metainfo_map[key],
                        EnergyEntry(value=val * ureg.eV),
                    )
                else:
                    sec_energy.contributions.append(
                        EnergyEntry(kind=key, value=val * ureg.eV)
                    )
            if source.energy_total is not None:
                sec_energy.total = EnergyEntry(value=source.energy_total)

            # forces
            if source.forces is not None and source.forces.atomic is not None:
                sec_calc.forces = Forces(
                    total=ForcesEntry(
                        value=source.forces.atomic * ureg.eV / ureg.angstrom
                    )
                )

            # stress tensor
            if source.stress_tensor is not None:
                sec_calc.stress = Stress(total=StressEntry(value=source.stress_tensor))

            # dipoles
            if source.electric_dipole is not None:
                sec_multipoles = Multipoles()
                sec_calc.multipoles.append(sec_multipoles)
                sec_multipoles.kind = 'electric'
                sec_multipoles.dipole = MultipolesEntry(total=source.electric_dipole)

            # multipoles
            if not sec_system.atoms and self.out_parser.get('x_siesta_number_of_atoms'):
                n_atoms = self.out_parser.get('x_siesta_number_of_atoms')
                sec_system.atoms = Atoms(
                labels=['X'] * n_atoms,
                positions=[[0.0, 0.0, 0.0]] * n_atoms 
            )
                for atom_n, atom in enumerate(atoms):
                    spin_n = atom_n // n_atoms
                    for orb_n, orb in enumerate(atom.get('orbital', [])):
                        # TODO map orb to lm value
                        sec_charges.orbital_projected.append(
                            ChargesValue(
                                spin=spin_n,
                                atom_label=atom.label,
                                orbital=orb,
                                value=atom.values[orb_n + 2]
                                * ureg.elementary_charge,  # 0: index 1: sum
                            )
                        )

                    if spin == 2:
                        dos.spin_polarized = True
                        # spin peojected
                        sec_charges.spin_projected.append(
                            ChargesValue(
                                spin=spin_n,
                                atom_label=atom.label,
                                value=atom.values[1] * ureg.elementary_charge,
                            )
                        )
                    value[atom_n % n_atoms] += atom.values[1]

                sec_charges.analysis_method = 'Mulliken'
                sec_charges.value = value * ureg.elementary_charge
                sec_charges.total = (
                    sum(source.mulliken.get('qtot', [])) * ureg.elementary_charge
                )

            # TODO parse more properties
            # scf stweps
            for step in source.get('scf', {}).get('step', []):
                sec_scf = ScfIteration()
                sec_calc.scf_iteration.append(sec_scf)
                sec_scf.energy = Energy(
                    total=EnergyEntry(value=step[1] * ureg.eV),
                    fermi=step[4] * ureg.eV,
                    free=EnergyEntry(value=step[2] * ureg.eV),
                )
                sec_scf.energy.types.append(
                    EnergyEntry(kind='Harris', value=step[0] * ureg.eV)
                )

            return sec_calc

        def parse_configurations(source):
            system = parse_system(source)
            calc = parse_calculation(source)
            calc.system_ref = system

        if self.out_parser.single_point is not None:
            parse_configurations(self.out_parser.single_point)
            archive.workflow2 = SinglePoint()

        if self.out_parser.geometry_optimization is not None:
            for step in self.out_parser.geometry_optimization.get('step', []):
                parse_configurations(step)
            archive.workflow2 = GeometryOptimization()

        # final properties
        calc = parse_calculation(self.out_parser)
        calc.system_ref = sec_run.system[-1]

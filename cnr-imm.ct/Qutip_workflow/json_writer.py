'''
Copyright 2025 Castorina Giovanni

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import json
import numpy as np
import qutip as qt
import os
from datetime import datetime

# --- Function for Qobj Conversion ---
def _qobj_to_quantum_object_dict(qobj):
    """
    Converts a QuTiP Qobj to a dictionary matching the QuantumObject schema section.
    Returns properties dict and matrix dict separately.
    """
    if not isinstance(qobj, qt.Qobj):
        print(f"Warning: Input is not a QuTiP Qobj. Type: {type(qobj)}")

        return {"error": "Input must be a QuTiP Qobj"}, None
    try:
        data_full = qobj.full()
        dims_list = [[int(d) for d in sublist] for sublist in qobj.dims]
        shape_list = [int(s) for s in qobj.shape]
        obj_type = qobj.type

        matrix_dict = None
        if isinstance(data_full, np.ndarray):
            # Consistent indentation
            real_part = np.real(data_full).tolist()
            imag_part = np.imag(data_full).tolist()
            matrix_dict = {
                "re": real_part,
                "im": imag_part
            }



        quantum_object_base = {
            "dims": dims_list,
            "shape": shape_list,
            "type": obj_type,
            "is_hermitian": bool(qobj.isherm),
            "storage_format": "Dense",
        }



        return quantum_object_base, matrix_dict

    except Exception as e:
        print(f"Warning: Could not process Qobj: {e}")

        return {"error": f"Failed to serialize Qobj: {e}"}, None

# --- Formatting Functions ---

def format_program_info(name="QuTiP", version=None):
    """Formats program information."""
    if version is None:
        try:
            version = qt.__version__
        except AttributeError:
            version = "unknown"
    return {"name": str(name), "version": str(version)}

def format_system_info(name="Quantum System", num_qubits=None):
    """Formats system information."""
    system_dict = {"name": str(name)}
    if num_qubits is not None:
        system_dict["num_qubits"] = int(num_qubits)
    return system_dict

def format_hamiltonian_parameters(params_dict):
    """
    Formats Hamiltonian parameters from a dictionary.
    """
    params_list = []
    for key, value_unit_tuple in params_dict.items():
        if isinstance(value_unit_tuple, (tuple, list)) and len(value_unit_tuple) == 2:
            value, unit = value_unit_tuple
        else: # Assume value only, no unit
             value = value_unit_tuple
             unit = None

        if value is not None:
            param_entry = {
                "name": str(key),
                "value": float(value)
            }
            if unit:
                param_entry["unit"] = str(unit)
            params_list.append(param_entry)
        else:
             print(f"Warning: Skipping parameter '{key}' with None value.")
    return params_list

def format_spin_hamiltonian(name, formula, parameters_list):
    """Formats the SpinHamiltonian section."""
    return {
        "name": str(name),
        "formula": str(formula),
        "parameters": parameters_list # Expects list from format_hamiltonian_parameters
    }

def format_operator(name, qobj):
    """Formats a QuantumOperator section."""
    qobj_props_dict, matrix_data_dict = _qobj_to_quantum_object_dict(qobj)
    if qobj_props_dict and "error" not in qobj_props_dict:
        operator_dict = {
            "name": str(name),
            "quantum_object": qobj_props_dict
        }
        if matrix_data_dict:
        	operator_dict["matrix"] = matrix_data_dict
        return operator_dict
    else:
        print(f"Warning: Skipping operator '{name}' due to Qobj conversion error.")
        return None

def format_state(label, qobj, state_type_hint=None):
    """
    Formats a QuantumState section.
    """
    qobj_props_dict, matrix_data_dict = _qobj_to_quantum_object_dict(qobj)
    if qobj_props_dict and "error" not in qobj_props_dict:
        if state_type_hint in ['ket', 'bra','oper']:
            qobj_props_dict['type'] = state_type_hint
        state_dict = {
            "label": str(label),
            "quantum_object": qobj_props_dict
        }
        if matrix_data_dict:
        	state_dict["matrix"] = matrix_data_dict
        return state_dict
    else:
        print(f"Warning: Skipping state '{label}' due to Qobj conversion error.")
        return None

def format_variable_dict(name, values, unit=None):
     """Formats the variable dictionary structure used within results."""
     var_dict = {
         "name": str(name),
         "values": np.array(values).tolist()
     }
     if unit:
         var_dict["unit"] = str(unit)
     return var_dict

def format_eigenvalue_result(property_name, eigenvalues, variable_dict):
    """
    Formats an EigenvaluesInVariable result section.
    variable_dict should be the output of format_variable_dict.
    """
    if not isinstance(eigenvalues, (np.ndarray, list)):
         print(f"Warning: Eigenvalues for '{property_name}' are not a list or array. Skipping.")
         return None
    if not variable_dict:
         print(f"Warning: Variable dictionary missing for eigenvalue result '{property_name}'. Skipping.")
         return None

    return {
        "calculation_type": "eigenvalues",
        "property_name": str(property_name),
        "eigenvalues": np.array(eigenvalues).tolist(),
        "variable": variable_dict
    }

def format_solver_stats(qutip_result_stats):
    """
    Formats SolverStats from a qutip result.stats dictionary.
    Maps known qutip stats keys to the keys expected by the NOMAD parser/schema.
    """
    if not isinstance(qutip_result_stats, dict):
        return {}

    stats_dict = {}
    # Map keys based on schema.py mappers
    if 'solver' in qutip_result_stats:
        stats_dict["solver_name"] = str(qutip_result_stats['solver'])
    if 'method' in qutip_result_stats:
        stats_dict["method"] = str(qutip_result_stats['method'])

    init_time = qutip_result_stats.get('ode_init_time', qutip_result_stats.get('init_time'))
    if init_time is not None:
        stats_dict["init_time_s"] = float(init_time)

    prep_time = qutip_result_stats.get('ode_prep_time', qutip_result_stats.get('prep_time'))
    if prep_time is not None:
        stats_dict["prep_time_s"] = float(prep_time)

    if 'run_time' in qutip_result_stats:
        stats_dict["run_time_s"] = float(qutip_result_stats['run_time'])

    # Step count
    n_steps_val = qutip_result_stats.get('num_steps', qutip_result_stats.get('nsteps'))
    if n_steps_val is not None:
        stats_dict["n_steps"] = int(n_steps_val)

    # Number of expectation operators
    num_e_ops_val = qutip_result_stats.get('num_e_ops', qutip_result_stats.get('num_exp_ops'))
    if num_e_ops_val is not None:
        stats_dict["num_e_ops"] = int(num_e_ops_val)

    # Description (e.g  Schrodinger Evolution)
    if 'description' in qutip_result_stats:
         stats_dict["description"] = str(qutip_result_stats['description'])



    return stats_dict



def format_time_evolution_result(property_name, expect_values, e_ops_names,
                                 time_variable_dict, qutip_result_stats=None,
                                 tlist=None, solver_options=None):
    """
    Formats a TimeEvolutionProperty result section.
    expect_values should be (times x ops).
    time_variable_dict should be the output of format_variable_dict for time.
    qutip_result_stats is the optional result.stats dictionary from qutip.
    tlist is the optional list/array of time points.
    solver_options is the optional dictionary of options passed to the solver.
    """
    if not isinstance(expect_values, (np.ndarray, list)):
         print(f"Warning: Expectation values for '{property_name}' are not a list or array. Skipping.")
         return None
    if not time_variable_dict:
         print(f"Warning: Time variable dictionary missing for time evolution result '{property_name}'. Skipping.")
         return None

    # Ensure expect_values is a list of lists
    expect_values_list = np.array(expect_values).tolist()

    result_dict = {
        "calculation_type": "time_evolution",
        "property_name": str(property_name),
        "expectation_values": expect_values_list,
        "e_ops_names": [str(name) for name in e_ops_names] if e_ops_names else [],
        "variable": time_variable_dict
    }

    # Format solver stats from qutip results
    solver_stats_dict = format_solver_stats(qutip_result_stats)

    # Add information from simulation setup if available
    if tlist is not None and len(tlist) > 0:
        try:
            solver_stats_dict["t_start"] = float(tlist[0])
            solver_stats_dict["t_end"] = float(tlist[-1])
            # If n_steps wasn't found in stats, maybe infer from tlist length
            if "n_steps" not in solver_stats_dict:
                 solver_stats_dict["n_steps"] = len(tlist)
        except (TypeError, IndexError, ValueError) as e:
             print(f"Warning: Could not extract t_start/t_end from tlist: {e}")

    if solver_options and isinstance(solver_options, dict):
         # Map the schema key '.final_state_saved'
         if 'store_final_state' in solver_options:
              solver_stats_dict["final_state_saved"] = bool(solver_options['store_final_state'])

    if solver_stats_dict: # Only add if not empty
        result_dict["solver_stats"] = solver_stats_dict

    return result_dict

# --- Main Assembly and Saving Function ---

def create_simulation_json(
    filename="simulation_nomad.json",
    program_info=None,
    system_info=None,
    hamiltonian_info=None, # Dictionary from format_spin_hamiltonian
    operators_list=None, # List of dictionaries from format_operator
    states_list=None,    # List of dictionaries from format_state
    results_list=None,   # List of dictionaries from format_eigenvalue/time_evolution_result
    simulation_name="Quantum Simulation",
    ):
    """
    Assembles the full simulation data dictionary and saves it to a JSON file.
    Modifies the output structure to match the parser's expectation of dictionaries
    for operators, states, and results, keyed by name/label or type.
    """
    simulation_data = {}

    # Add simulation name (used by parser's get_system if quantum_system name is missing)
    simulation_data["simulation_name"] = simulation_name

    # Add program info
    if program_info:
        simulation_data["program"] = program_info
    else:
        simulation_data["program"] = format_program_info() 

    # Add system info
    if system_info:
        simulation_data["quantum_system"] = system_info
    else:
         simulation_data["quantum_system"] = format_system_info() 

    # Add hamiltonian (using the generalized key 'spin_hamiltonian')
    if hamiltonian_info:
        simulation_data["spin_hamiltonian"] = hamiltonian_info
    else:
        print("Warning: Hamiltonian information not provided.")

    # Add operators 
    operators_dict = {}
    if operators_list:
        for op in operators_list:
            if isinstance(op, dict) and 'name' in op:
                operators_dict[op['name']] = op
            else:
                print(f"Warning: Skipping invalid operator entry in list: {op}")
    simulation_data["operators"] = operators_dict


    # Add states 
    states_dict = {}
    if states_list:
        for state in states_list:
            if isinstance(state, dict) and 'label' in state:
                 states_dict[state['label']] = state
            else:
                print(f"Warning: Skipping invalid state entry in list: {state}")

    simulation_data["states"] = states_dict


    # Add results 
    results_dict = {}
    if results_list:
        for res in results_list:
            if isinstance(res, dict) and 'calculation_type' in res:
                results_dict[res['calculation_type']] = res
            else:
                 print(f"Warning: Skipping invalid result entry in list: {res}")

    results_output_dict = {}
    if results_list:
        for i, res in enumerate(results_list):
            if isinstance(res, dict) and 'calculation_type' in res:
                # Create a unique key for each result, maybe using property_name if available, fallback to index
                key = res.get('property_name', f"result_{i}")
                results_output_dict[key] = res
            else:
                 print(f"Warning: Skipping invalid result entry in list at index {i}: {res}")

    simulation_data["results"] = results_output_dict


    #
    simulation_data["generation_timestamp"] = datetime.now().isoformat()

    # --- Write to JSON File ---
    try:
        output_dir = os.getcwd()
        full_path = os.path.join(output_dir, filename)
        with open(full_path, 'w') as f:
            # Use default=str as a fallback for non-standard types like complex numbers
            json.dump(simulation_data, f, indent=4, default=str)
        print(f"\nSuccessfully wrote NOMAD-schema compatible simulation data to '{filename}'")
        print(f"JSON file saved in directory: {output_dir}")
        return full_path # Return the path to the saved file
    except TypeError as e:
         print(f"\nError during JSON serialization: {e}")
         print("There might be incompatible data types (e.g., complex numbers not handled by default=str).")
         print("Problematic data structure snippet:")
         try:
             # Attempt to serialize with a custom handler to show problematic types
             print(json.dumps(simulation_data, indent=4, default=lambda o: f"<unserializable: {type(o)}>"))
         except Exception:
             print("(Could not serialize snippet for debugging)")
         return None
    except Exception as e:
        print(f"\nAn error occurred during JSON file writing: {e}")
        return None

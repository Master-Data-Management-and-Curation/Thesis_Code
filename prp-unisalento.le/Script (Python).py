import os
import glob
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from ncempy.io import dm
import numpy as np
import json

# Lista aggiornata dei parametri da cercare
METADATA_KEYS = [
    "Device Name", "Formatted Voltage", "Exposure (s)", "Acquisition Date",
    "Acquisition Time", "Formatted Indicated Mag", "Pixel Size (um)", "PixelDepth",
    "Stage Alpha", "Stage Beta", "Stage X", "Stage Y", "Stage Z",
    "Active Size (pixels)"  # Nuovo parametro aggiunto
]

def find_metadata_values(metadata):
    """Cerca nei metadati i parametri richiesti e ne estrae il valore dopo i due punti."""
    extracted_data = {key: "N/A" for key in METADATA_KEYS}  # Inizializza con N/A
   
    def recursive_search(data):
        """Ricorsivamente cerca le chiavi nei dizionari e liste annidate."""
        if isinstance(data, dict):
            for key, value in data.items():
                for target_key in METADATA_KEYS:
                    if target_key in key:  # Se il nome della chiave contiene il parametro cercato
                        extracted_data[target_key] = convert_value(value)  # Converte i dati
                recursive_search(value)  # Continua la ricerca nei sotto-dizionari
        elif isinstance(data, list):
            for item in data:
                recursive_search(item)  # Cerca in ogni elemento della lista

    recursive_search(metadata)
    return extracted_data

def convert_value(value):
    """Converte i tipi NumPy in tipi standard Python per la compatibilità JSON."""
    if isinstance(value, np.ndarray):
        return value.tolist()  # Converti array NumPy in lista Python
    elif isinstance(value, (np.int64, np.uint64, np.int32, np.uint32)):
        return int(value)  # Converti interi NumPy in interi Python
    elif isinstance(value, (np.float64, np.float32)):
        return float(value)  # Converti float NumPy in float Python
    return value  # Restituisci il valore originale se già compatibile

def extract_metadata(dm4_file):
    """Estrai SOLO i metadati richiesti da un file DM4."""
    try:
        dm4_data = dm.fileDM(dm4_file)
        metadata = dm4_data.allTags  # Estrarre tutti i metadati
       
        # Cerca i parametri e i valori dopo i due punti
        filtered_metadata = find_metadata_values(metadata)
        return filtered_metadata

    except Exception as e:
        return {"Errore": f"Errore nella lettura di {dm4_file}: {e}"}

def convert_to_text(metadata_dict):
    """Converte i metadati in una stringa formattata per il file di testo."""
    text_output = ""
    for file_name, metadata in metadata_dict.items():
        text_output += f"=== METADATI DI {file_name} ===\n\n"
        for key, value in metadata.items():
            text_output += f"{key}: {value}\n"
        text_output += "\n" + "=" * 50 + "\n\n"  # Separatore tra file
    return text_output

def save_results(folder_path, metadata_dict):
    """Salva i metadati sia in formato TXT che JSON."""
    output_txt = os.path.join(folder_path, "metadata_output.txt")
    output_json = os.path.join(folder_path, "metadata_output.json")

    try:
        # Salvataggio in TXT
        with open(output_txt, "w", encoding="utf-8") as txt_file:
            txt_file.write(convert_to_text(metadata_dict))
       
        # Salvataggio in JSON con conversione automatica dei tipi
        with open(output_json, "w", encoding="utf-8") as json_file:
            json.dump(metadata_dict, json_file, indent=4, ensure_ascii=False)

        messagebox.showinfo("Completato", f"Metadati salvati con successo in:\n{output_txt}\n{output_json}")
        open_folder(folder_path)

    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile salvare i file:\n{e}")

def process_dm4_files(folder_path):
    """Legge i file DM4 nella cartella e salva i metadati."""
    metadata_dict = {}
    dm4_files = glob.glob(os.path.join(folder_path, "*.dm4"))

    if not dm4_files:
        messagebox.showerror("Errore", "Nessun file DM4 trovato nella cartella selezionata.")
        return

    for dm4_file in dm4_files:
        metadata = extract_metadata(dm4_file)
        metadata_dict[os.path.basename(dm4_file)] = metadata

    save_results(folder_path, metadata_dict)

def open_folder(path):
    """Apre la cartella dei risultati in Esplora File/Finder."""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(f'explorer "{path}"')
        elif os.name == 'posix':  # Mac/Linux
            subprocess.run(['xdg-open', path] if 'linux' in sys.platform else ['open', path])
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile aprire la cartella:\n{e}")

def select_folder():
    """Apre la finestra di selezione della cartella e avvia l'elaborazione."""
    root = tk.Tk()
    root.withdraw()  # Nasconde la finestra principale

    folder_selected = filedialog.askdirectory(title="Seleziona la cartella con i file DM4")

    if folder_selected:
        process_dm4_files(folder_selected)
    else:
        messagebox.showinfo("Info", "Nessuna cartella selezionata. Operazione annullata.")

# Se eseguito con doppio click, usa la cartella dello script
if __name__ == "__main__":
    select_folder()
    input("\nPremi INVIO per chiudere...")  # Evita la chiusura immediata

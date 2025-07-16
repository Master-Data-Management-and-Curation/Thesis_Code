#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import shutil
import requests
import h5py
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QGroupBox, QGridLayout,
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
                             QComboBox, QCheckBox, QPushButton, QFileDialog, QMessageBox, QScrollArea, QSizePolicy)
from PyQt6.QtGui import QFont


# Definisce il font globale
APP_QFONT = QFont("Segoe UI", 11)

# Inserisci qui la tua API key e la base URL del server eLabFTW
BASE_URL = "https://prp-electronic-lab.areasciencepark.it/api/v2"
API_KEY = "48-35ba6041a796c9e4427d99b01f21edc8d7c21b4e392dc59cae24907b8caae8dba8a3a16760aface5a13548"

# Lista dei template disponibili con ID e descrizione
TEMPLATES = {
    "29 - Standard Beamtime Copia": 29
}

# Cartella report
REPORT_DIR = "ptirodat_generated_files"
REPORT_FILENAME = "experiment_report.html"

# Path dell'immagine HDF5 da estrarre
PTIR_SAMPLE_IMAGE1_PATH = "/Images/Image_000"
PTIR_SAMPLE_IMAGE2_PATH = "/Images/Image_001"

# Colori alternati per le righe delle tabelle nel report
ALT_COLOR_SUMMARY = "#ffe8cc"
ALT_COLOR_GROUPS = "#d1e0f0"
ALT_COLOR_MEASUREMENT = "#edd7c3"

# Fairified ptir variables
FAIR_PTIR_DIR = "ptirodat_generated_files"
FAIR_PTIR_SUFFIX = "_fair"
FAIR_PTIR_GROUP_NAME = "elab_metadata"

# Filename dei plot
PTIR_PLOT_OPTIR_PNG = "optir_plot.png"
PTIR_PLOT_RAMAN_PNG = "raman_plot.png"

PTIR_ANALISYS_FNAME = "ptir_structure.html"

# GET a eLab pasandogli l'ID del template che torna il json di risposta alla get
def fetch_template_json(template_id):
    url = f"{BASE_URL}/experiments_templates/{template_id}"
    print(url)
    headers = {"Authorization": API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    template = response.json()
    print("[DEBUG] Template JSON ricevuto.")
    return template

def fetch_resources_by_category(category_id):
    url = f"{BASE_URL}/items?cat={category_id}"
    headers = {"Authorization": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        items = response.json()
        return [{"id": item["id"], "title": item["title"]} for item in items]
    except Exception as e:
        print(f"[WARN] Impossibile caricare risorse per categoria {category_id}: {e}")
        return []
# prende in input la stringa json - questo son contiene le definizioni dei gruppi e degli extra fields
# - e li estrae come dictionary (definiscono i metadati!!!!)
def parse_extra_fields(template):
    metadata = template.get("metadata_decoded", {})
    raw_fields = metadata.get("extra_fields", {})
    elabftw_meta = metadata.get("elabftw", {})
    group_objects = sorted(elabftw_meta.get("extra_fields_groups", []), key=lambda g: g["id"])
    group_names_by_id = {g["id"]: g["name"] for g in group_objects}

    result = []
    for name, info in raw_fields.items():
        ftype = info.get("type", "text")
        description = info.get("description", "")
        group_id = info.get("group_id")
        group_name = group_names_by_id.get(group_id, "Generale")

        resources = []
        if ftype == "items":
            match = re.match(r"\[(\d+)]", description.strip())
            if match:
                cat_id = int(match.group(1))
                resources = fetch_resources_by_category(cat_id)
                if not resources:
                    continue  # salta se la categoria è vuota
            else:
                continue  # descrizione non valida per items

        result.append({
            "name": name,
            "type": ftype,
            "description": description,
            "group": group_name,
            "group_id": group_id,
            "units": info.get("units", []),
            "options": info.get("options", []),
            "default": info.get("value", ""),
            "readonly": info.get("readonly", False),
            "required": info.get("required", True),
            "position": info.get("position", 0),
            "resources": resources
        })

    result.sort(key=lambda f: (f["group_id"] or 0, f["position"]))
    return result, group_objects

# questa funzione estrae le prime due immagini dal file ptir in accordo con i percorsi definiti
# dalle variabili globali in testa e le salva mantenendo gli stessi nomi che hanno nel file ptir
# la directory di salvataggio è REPORT_DIR nella directory in cui si trova il file .ptir
def extract_and_save_images(hdf5_path):
    image_paths = []
    image_targets = [PTIR_SAMPLE_IMAGE1_PATH, PTIR_SAMPLE_IMAGE2_PATH]

    repo_dir = os.path.join(os.path.dirname(hdf5_path), REPORT_DIR)

    os.makedirs(repo_dir, exist_ok=True)

    try:
        with h5py.File(hdf5_path, "r") as f:
            for dataset_path in image_targets:
                if dataset_path not in f:
                    print(f"[WARN] Dataset '{dataset_path}' non trovato.")
                    continue
                try:
                    data = f[dataset_path][:]
                    dataset_name = os.path.basename(dataset_path)
                    output_path = os.path.join(repo_dir, f"{dataset_name}.png")
                    plt.imsave(output_path, data, cmap="gray")
                    image_paths.append(output_path)
                    print(f"[INFO] Saved image: {output_path}")
                except Exception as e:
                    print(f"[WARN] Errore durante il salvataggio di '{dataset_path}': {e}")
    except Exception as e:
        # In ambiente GUI, l'errore verrà mostrato con un message box (vedi sotto)
        raise Exception(f"Errore durante l'apertura di {hdf5_path}:\n{e}")

    return image_paths

def plot_measurements_h5py(file_path, output_dir, png_name_nonraman, png_name_raman):
    try:
        with h5py.File(file_path, 'r') as f:
            raman_data = []
            nonraman_data = []

            for key in f.keys():
                if key.startswith("Measurement_"):
                    group = f[key]
                    is_background = group.attrs.get('IsBackground', 0)
                    is_background = is_background.item() if hasattr(is_background, "item") else int(is_background)
                    is_raman = group.attrs.get('IsRaman', 0) if 'IsRaman' in group.attrs else 0
                    is_raman = is_raman.item() if hasattr(is_raman, "item") else int(is_raman)

                    if is_background != 0:
                        continue

                    if "Channel_000" in group and "Raw_Data" in group["Channel_000"]:
                        data = group["Channel_000"]["Raw_Data"][()]
                        if data.ndim == 2 and data.shape[0] == 1:
                            data = data[0]
                        if is_raman:
                            raman_data.append(data)
                        else:
                            nonraman_data.append(data)

            result = 0

            if nonraman_data:
                plt.figure()
                for data in nonraman_data:
                    plt.plot(data)
                plt.title("O-PTIR spectra")
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, png_name_nonraman))
                plt.close()
                result = 1

            if raman_data:
                plt.figure()
                for data in raman_data:
                    plt.plot(data)
                plt.title("Raman spectra")
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, png_name_raman))
                plt.close()
                result = 2 if result == 1 else 1

            return result

    except Exception as e:
        print(f"[h5py] Errore: {e}")
        return 0

def create_experiment(template_id):
    url = f"{BASE_URL}/experiments"
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}
    payload = {"template": template_id}

    # qui gli passo l'url dell'api experiments...il payload è il contenuto della chiamata
    # (un json che cotiene il template ID)
    response = requests.post(url, headers=headers, json=payload)
    # print("Status Code:", response.status_code)
    if response.status_code != 201:
        print("Errore durante la creazione:", response.text)
        return None
    location = response.headers.get("Location") # "location" è il path dell'esperimento con ultimo token l'ID
    if not location:
        print("Header 'Location' mancante nella risposta.")
        return None
    experiment_id = location.rstrip("/").split("/")[-1] #estrazione dell'ID
    # print(f"Esperimento creato con ID: {experiment_id}")
    return experiment_id

#aggiorna l'esperimento su eLab
def update_experiment_data(experiment_id, extra_data, all_fields, group_objects, template, experiment_title):
    #costruisce l'html del body
    table_rows = ""
    for field in all_fields:
        name = field["name"]
        if name in extra_data:
            value = extra_data[name]
        elif field["type"] == "items" and field["required"]:
            value = "0"
            extra_data[name] = "0"
        else:
            continue
        value_html = str(value).replace("\n", "<br>")
        table_rows += (
            f"<tr>"
            f"<td style='padding: 6px 12px; border: 1px solid #ccc;'><strong>{name}</strong></td>"
            f"<td style='padding: 6px 12px; border: 1px solid #ccc;'>{value_html}</td>"
            f"</tr>\n"
        )

    body_html = f"""
    <table style='border-collapse: collapse; border: 1px solid #ccc;'>{table_rows}</table>
    """

#la storiaccia delle atringa nella stringa:
#si prende la struttura estratta dal template,
    original_fields = template.get("metadata_decoded", {}).get("extra_fields", {})
    metadata_obj = {
        "elabftw": {
            "extra_fields_groups": group_objects
        },
        "extra_fields": {}
    }
#sta inserendo i valori letti dall'interfaccia negli extra fields del dictionary metadata_obj
    for field in all_fields:
        name = field["name"]
        updated_value = extra_data.get(name, "")
        original_entry = original_fields.get(name, {}).copy()
        if(field["type"]) == "number":
            updated_value = updated_value.split(" ")[0]
        original_entry["value"] = updated_value
        metadata_obj["extra_fields"][name] = original_entry

#fa la follia  (non documentata) di rendere il dictionary metadata_obj una stringa json che infiliamo nel campo "metadata" del json di patch
    metadata_str = json.dumps(metadata_obj)
    payload = {
        "title": experiment_title,
        "body": body_html,
        "metadata": metadata_str
    }
    url = f"{BASE_URL}/experiments/{experiment_id}"
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}
    # print(f"[DEBUG] PATCH esperimento ID {experiment_id}")
    print(payload)
    try:
        # ecco la patch
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status() #se lo stato è diverso da 201 solleva un'eccezzione
        print("[DEBUG] Esperimento aggiornato con successo.")
    except Exception as e:
        print("[ERRORE PATCH DATI EXPERIMENT]", e)
        raise

def create_fair_ptir_copy(original_ptir_path, experiment_id, extra_fields_data, group_objects, all_fields):
    fair_dir = os.path.join(os.path.dirname(original_ptir_path), FAIR_PTIR_DIR)
    os.makedirs(fair_dir, exist_ok=True)

    base_name = os.path.basename(original_ptir_path)
    name, ext = os.path.splitext(base_name)
    fair_filename = name + FAIR_PTIR_SUFFIX + ext
    fair_path = os.path.join(fair_dir, fair_filename)
    try:
        shutil.copy2(str(original_ptir_path), str(fair_path))
        with h5py.File(fair_path, "a") as f:
            if FAIR_PTIR_GROUP_NAME in f:
                del f[FAIR_PTIR_GROUP_NAME]
            meta_group = f.create_group(FAIR_PTIR_GROUP_NAME)
            meta_group.attrs["elab_id"] = str(experiment_id)
            grouped_fields = {}
            for field in all_fields:
                grouped_fields.setdefault(field["group"], []).append(field)
            for group in group_objects:
                group_name = group["name"]
                group_fields = grouped_fields.get(group_name, [])
                group_target = meta_group.create_group(group_name) if group_name else meta_group
                for field in group_fields:
                    fname = field["name"]
                    value = extra_fields_data.get(fname, "")
                    ftype = field["type"]
                    if ftype == "number":
                        try:
                            val = float(value.split()[0])
                        except Exception:
                            val = str(value)
                    elif ftype == "checkbox":
                        val = bool(value)
                    elif ftype == "items":
                        id_str = str(value)
                        titolo = next(
                            (res["title"] for res in field.get("resources", [])
                             if str(res["id"]) == id_str),
                            "[descrizione non trovata]"
                        )
                        val = f"{id_str} - {titolo}"
                    # Tutti gli altri campi diventano stringa
                    else:
                        val = str(value)
                    group_target.attrs[fname] = val
        print(f"[INFO] File FAIR PTIR creato correttamente in: {fair_path}")
        return fair_path
    except Exception as e:
        print(f"[ERROR] Errore durante la creazione del file FAIR PTIR: {e}")
        return None

def get_ptir_metadata(file_path, value_attr_names, minmax_attr_names, list_attr_names):
    value_attr_values = []
    minmax_attr_values = [[None, None] for _ in minmax_attr_names]
    list_attr_values = [ ([], []) for _ in list_attr_names ]
    count_non_raman = 0
    count_raman = 0

    def clean_value(val):
        if isinstance(val, bytes):
            val = val.decode("utf-8")
        elif isinstance(val, np.ndarray) and val.size == 1:
            val = val.item()
        elif isinstance(val, (list, tuple)) and len(val) == 1:
            val = val[0]
        return str(val)

    try:
        with h5py.File(file_path, "r") as f:
            for attr_path in value_attr_names:
                try:
                    if attr_path in f.attrs:
                        val = f.attrs[attr_path]
                    elif attr_path in f:
                        ds = f[attr_path]
                        if hasattr(ds, 'attrs') and len(ds.attrs) > 0:
                            value_attr_values.append({k: clean_value(v) for k, v in dict(ds.attrs).items()})
                            continue
                        val = ds[()]
                    else:
                        parts = attr_path.strip("/").split("/")
                        group_path = "/".join(parts[:-1])
                        attr_name = parts[-1]
                        if group_path in f:
                            group = f[group_path]
                            if attr_name in group.attrs:
                                val = group.attrs[attr_name]
                            else:
                                value_attr_values.append("[NON PRESENTE]")
                                continue
                        else:
                            value_attr_values.append("[NON PRESENTE]")
                            continue
                    val = clean_value(val)
                    value_attr_values.append(val)
                except Exception as e:
                    print(f"[WARN] Errore lettura valore '{attr_path}': {e}")
                    value_attr_values.append("[UNDEFINED]")
            for key in f:
                if not key.startswith("Measurement_"):
                    continue
                group = f[key]
                attrs = group.attrs
                is_bg = attrs.get("IsBackground", 0)
                is_bg = is_bg.item() if hasattr(is_bg, "item") else int(is_bg)
                if is_bg != 0:
                    continue
                is_raman = attrs.get("IsRaman", 0)
                is_raman = is_raman.item() if hasattr(is_raman, "item") else int(is_raman)
                index = 1 if is_raman else 0
                if index == 0:
                    count_non_raman += 1
                else:
                    count_raman += 1
                for i, attr in enumerate(minmax_attr_names):
                    if attr in attrs:
                        val = attrs[attr]
                        val = val.item() if hasattr(val, "item") else val
                        try:
                            val = float(val)
                        except:
                            continue
                        current_minmax = minmax_attr_values[i][index]
                        if current_minmax is None:
                            minmax_attr_values[i][index] = (val, val)
                        else:
                            current_min, current_max = current_minmax
                            minmax_attr_values[i][index] = (min(current_min, val), max(current_max, val))
                for i, attr in enumerate(list_attr_names):
                    if attr in attrs:
                        val = attrs[attr]
                        val = clean_value(val)
                        target_list = list_attr_values[i][index]
                        if val not in target_list:
                            target_list.append(val)
    except Exception as e:
        print(f"[ERROR] Errore lettura file PTIR: {e}")
    return value_attr_values, minmax_attr_values, list_attr_values, (count_non_raman, count_raman)

def format_list_field(lst):
    if isinstance(lst, list):
        return ", ".join(lst)
    return str(lst)

def create_html_report(experiment_id, experiment_title, extra_data, group_objects, all_fields, ptir_file_path, saved_images):
    def sanitize(value):
        return value if value else "[NON PRESENTE]"

    def build_table_row(label, value, alt=False):
        cls = "alt-row" if alt else ""
        return f'<tr class="{cls}"><td>{label}</td><td>{sanitize(value)}</td></tr>'

    fair_dir = os.path.join(os.path.dirname(ptir_file_path), REPORT_DIR)
    os.makedirs(fair_dir, exist_ok=True)

    out_path = os.path.join(fair_dir, REPORT_FILENAME)

    css = """
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; max-width: 960px; margin: auto; background-color: #f9f9f9; color: #333; }}
        h1 {{ text-align: center; font-size: 22px; margin-bottom: 5px; }}
        h2 {{ font-style: italic; text-align: center; font-size: 18px; margin-top: 0; color: #555; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .label {{ font-weight: bold; margin-top: 20px; margin-bottom: 10px; font-size: 16px; border-bottom: 2px solid #004b91; padding-bottom: 5px; color: #004b91; }}
        .image-container {{ background: #fff; border: 1px solid #ccc; padding: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; max-width: 48%; width: 100%; }}
        .image-container img {{ width: 100%; height: auto; }}
        .image-container.centered {{
            margin: 0;
            flex: 1 1 48%;
            max-width: 48%;
        }}
        .row {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        table {{ border-collapse: collapse; width: 100%; table-layout: auto; background-color: white; margin-bottom: 20px; }}
        td {{ border: 1px solid #bbb; padding: 8px 12px; text-align: left; }}
        td:first-child {{ white-space: nowrap; width: 1%; font-weight: bold; }}
        .main-table tr.alt-row td {{ background-color: {summary}; }}
        .group-fields tr.alt-row td {{ background-color: {groups}; }}
        .measurement-settings tr.alt-row td {{ background-color: {measurement}; }}
        .plot-column {{
            width: 48%;
        }}
    </style>
    """.format(
        summary=ALT_COLOR_SUMMARY,
        groups=ALT_COLOR_GROUPS,
        measurement=ALT_COLOR_MEASUREMENT
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{experiment_title}</title>
    {css}
</head>
<body>
    <div class="header">
        <h1>{experiment_title}</h1>
        <h2>Short report with data preview</h2>
    </div>
    """

    html += '<table class="main-table">\n'
    html += build_table_row("Experiment number", experiment_id, alt=True)

    instr_value = extra_data.get("Instrumentation", "")
    instr_label = instr_value
    for field in all_fields:
        if field["name"] == "Instrumentation" and field["type"] == "items":
            id_map = {str(res["id"]): res["title"] for res in field.get("resources", [])}
            if instr_value:
                instr_label = f"{instr_value} - {id_map.get(instr_value, '[descrizione non trovata]')}"
            else:
                instr_label = "[UNDEFINED]"
            break

    html += build_table_row("Instrumentation", instr_label)
    html += build_table_row("Proposal", extra_data.get("Proposal"), alt=True)
    html += build_table_row("Principal investigator", extra_data.get("Principal investigator"))
    html += build_table_row("Local contact", extra_data.get("Local contact"), alt=True)
    html += '</table>\n'

    if saved_images:
        html += f'<div class="row">'
        for path in saved_images:
            img_name = os.path.basename(path)
            html += f'<div class="image-container centered"><img src="{img_name}" alt="Image"></div>\n'
        html += f'</div>\n'

    sorted_groups = sorted(group_objects, key=lambda g: g["id"])
    grouped_fields = {}
    for field in all_fields:
        if field["group"] == "Experiment info":
            continue
        grouped_fields.setdefault(field["group"], []).append(field)
    for group in sorted_groups:
        group_name = group["name"]
        if group_name == "Experiment info" or group_name not in grouped_fields:
            continue
        html += f'<div class="label">{group_name}</div>\n<table class="group-fields">\n'
        fields = sorted(grouped_fields[group_name], key=lambda f: f["position"])
        alt = True
        for field in fields:
            raw_value = extra_data.get(field["name"], "")
            display_value = raw_value
            if field["type"] == "items" and field.get("resources"):
                id_map = {str(res["id"]): res["title"] for res in field["resources"]}
                display_value = f"{raw_value} - {id_map.get(raw_value, '[descrizione non trovata]')}" if raw_value else "[NON PRESENTE]"
            html += build_table_row(field["name"], display_value, alt=alt)
            alt = not alt
        html += '</table>\n'

    repo_dir = os.path.join(os.path.dirname(ptir_file_path), REPORT_DIR)

    result = plot_measurements_h5py(ptir_file_path, repo_dir, PTIR_PLOT_OPTIR_PNG, PTIR_PLOT_RAMAN_PNG)

    op_mode = "[UNDEFINED]"
    if result == 1:
        op_mode = "O-PTIR"
    elif result == 2:
        op_mode = "O-PTIR, Raman"

    value_attr_values, minmax_attr_values, list_attr_values, measurements_count = get_ptir_metadata(
        ptir_file_path,
        ["/Measurement_000/Detector", "/Measurement_000/IRPower", "/Measurement_000/ProbePower"],
        ["Averages"],
        ["BeamPath", "DetectorGain", "Objective", "PowerScalars"]
    )

    isalt = False
    html += '<div class="label" style="margin-top:30px">Measurement settings</div>\n<table class="measurement-settings">\n'
    html += build_table_row("Operational mode", op_mode, alt=True)
    html += build_table_row("Detector", value_attr_values[0])
    html += build_table_row("IR power", value_attr_values[1], alt=True)
    html += build_table_row("Vis power", value_attr_values[2])

    html += build_table_row("Averages O-PTIR min - max", str(minmax_attr_values[0][0][0]) + " - " + str(minmax_attr_values[0][0][1]), alt=True)
    if result == 2:
        html += build_table_row("Averages Raman min - max", str(minmax_attr_values[0][1][0]) + " - " + str(minmax_attr_values[0][1][1]), alt=isalt)
        isalt = not isalt

    html += build_table_row("Beam path O-PTIR", format_list_field(list_attr_values[0][0]), alt=isalt)
    isalt = not isalt
    if result == 2:
        html += build_table_row("Beam path Raman", format_list_field(list_attr_values[0][1]), alt=isalt)
        isalt = not isalt

    html += build_table_row("Detector gain O-PTIR", format_list_field(list_attr_values[1][0]), alt=isalt)
    isalt = not isalt
    if result == 2:
        html += build_table_row("Detector gain Raman", format_list_field(list_attr_values[1][1]), alt=isalt)
        isalt = not isalt

    html += build_table_row("Objective O-PTIR", format_list_field(list_attr_values[2][0]), alt=isalt)
    isalt = not isalt
    if result == 2:
        html += build_table_row("Objective Raman", format_list_field(list_attr_values[2][1]), alt=isalt)
        isalt = not isalt

    html += build_table_row("Power scalars O-PTIR", format_list_field(list_attr_values[3][0]), alt=isalt)
    isalt = not isalt
    if result == 2:
        html += build_table_row("Power scalars Raman", format_list_field(list_attr_values[3][1]), alt=isalt)
        isalt = not isalt


    html += build_table_row("# O-PTIR spectra", str(measurements_count[0]), alt=isalt)
    isalt = not isalt
    if result == 2:
        html += build_table_row("# Raman spectra", str(measurements_count[1]), alt=isalt)
        isalt = not isalt

    html += build_table_row("PTIR file", os.path.basename(ptir_file_path), alt=isalt)
    html += '</table>\n'

    if result == 1:
        html += f'<div class="image-container centered"><img src="{PTIR_PLOT_OPTIR_PNG}" alt="O-PTIR Plot"></div>\n'
    elif result == 2:
        html += f'<div class="row">'
        html += f'<div class="image-container"><img src="{PTIR_PLOT_OPTIR_PNG}" alt="O-PTIR Plot"></div>'
        html += f'<div class="image-container"><img src="{PTIR_PLOT_RAMAN_PNG}" alt="Raman Plot"></div>'
        html += f'</div>\n'
    html += '</body></html>'
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


# --- Interfaccia Utente con PyQt6 ---

class InitialWindow(QWidget):
    """
    Finestra iniziale per la selezione del template e del file PTIR.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Template & PTIR file selection")
        self.setMinimumSize(600, 180)
        self.setFont(APP_QFONT)
        self.setup_ui() # costruisco il layout

    def setup_ui(self):
        layout = QGridLayout()

        self.setLayout(layout)

        # Selezione Template
        lbl_template = QLabel("Template:")
        layout.addWidget(lbl_template, 0, 0)
        self.template_combo = QComboBox()
        self.template_combo.setFont(APP_QFONT)
        self.template_combo.addItems(list(TEMPLATES.keys())) # prende le chiavi del config
        layout.addWidget(self.template_combo, 0, 1, 1, 2)

        # Selezione file PTIR
        lbl_file = QLabel("PTIR file:")
        layout.addWidget(lbl_file, 1, 0)
        self.file_line_edit = QLineEdit()
        self.file_line_edit.setFont(APP_QFONT)
        self.file_line_edit.setReadOnly(True)
        layout.addWidget(self.file_line_edit, 1, 1)
        btn_browse = QPushButton("Browse")
        btn_browse.setFont(APP_QFONT)
        btn_browse.clicked.connect(self.browse_file)
        layout.addWidget(btn_browse, 1, 2)

        # Bottone Continue
        self.btn_continue = QPushButton("Continue")
        self.btn_continue.setFont(APP_QFONT)
        self.btn_continue.setEnabled(False)
        self.btn_continue.setFixedHeight(50)
        self.btn_continue.clicked.connect(self.proceed)
        layout.addWidget(self.btn_continue, 2, 0, 1, 3)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PTIR file", "", "PTIR files (*.ptir);;All files (*)")
        if file_path:
            self.file_line_edit.setText(file_path)
            self.btn_continue.setEnabled(True)

    def proceed(self):
        selection = self.template_combo.currentText()
        file_path = self.file_line_edit.text()
        if selection not in TEMPLATES:
            QMessageBox.critical(self, "Error", "Select a valid template.")
            return
        if not file_path:
            QMessageBox.critical(self, "Error", "Select an HDF5 file.")
            return
        template_id = TEMPLATES[selection]
        try:
            saved_images_paths = extract_and_save_images(file_path)
            print(f"[DEBUG] Immagini salvate: {saved_images_paths}")
            print("[DEBUG] Ora recupero il template...")

            # qui c'è la prima chiamata a  eLab che recupera il json del template
            template = fetch_template_json(template_id)
            print(template)
            # faccio un parsing della stringa json e ritorna i dati in dizionari
            extra_fields, group_objects = parse_extra_fields(template)
            print("[DEBUG] Extra fields estratti.")
            self.hide()  # Nascondo la finestra iniziale
            # creo e visualizzo la finestra di input con tutti i campi definiti dal parsing
            self.main_form = MainForm(extra_fields, template_id, group_objects, template, saved_images_paths, file_path)
            self.main_form.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Terminated due to previous error:\n{e}")
            print("[ERROR]", e)

class MainForm(QMainWindow):
    """
    Finestra principale per compilare il form dell’esperimento.
    """
    def __init__(self, extra_fields, template_id, group_objects, template, saved_images_paths, ptir_file_path):
        super().__init__()
        self.extra_fields = extra_fields
        self.template_id = template_id
        self.group_objects = group_objects
        self.template = template
        self.saved_images_paths = saved_images_paths
        self.ptir_file_path = ptir_file_path
        self.field_widgets = {}
        self.setWindowTitle(f"Experiment Form - Template {template_id}")
        self.setFont(APP_QFONT)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Aggiungiamo uno scroll area nel caso ci siano tanti campi
        scroll = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.form_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.form_layout)
        scroll.setWidget(self.scroll_widget)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        self.create_form(self.form_layout)

        self.btn_submit = QPushButton("Submit")
        self.btn_submit.setFont(APP_QFONT)
        self.btn_submit.setFixedHeight(50)
        self.btn_submit.clicked.connect(self.submit)
        main_layout.addWidget(self.btn_submit)

    def create_form(self, layout):
        # Raggruppa i campi per gruppo
        grouped_fields = {}
        for field in self.extra_fields:
            grouped_fields.setdefault(field["group"], []).append(field)
        # Crea un QGroupBox per ogni gruppo
        for group_name, fields in grouped_fields.items():
            group_box = QGroupBox(group_name if group_name else "Generale")
            group_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
            group_box.setFont(APP_QFONT)
            grid = QGridLayout()
            grid.setHorizontalSpacing(0)
            group_box.setLayout(grid)
            layout.addWidget(group_box)
            for idx, field in enumerate(fields):
                name = field["name"]
                ftype = field["type"]
                desc = field["description"]
                default = field["default"]
                readonly = field["readonly"]
                units = field["units"]
                options = field["options"]
                resources = field.get("resources", [])
                lbl = QLabel(name)
                lbl.setFont(APP_QFONT)
                lbl.setStyleSheet("padding-right: 5px;")
                grid.addWidget(lbl, idx, 0)
                if ftype == "text" and "[multiline]" in desc.lower():
                    widget = QTextEdit()
                    widget.setFont(APP_QFONT)
                    widget.setFixedHeight(80)
                    widget.setPlainText(default)
                    widget.setReadOnly(readonly)
                    grid.addWidget(widget, idx, 1)
                    self.field_widgets[name] = widget
                elif ftype in ["select", "radio"]:
                    widget = QComboBox()
                    widget.setFont(APP_QFONT)
                    widget.addItems([str(opt).strip() for opt in options])
                    if default in options:
                        widget.setCurrentText(default)
                    else:
                        if options:
                            widget.setCurrentIndex(0)
                    grid.addWidget(widget, idx, 1)
                    self.field_widgets[name] = widget
                elif ftype == "checkbox":
                    widget = QCheckBox()
                    widget.setChecked(bool(default))
                    widget.setEnabled(not readonly)
                    widget.setFont(APP_QFONT)
                    grid.addWidget(widget, idx, 1)
                    self.field_widgets[name] = widget
                elif ftype == "number":
                    # Crea un contenitore con layout orizzontale per raggruppare il QLineEdit e la QComboBox
                    container = QWidget()
                    h_layout = QHBoxLayout(container)
                    h_layout.setContentsMargins(0, 0, 0, 0)  # Rimuove i margini extra
                    h_layout.setSpacing(5)  # Puoi regolare lo spacing se necessario

                    # Crea il QLineEdit per il valore numerico
                    widget = QLineEdit()
                    widget.setFont(APP_QFONT)
                    widget.setText(default)
                    widget.setReadOnly(readonly)
                    h_layout.addWidget(widget)

                    # Se sono previste delle unità, crea la QComboBox per selezionarle
                    if units:
                        unit_combo = QComboBox()
                        unit_combo.setFont(APP_QFONT)
                        unit_combo.addItems(units)
                        unit_combo.setCurrentIndex(0)
                        h_layout.addWidget(unit_combo)
                        # Imposta lo stretch uguale per condividere l'area orizzontale
                        h_layout.setStretch(0, 1)
                        h_layout.setStretch(1, 0)
                        self.field_widgets[name + "_unit"] = unit_combo
                    else:
                        h_layout.setStretch(0, 1)

                    # Aggiunge il contenitore alla griglia, facendo sì che occupi due colonne (la stessa larghezza degli altri controlli singoli)
                    grid.addWidget(container, idx, 1, 1, 2)
                    # grid.addWidget(container, idx, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)
                    self.field_widgets[name] = widget
                elif ftype == "items" and resources:
                    widget = QComboBox()
                    widget.setFont(APP_QFONT)
                    id_to_title = {str(item["id"]): item["title"] for item in resources}
                    display_list = [f"{k} - {id_to_title[k]}" for k in id_to_title]
                    widget.addItems(display_list)
                    if display_list:
                        widget.setCurrentIndex(0)
                    grid.addWidget(widget, idx, 1)
                    self.field_widgets[name] = widget
                else:
                    widget = QLineEdit()
                    widget.setFont(APP_QFONT)
                    widget.setText(default)
                    widget.setReadOnly(readonly)
                    grid.addWidget(widget, idx, 1)
                    self.field_widgets[name] = widget


    def showEvent(self, event):
        super().showEvent(event)
        # Calcola l'altezza ideale della finestra in base al contenuto della scroll area
        screen_geom = QApplication.primaryScreen().availableGeometry()
        max_allowed_height = int(screen_geom.height() * 0.9)
        # Ottieni l'altezza necessaria per i widget interni della scroll area
        content_height = self.scroll_widget.sizeHint().height()
        submit_height = self.btn_submit.sizeHint().height()
        # Aggiungi un margine per tenere conto di spazi, bordi, etc.
        extra_margins = 50  # Regola questo valore se necessario
        desired_height = content_height + submit_height + extra_margins
        new_height = min(desired_height, max_allowed_height)
        # Ridimensiona la finestra principale in altezza
        self.resize(600, new_height)

# raccoglie i dati dall'intefraccia, costruisce il json da inviare a eLab e salva l'esperimento
    def submit(self):
        errors = []
        final_data = {} #questa è la variabile che alla fine viene trasformata in json
        for field in self.extra_fields:
            name = field["name"]
            ftype = field["type"]
            required = field["required"]
            widget = self.field_widgets.get(name)
            if widget is None:
                continue
            if ftype == "text" and "[multiline]" in field["description"].lower():
                val = widget.toPlainText().strip()
            elif ftype == "checkbox":
                val = widget.isChecked()
            elif ftype == "items":
                current_text = widget.currentText()
                val = current_text.split(" - ")[0].strip() if current_text else ""
            elif isinstance(widget, QComboBox):
                val = widget.currentText().strip()
            else:  # QLineEdit
                val = widget.text().strip()
            if required and not val:
                errors.append(f"Field '{name}' is required.")
            if ftype == "number" and (name + "_unit") in self.field_widgets:
                unit = self.field_widgets[name + "_unit"].currentText()
                val = f"{val} {unit}".strip()
            final_data[name] = val

        if errors:
            QMessageBox.critical(self, "Validation errors", "\n".join(errors))
            return


        try:
            print(f"[INFO] Creazione esperimento...")
            experiment_id = create_experiment(self.template_id) # crea l'esperimento da tempalte ID
            print(f"[INFO] Creato esperimento {experiment_id}")

#dati da inserire nell'update dell'esperimento appena creato
#titolo creato secondo questo schema: "Experiment"_proposal_PI_date
            now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            proposal = final_data.get("Proposal", "").strip()
            pi = final_data.get("Principal investigator", "").strip()
            experiment_title = f"{proposal} {pi} {now_str}".strip()
            if not experiment_title or experiment_title == now_str:
                experiment_title = f"Esperimento {now_str}"

#aggiornamento dell'esperimento attraverso patch eLab
            print(f"[INFO] Patch esperimento...")
            update_experiment_data(
                experiment_id=experiment_id,
                extra_data=final_data,
                all_fields=self.extra_fields,
                group_objects=self.group_objects,
                template=self.template,
                experiment_title=experiment_title
            )
            print(f"[INFO] Esperimento patchato")

            print(f"[INFO] Creazione copia ptir fairificata...")
            create_fair_ptir_copy(
                original_ptir_path=self.ptir_file_path,
                experiment_id=experiment_id,
                extra_fields_data=final_data,
                group_objects=self.group_objects,
                all_fields=self.extra_fields
            )
            print(f"[INFO] Copia ptir fairificata creata")

            print(f"[INFO] Creazione report html...")
            create_html_report(
                experiment_id=experiment_id,
                experiment_title=experiment_title,
                extra_data=final_data,
                group_objects=self.group_objects,
                all_fields=self.extra_fields,
                ptir_file_path=self.ptir_file_path,
                saved_images=self.saved_images_paths
            )
            print(f"[INFO] Report html creato")
            QMessageBox.information(self, "Info", f"Esperimento creato con successo")

            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error:\n{e}")
            print(f"[ERROR] {e}")

if __name__ == "__main__":

    with open("config.json", "r", encoding="utf-8") as f: config_dict = json.load(f)

    BASE_URL = config_dict["BASE_URL"]
    API_KEY = config_dict["API_KEY"]
    TEMPLATES = config_dict["TEMPLATES"]

    # creo l'interfaccia grafica
    app = QApplication(sys.argv)
    initial_window = InitialWindow()
    initial_window.show()
    sys.exit(app.exec())

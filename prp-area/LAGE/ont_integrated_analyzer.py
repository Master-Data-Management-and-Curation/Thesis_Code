#!/usr/bin/env python3
"""
ONT_Integrated_Analyzer - comprehensive analysis of Oxford Nanopore data 

analyzes nanopore sequencing data with:
- pod5/fastq comparisons
- metrics extraction
- quality assessments
- fair-compliance enhancements

author: AREA Science Park
version: 4.0
"""

import os
import sys
import json
import csv
import glob
import argparse
import datetime
import re
import uuid
import hashlib
import pandas as pd
import numpy as np
from collections import OrderedDict
from pathlib import Path
import time

# --- Utility Functions ---

def numpy_to_python_type(obj):
    """converts numpy types to python types for json serialization"""
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, (np.bool_)):
        return bool(obj)
    elif isinstance(obj, (dict,)):
        return {k: numpy_to_python_type(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [numpy_to_python_type(i) for i in obj]
    return obj

# --- File Finding Functions ---

def find_pod5_fastq_dirs(parent_dir):
    """finds pod5 and fastq directories"""
    dirs = {
        "pod5": None,
        "fastq_pass": None,
        "fastq_fail": None, 
        "fastq_skip": None
    }
    
    # look for directories
    pod5_dir = os.path.join(parent_dir, "pod5")
    if os.path.isdir(pod5_dir):
        dirs["pod5"] = pod5_dir
    
    for fastq_type in ["fastq_pass", "fastq_fail", "fastq_skip"]:
        fastq_dir = os.path.join(parent_dir, fastq_type)
        if os.path.isdir(fastq_dir):
            dirs[fastq_type] = fastq_dir
    
    return dirs

def find_data_files(directory):
    """finds relevant data files in the directory"""
    data_files = {
        "final_summary": None,
        "sequencing_summary": None,
        "report_json": None,
        "report_html": None,
        "pore_activity": None,
        "throughput": None,
        "sample_sheet": None,
        "sequencing_telemetry": None
    }
    
    # find files by patterns
    for file in os.listdir(directory):
        if file.endswith(".txt") and "final_summary" in file:
            data_files["final_summary"] = os.path.join(directory, file)
        elif file.endswith(".txt") and "sequencing_summary" in file:
            data_files["sequencing_summary"] = os.path.join(directory, file)
        elif file.endswith(".json") and "report" in file:
            data_files["report_json"] = os.path.join(directory, file)
        elif file.endswith(".html") and "report" in file:
            data_files["report_html"] = os.path.join(directory, file)
        elif file.endswith(".csv") and "pore_activity" in file:
            data_files["pore_activity"] = os.path.join(directory, file)
        elif file.endswith(".csv") and "throughput" in file:
            data_files["throughput"] = os.path.join(directory, file)
        elif file.endswith(".csv") and "sample_sheet" in file:
            data_files["sample_sheet"] = os.path.join(directory, file)
        elif file.endswith(".js") and "telemetry" in file:
            data_files["sequencing_telemetry"] = os.path.join(directory, file)
    
    return data_files

def extract_run_metadata(data_files, directory_name):
    """
    extracts run metadata from available files
    
    tries to get flowcell id, date, protocol, etc. from multiple sources
    """
    metadata = {
        "flowcell_id": "Unknown",
        "run_date": "Unknown",
        "protocol": "Unknown",
        "sample_id": "Unknown"
    }
    
    # try to extract from directory name using regex
    flowcell_match = re.search(r'(PAY\d+|FAK\d+|FAL\d+)', directory_name)
    date_match = re.search(r'(\d{8})', directory_name)
    
    if flowcell_match:
        metadata["flowcell_id"] = flowcell_match.group(1)
        # get instrument type from flowcell prefix
        prefix = metadata["flowcell_id"][:3]
        if prefix == "PAY":
            metadata["instrument_type"] = "PromethION"
        elif prefix in ["FAK", "FAL"]:
            metadata["instrument_type"] = "MinION/GridION"
    
    if date_match:
        date_str = date_match.group(1)
        try:
            # convert to YYYY-MM-DD
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            metadata["run_date"] = formatted_date
        except:
            metadata["run_date"] = date_str
    
    # try final_summary.txt (more reliable)
    if data_files.get("final_summary"):
        try:
            with open(data_files["final_summary"], 'r') as f:
                content = f.read()
                
                # search patterns
                key_patterns = {
                    "flowcell_id": [r'flow_?cell_?id=([^\r\n]+)'],
                    "run_date": [
                        r'started=([^\r\n]+)', 
                        r'protocol_start_time=([^\r\n]+)',
                        r'exp_start_time=([^\r\n]+)'
                    ],
                    "protocol": [
                        r'protocol=([^\r\n]+)',
                        r'protocol_?name=([^\r\n]+)',
                        r'protocol_?group_?id=([^\r\n]+)'
                    ],
                    "sample_id": [
                        r'sample_?id=([^\r\n]+)',
                        r'sample_?name=([^\r\n]+)'
                    ]
                }
                
                # search for each field
                for field, patterns in key_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            metadata[field] = match.group(1).strip()
                            break
        except:
            pass
    
    # try report_json (also reliable)
    if data_files.get("report_json"):
        try:
            with open(data_files["report_json"], 'r') as f:
                data = json.load(f)
                
                # check metadata
                if "metadata" in data:
                    meta = data["metadata"]
                    
                    # flowcell data
                    if "flow_cell" in meta:
                        fc = meta["flow_cell"]
                        if "flow_cell_id" in fc:
                            metadata["flowcell_id"] = fc["flow_cell_id"]
                    
                    # protocol data
                    if "protocol" in meta:
                        protocol = meta["protocol"]
                        if "name" in protocol:
                            metadata["protocol"] = protocol["name"]
                        if "start_time" in protocol:
                            date_str = protocol["start_time"]
                            if 'T' in date_str:  # ISO format
                                date_part = date_str.split('T')[0]
                                metadata["run_date"] = date_part
                    
                    # instrument data
                    if "instrument" in meta:
                        instrument = meta["instrument"]
                        if "type" in instrument:
                            metadata["instrument_type"] = instrument["type"]
                    
                    # sample data
                    if "sample" in meta:
                        sample = meta["sample"]
                        if "name" in sample:
                            metadata["sample_id"] = sample["name"]
        except:
            pass
    
    # clean up values
    for key, value in metadata.items():
        if value == "NA" or value == "None" or value == "":
            metadata[key] = "Unknown"
    
    # extract sequencing kit from protocol string
    if metadata["protocol"] != "Unknown" and ":" in metadata["protocol"]:
        parts = metadata["protocol"].split(":")
        if len(parts) >= 3:
            # format: protocol:flowcell:kit:other
            metadata["sequencing_kit"] = parts[2]  # e.g., SQK-16S114-24
            
            # get instrument type if flowcell info in protocol
            if len(parts) >= 2 and "PRO" in parts[1]:
                metadata["instrument_type"] = "PromethION"
                # try to get model number
                model_match = re.search(r'PRO(\d+)', parts[1])
                if model_match:
                    metadata["instrument_type"] = f"PromethION {model_match.group(1)}"
    
    # if PAY flowcell but no instrument type yet
    if metadata["flowcell_id"].startswith("PAY") and ("instrument_type" not in metadata or metadata.get("instrument_type") == "Unknown"):
        metadata["instrument_type"] = "PromethION"
    
    # generate date component for ID
    date_component = "UNKNOWN"
    if metadata["run_date"] != "Unknown":
        # extract date only, remove time if present
        date_str = metadata["run_date"].split('T')[0] if 'T' in metadata["run_date"] else metadata["run_date"]
        # remove separators for YYYYMMDD
        date_component = date_str.replace('-', '').replace('/', '')
    
    # create dataset ID
    metadata["dataset_id"] = f"ONT-{metadata['flowcell_id']}-{date_component}-AREA"
    
    return metadata

# --- POD5/FASTQ Analysis Functions ---

def analyze_pod5_fastq(dirs):
    """
    compares pod5 and fastq files
    
    checks file counts, sizes, and calculates size ratio
    """
    results = {}
    
    # need pod5 dir
    if not dirs["pod5"]:
        results["status"] = "ERROR"
        results["message"] = "POD5 directory not found"
        return results
    
    # need fastq dirs
    fastq_dirs = [v for k, v in dirs.items() if k.startswith("fastq_") and v is not None]
    if not fastq_dirs:
        results["status"] = "ERROR"
        results["message"] = "No FASTQ directories found"
        return results
    
    # analyze pod5 files
    pod5_count, pod5_size = 0, 0
    pod5_other_count, pod5_other_size = 0, 0
    
    for root, _, files in os.walk(dirs["pod5"]):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path) / (1024 ** 3)  # GB
            
            if file.endswith(".pod5") and "." not in file[:-5]:  # normal pod5
                pod5_count += 1
                pod5_size += file_size
            elif ".pod5." in file:  # other pod5 formats
                pod5_other_count += 1
                pod5_other_size += file_size
    
    total_pod5_count = pod5_count + pod5_other_count
    total_pod5_size = pod5_size + pod5_other_size
    
    results["pod5"] = {
        "directory": dirs["pod5"],
        "regular_files": {
            "count": pod5_count,
            "size_gb": round(pod5_size, 2)
        },
        "other_files": {
            "count": pod5_other_count,
            "size_gb": round(pod5_other_size, 2)
        },
        "total": {
            "count": total_pod5_count,
            "size_gb": round(total_pod5_size, 2)
        }
    }
    
    # analyze fastq files
    results["fastq"] = {"directories": {}}
    total_fastq_count = 0
    total_fastq_size = 0
    
    for fastq_dir in fastq_dirs:
        dir_name = os.path.basename(fastq_dir)
        fastq_count, fastq_size = 0, 0
        
        for root, _, files in os.walk(fastq_dir):
            for file in files:
                if file.endswith('.fastq') or file.endswith('.fastq.gz'):
                    fastq_count += 1
                    file_path = os.path.join(root, file)
                    fastq_size += os.path.getsize(file_path) / (1024 ** 3)  # GB
        
        results["fastq"]["directories"][dir_name] = {
            "count": fastq_count,
            "size_gb": round(fastq_size, 2)
        }
        
        total_fastq_count += fastq_count
        total_fastq_size += fastq_size
    
    results["fastq"]["total"] = {
        "count": total_fastq_count,
        "size_gb": round(total_fastq_size, 2)
    }
    
    # calculate ratio (only regular pod5 files)
    expected_ratio = 10.8  # from ONT reference
    
    if total_fastq_size > 0:
        actual_ratio = pod5_size / total_fastq_size
        ratio_difference = abs(actual_ratio - expected_ratio) / expected_ratio * 100
        
        results["ratio_analysis"] = {
            "expected_ratio": round(expected_ratio, 1),
            "actual_ratio": round(actual_ratio, 1),
            "difference_percent": round(ratio_difference, 1),
            "within_expected_range": ratio_difference <= 15
        }
        
        # estimate flow cell output
        if total_fastq_size <= 65:
            estimate = (total_fastq_size / 65) * 100
            reference = "100 Gbases"
        elif total_fastq_size <= 130:
            estimate = (total_fastq_size / 130) * 200
            reference = "200 Gbases"
        else:
            estimate = (total_fastq_size / 188.5) * 290
            reference = "290 Gbases (TMO)"
        
        results["flow_cell_estimate"] = {
            "gbases": round(estimate, 1),
            "reference_scale": reference
        }
    
    # set status
    if "ratio_analysis" in results:
        if results["ratio_analysis"]["within_expected_range"]:
            results["status"] = "SUCCESS"
            results["message"] = "POD5 to FASTQ ratio within expected range"
        else:
            results["status"] = "WARNING"
            results["message"] = f"POD5 to FASTQ ratio differs by {results['ratio_analysis']['difference_percent']}% from expected"
    else:
        results["status"] = "WARNING"
        results["message"] = "Could not calculate POD5 to FASTQ ratio"
    
    return results

# --- Data File Analysis Functions ---

def parse_final_summary(file_path):
    """parses the final_summary.txt file"""
    metrics = {}
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            
            # extract key-value pairs
            for line in content.split('\n'):
                if "=" in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    metrics[key] = value
        
        # convert known numeric values
        numeric_keys = [
            'throughput', 'duration', 'wh_ratio', 'qscore_template', 'qscore_complement',
            'qscore_2d', 'mean_qscore_template', 'mean_qscore_complement', 'mean_qscore_2d',
            'sequences', 'sequence_length_template', 'sequence_length_complement', 'sequence_length_2d'
        ]
        
        for key in numeric_keys:
            if key in metrics:
                try:
                    metrics[key] = float(metrics[key])
                except ValueError:
                    pass
        
        # handle units for throughput
        if 'throughput' in metrics and isinstance(metrics['throughput'], str) and metrics['throughput'].lower().endswith('b'):
            try:
                # handle Gb, Mb, kb suffixes
                throughput_str = metrics['throughput'].lower().rstrip('b')
                if throughput_str.endswith('g'):
                    metrics['throughput'] = float(throughput_str.rstrip('g')) * 1e9
                elif throughput_str.endswith('m'):
                    metrics['throughput'] = float(throughput_str.rstrip('m')) * 1e6
                elif throughput_str.endswith('k'):
                    metrics['throughput'] = float(throughput_str.rstrip('k')) * 1e3
                else:
                    metrics['throughput'] = float(throughput_str)
            except (ValueError, TypeError):
                pass
                    
    except Exception as e:
        metrics['error'] = str(e)
    
    return metrics

def parse_sequencing_summary(file_path, max_rows=1000000):
    """parses the sequencing_summary.txt file (samples for large files)"""
    summary = {
        'columns': [],
        'row_count': 0,
        'sample_stats': {}
    }
    
    try:
        # get file size
        file_size = os.path.getsize(file_path)
        
        # count header and sample lines
        with open(file_path, 'r') as f:
            header = f.readline().strip().split('\t')
            summary['columns'] = header
            
            # sample lines for estimating
            sample_lines = []
            for i in range(min(1000, max_rows)):
                line = f.readline()
                if not line:
                    break
                sample_lines.append(line)
            
            if sample_lines:
                avg_line_size = sum(len(line) for line in sample_lines) / len(sample_lines)
                # estimate total rows
                estimated_rows = int((file_size - len(header)) / avg_line_size)
                summary['row_count_estimate'] = estimated_rows
            else:
                summary['row_count_estimate'] = 0
        
        # use pandas for statistics
        chunksize = min(max_rows, max(1000, int(file_size / 1e8)))
        
        # process in chunks
        all_stats = {}
        total_rows = 0
        
        for chunk in pd.read_csv(file_path, sep='\t', chunksize=chunksize):
            total_rows += len(chunk)
            
            # calculate stats on numeric columns
            numeric_columns = ['sequence_length_template', 'mean_qscore_template', 
                              'sequence_length', 'mean_qscore']
            
            for col in numeric_columns:
                if col in chunk.columns:
                    if chunk[col].dtype.kind in 'ifc':  # numeric
                        # first chunk init
                        if col not in all_stats:
                            all_stats[col] = {
                                'sum': chunk[col].sum(),
                                'count': chunk[col].count(),
                                'min': chunk[col].min(),
                                'max': chunk[col].max(),
                                'sq_sum': (chunk[col] ** 2).sum()
                            }
                        else:
                            # update stats
                            all_stats[col]['sum'] += chunk[col].sum()
                            all_stats[col]['count'] += chunk[col].count()
                            all_stats[col]['min'] = min(all_stats[col]['min'], chunk[col].min())
                            all_stats[col]['max'] = max(all_stats[col]['max'], chunk[col].max())
                            all_stats[col]['sq_sum'] += (chunk[col] ** 2).sum()
            
            # stop after processing enough
            if total_rows >= max_rows:
                break
        
        # calculate final statistics
        for col, stats in all_stats.items():
            if stats['count'] > 0:
                mean = stats['sum'] / stats['count']
                variance = (stats['sq_sum'] / stats['count']) - (mean ** 2)
                std = np.sqrt(variance) if variance > 0 else 0
                
                summary['sample_stats'][col] = {
                    'mean': float(mean),
                    'min': float(stats['min']),
                    'max': float(stats['max']),
                    'std': float(std)
                }
        
        # update row count
        if total_rows > 0:
            summary['row_count_sample'] = total_rows
            
    except Exception as e:
        summary['error'] = str(e)
    
    return summary

def calculate_n_values(lengths, weights=None, ns=[50, 90, 95]):
    """calculates n50, n90, etc. values from length array"""
    if not isinstance(lengths, np.ndarray) or len(lengths) == 0:
        return {f"N{n}": 0 for n in ns}
    
    sorted_lengths = np.sort(lengths)[::-1]  # sort descending
    
    if weights is None:
        weights = np.ones_like(sorted_lengths)
    else:
        weights = np.array(weights)[np.argsort(lengths)[::-1]]
    
    cumsum = np.cumsum(sorted_lengths * weights)
    total_length = cumsum[-1]
    
    n_values = {}
    for n in ns:
        threshold = total_length * (n / 100.0)
        n_value_index = np.searchsorted(cumsum, threshold)
        
        # check before indexing
        if n_value_index < len(sorted_lengths):
            n_values[f"N{n}"] = int(sorted_lengths[n_value_index])
        else:
            n_values[f"N{n}"] = int(sorted_lengths[-1]) if len(sorted_lengths) > 0 else 0
    
    return n_values

def analyze_read_length_distribution(summary_file, max_rows=100000):
    """analyzes read length distribution"""
    results = {}
    try:
        # read sample
        df = pd.read_csv(summary_file, sep='\t', nrows=max_rows)
        
        # find read length column
        length_cols = [col for col in df.columns if 'length' in col.lower()]
        if not length_cols:
            return {"error": "No read length column found"}
        
        length_col = length_cols[0]
        lengths = df[length_col].dropna().values
        
        if len(lengths) == 0:
            return {"error": "No valid read lengths found"}
        
        # basic statistics
        results["count"] = len(lengths)
        results["mean"] = float(np.mean(lengths))
        results["median"] = float(np.median(lengths))
        results["min"] = float(np.min(lengths))
        results["max"] = float(np.max(lengths))
        results["std"] = float(np.std(lengths))
        
        # n values
        n_values = calculate_n_values(lengths)
        results.update(n_values)
        
        # percentiles
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        results["percentiles"] = {
            f"P{p}": float(np.percentile(lengths, p)) for p in percentiles
        }
        
        # length distribution by range
        bins = [0, 1000, 5000, 10000, 25000, 50000, 100000, float('inf')]
        bin_labels = ["<1kb", "1-5kb", "5-10kb", "10-25kb", "25-50kb", "50-100kb", ">100kb"]
        
        binned = pd.cut(lengths, bins=bins, labels=bin_labels)
        distribution = binned.value_counts().sort_index()
        
        results["distribution"] = {
            str(label): int(count) for label, count in zip(distribution.index, distribution.values)
        }
        
        # percentage in each range
        results["distribution_percent"] = {
            str(label): float(count) / len(lengths) * 100 for label, count in results["distribution"].items()
        }
        
    except Exception as e:
        results["error"] = str(e)
    
    return results

def analyze_quality_distribution(summary_file, max_rows=100000):
    """analyzes quality score distribution"""
    results = {}
    try:
        # read sample
        df = pd.read_csv(summary_file, sep='\t', nrows=max_rows)
        
        # find quality column
        qscore_cols = [col for col in df.columns if ('qscore' in col.lower() or 'quality' in col.lower())]
        if not qscore_cols:
            return {"error": "No quality score column found"}
        
        qscore_col = qscore_cols[0]
        qscores = df[qscore_col].dropna().values
        
        if len(qscores) == 0:
            return {"error": "No valid quality scores found"}
        
        # basic statistics
        results["count"] = len(qscores)
        results["mean"] = float(np.mean(qscores))
        results["median"] = float(np.median(qscores))
        results["min"] = float(np.min(qscores))
        results["max"] = float(np.max(qscores))
        results["std"] = float(np.std(qscores))
        
        # quality thresholds
        thresholds = [7, 10, 12, 15, 20]
        results["above_threshold"] = {
            f"Q{t}": float(np.sum(qscores >= t) / len(qscores) * 100) for t in thresholds
        }
        
        # error probabilities
        # Q = -10 * log10(error_prob)
        mean_error_prob = 10 ** (-results["mean"] / 10)
        results["mean_error_probability"] = float(mean_error_prob)
        results["mean_accuracy"] = float(1 - mean_error_prob)
        
        # quality distribution by range
        bins = [0, 7, 10, 12, 15, 20, 30]
        bin_labels = ["<Q7", "Q7-Q10", "Q10-Q12", "Q12-Q15", "Q15-Q20", "Q20+"]
        
        binned = pd.cut(qscores, bins=bins, labels=bin_labels)
        distribution = binned.value_counts().sort_index()
        
        results["distribution"] = {
            str(label): int(count) for label, count in zip(distribution.index, distribution.values)
        }
        
        # percentage in each range
        results["distribution_percent"] = {
            str(label): float(count) / len(qscores) * 100 for label, count in results["distribution"].items()
        }
        
    except Exception as e:
        results["error"] = str(e)
    
    return results

def parse_throughput(file_path):
    """parses throughput CSV file for yield over time"""
    summary = {
        'total_yield': 0,
        'run_duration_hours': 0
    }
    
    try:
        # try with different encodings
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except:
            df = pd.read_csv(file_path, encoding='latin1')
            
        # log columns
        summary['columns'] = df.columns.tolist()
        
        # find time and yield columns
        time_cols = [col for col in df.columns if any(term in col.lower() for term in ['time', 'hour', 'duration'])]
        yield_cols = [col for col in df.columns if any(term in col.lower() for term in ['yield', 'bases', 'cumulative', 'throughput'])]
        
        if time_cols and yield_cols:
            # use likely columns
            time_col = time_cols[0]
            yield_col = yield_cols[0]
            
            # get last row
            if not df.empty:
                last_row = df.iloc[-1]
                
                # run duration
                if time_col in last_row:
                    time_val = last_row[time_col]
                    # convert seconds to hours if needed
                    if time_val > 24 and time_val < 86400:
                        summary['run_duration_hours'] = time_val / 3600
                    else:
                        summary['run_duration_hours'] = time_val
                
                # total yield
                if yield_col in last_row:
                    yield_val = last_row[yield_col]
                    if yield_val > 0:
                        summary['total_yield'] = yield_val
                        
                        # check for unit issues
                        if yield_val > 1e12:
                            summary['total_yield'] = yield_val / 1e9
                            summary['yield_unit_note'] = "Adjusted from very large value"
                            
    except Exception as e:
        summary['error'] = str(e)
    
    return summary

def check_report_json(file_path):
    """checks report JSON file for metrics"""
    metrics = {}
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # get top-level metrics
        for key in ['yield', 'throughput', 'mean_qscore', 'mean_read_length', 'active_channels']:
            if key in data:
                metrics[key] = data[key]
        
        # nested metrics
        if 'metadata' in data:
            metrics['metadata'] = data['metadata']
        
        if 'runs' in data and isinstance(data['runs'], list) and data['runs']:
            run_data = data['runs'][0]
            for key in ['yield', 'duration', 'active_channels', 'basecalled_passes']:
                if key in run_data:
                    metrics[f'run_{key}'] = run_data[key]
    except Exception as e:
        metrics['error'] = str(e)
    
    return metrics

def parse_pore_activity(file_path):
    """parses pore activity CSV file"""
    summary = {}
    
    try:
        # try different encodings
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except:
            df = pd.read_csv(file_path, encoding='latin1')
        
        # log columns
        summary['columns'] = df.columns.tolist()
        
        # check for expected columns
        if 'channel' in df.columns:
            # look for pore type column
            pore_type_cols = [col for col in df.columns if 'pore' in col.lower() and 'type' in col.lower()]
            state_cols = [col for col in df.columns if 'state' in col.lower()]
            
            pore_type_col = pore_type_cols[0] if pore_type_cols else (state_cols[0] if state_cols else None)
            
            if pore_type_col:
                # count pore types
                pore_counts = df[pore_type_col].value_counts().to_dict()
                summary['pore_counts'] = pore_counts
                
                # calculate active percentage
                total_pores = sum(pore_counts.values())
                if total_pores > 0:
                    # look for active status
                    active_keys = [k for k in pore_counts.keys() if 'active' in str(k).lower()]
                    if active_keys:
                        active_count = sum(pore_counts[k] for k in active_keys)
                        summary['active_pore_percentage'] = (active_count / total_pores) * 100
                    else:
                        # just log all states
                        summary['states'] = list(pore_counts.keys())
                
    except Exception as e:
        summary['error'] = str(e)
    
    return summary

def extract_metrics(data_files):
    """
    extracts metrics from data files
    
    combines metrics from various files into one structure
    """
    metrics = {}
    errors = []
    
    # parse final summary
    if data_files["final_summary"]:
        final_metrics = parse_final_summary(data_files["final_summary"])
        if 'error' in final_metrics:
            errors.append(f"Error parsing final summary: {final_metrics['error']}")
        else:
            metrics["final_summary"] = final_metrics
    
    # parse sequencing summary
    if data_files["sequencing_summary"]:
        seq_metrics = parse_sequencing_summary(data_files["sequencing_summary"])
        if 'error' in seq_metrics:
            errors.append(f"Error parsing sequencing summary: {seq_metrics['error']}")
        else:
            metrics["sequencing_summary"] = seq_metrics
    
    # parse pore activity
    if data_files["pore_activity"]:
        pore_metrics = parse_pore_activity(data_files["pore_activity"])
        if 'error' in pore_metrics:
            errors.append(f"Error parsing pore activity: {pore_metrics['error']}")
        else:
            metrics["pore_activity"] = pore_metrics
    
    # parse throughput
    if data_files["throughput"]:
        throughput_metrics = parse_throughput(data_files["throughput"])
        if 'error' in throughput_metrics:
            errors.append(f"Error parsing throughput: {throughput_metrics['error']}")
        else:
            metrics["throughput"] = throughput_metrics
    
    # check report JSON
    if data_files["report_json"]:
        json_metrics = check_report_json(data_files["report_json"])
        if 'error' in json_metrics:
            errors.append(f"Error parsing report JSON: {json_metrics['error']}")
        else:
            metrics["report_json"] = json_metrics
    
    return metrics, errors

# --- Advanced Assessment Functions ---

def perform_advanced_assessments(data_files):
    """
    performs advanced assessments on sequencing data
    
    analyzes read length and quality distributions
    """
    results = {}
    errors = []
    
    # need sequencing summary
    if not data_files["sequencing_summary"]:
        results["status"] = "SKIPPED"
        results["message"] = "No sequencing summary file found"
        return results, ["No sequencing summary file found for advanced assessments"]
    
    # read length analysis
    length_analysis = analyze_read_length_distribution(data_files["sequencing_summary"])
    if "error" in length_analysis:
        errors.append(f"Error in read length analysis: {length_analysis['error']}")
        results["read_length_status"] = "ERROR"
    else:
        results["read_length_analysis"] = length_analysis
        results["read_length_status"] = "SUCCESS"
    
    # quality analysis
    quality_analysis = analyze_quality_distribution(data_files["sequencing_summary"])
    if "error" in quality_analysis:
        errors.append(f"Error in quality score analysis: {quality_analysis['error']}")
        results["quality_status"] = "ERROR"
    else:
        results["quality_analysis"] = quality_analysis
        results["quality_status"] = "SUCCESS"
    
    # overall status
    if "ERROR" in [results.get("read_length_status"), results.get("quality_status")]:
        results["status"] = "WARNING"
        results["message"] = "Some advanced assessments encountered errors"
    else:
        results["status"] = "SUCCESS"
        results["message"] = "Advanced assessments completed successfully"
    
    return results, errors

# --- FAIR Enhancement Functions ---

def enhance_fair_compliance(directory, metrics=None, kpis=None, metadata=None, data_files=None):
    """enhances FAIR compliance with README and metadata files"""
    results = {}
    errors = []
    
    try:
        # get run metadata
        run_metadata = extract_run_metadata(data_files, os.path.basename(directory))
        flowcell_id = run_metadata["flowcell_id"]
        run_date = run_metadata["run_date"]
        dataset_id = run_metadata["dataset_id"]
        
        # calculate checksums
        checksums = {}
        key_extensions = ('.txt', '.csv', '.json', '.html')
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(key_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        md5 = hashlib.md5()
                        with open(file_path, 'rb') as f:
                            for chunk in iter(lambda: f.read(4096), b''):
                                md5.update(chunk)
                        checksums[os.path.relpath(file_path, directory)] = md5.hexdigest()
                    except Exception as e:
                        errors.append(f"Error calculating checksum for {file}: {str(e)}")
        
        results["checksums"] = checksums
        
        # create metadata
        experiment_metadata = {
            "dataset_id": dataset_id,
            "created_date": datetime.datetime.now().isoformat(),
            "flowcell_id": flowcell_id,
            "run_date": run_date,
            "institution": "AREA Science Park",
            "copyright": f"© {datetime.datetime.now().year} AREA Science Park",
            "license": "CC-BY-4.0"
        }
        
        # add instrument type if known
        if "instrument_type" in run_metadata and run_metadata["instrument_type"] != "Unknown":
            experiment_metadata["instrument_type"] = run_metadata["instrument_type"]
        
        # add protocol if known
        if run_metadata["protocol"] != "Unknown":
            experiment_metadata["protocol"] = run_metadata["protocol"]
        
        # add sample ID if known
        if run_metadata["sample_id"] != "Unknown":
            experiment_metadata["sample_id"] = run_metadata["sample_id"]
        
        # add sequencing kit if extracted
        if "sequencing_kit" in run_metadata and run_metadata["sequencing_kit"] != "Unknown":
            experiment_metadata["sequencing_kit"] = run_metadata["sequencing_kit"]
        
        # add KPIs if available
        if kpis:
            experiment_metadata["sequencing_metrics"] = {
                "total_yield_bases": kpis.get("total_yield", 0),
                "read_count": kpis.get("read_count", 0),
                "mean_read_length": kpis.get("mean_read_length", 0),
                "mean_qscore": kpis.get("mean_qscore", 0),
                "run_duration_hours": kpis.get("run_duration_hours", 0)
            }
        
        # add user metadata if available
        if metadata:
            experiment_metadata.update(metadata)
        
        results["metadata"] = experiment_metadata
        results["dataset_identifier"] = dataset_id
        
        # create README content
        readme_content = f"""# Oxford Nanopore Sequencing Data: {flowcell_id}

## Run Information
- **Dataset ID**: {dataset_id}
- **Flowcell ID**: {flowcell_id}
- **Run Date**: {run_date}
"""

        # add optional metadata
        if "instrument_type" in experiment_metadata:
            readme_content += f"- **Instrument Type**: {experiment_metadata['instrument_type']}\n"
        
        if "protocol" in experiment_metadata:
            readme_content += f"- **Protocol**: {experiment_metadata['protocol']}\n"
            
        if "sample_id" in experiment_metadata:
            readme_content += f"- **Sample ID**: {experiment_metadata['sample_id']}\n"
            
        if "sequencing_kit" in experiment_metadata:
            readme_content += f"- **Sequencing Kit**: {experiment_metadata['sequencing_kit']}\n"
            
        # add standard metadata
        readme_content += f"""- **Analysis Date**: {datetime.datetime.now().strftime('%Y-%m-%d')}
- **Institution**: AREA Science Park
- **License**: {experiment_metadata['license']}

## Sequencing Summary
"""
        # add KPIs to README
        if kpis:
            yield_gb = kpis.get("total_yield", 0) / 1e9
            readme_content += f"""
- **Total Yield**: {yield_gb:.2f} Gb
- **Read Count**: {kpis.get("read_count", 0):,.0f}
- **Mean Read Length**: {kpis.get("mean_read_length", 0):,.0f} bases
- **Mean Quality Score**: {kpis.get("mean_qscore", 0):.1f}
"""

        # dataset contents
        readme_content += f"""
## Dataset Contents

This directory contains a complete Oxford Nanopore sequencing dataset:

### Raw Data
- **POD5 Files**: Raw signal data (.pod5)
- **FASTQ Files**: Base-called sequence data (.fastq/.fastq.gz)
  - `fastq_pass/`: Sequences that passed quality filters
  - `fastq_fail/`: Sequences that failed quality filters

### Metadata & Reports
- **Summary Files**: Statistical information about the run
  - `final_summary_*.txt`: Overall run metrics
  - `sequencing_summary_*.txt`: Per-read metrics
- **Report Files**: Interactive data visualization
  - `report_*.html`: Web-based report
  - `report_*.json`: Data for the report

### Quality Control
- `qc_report.json`: Comprehensive QC analysis results
- `checksums.md5`: MD5 checksums for data integrity verification

## Data Usage

This dataset has been analyzed and enhanced using the ONT_Integrated_Analyzer tool.
For optimal analysis of these data, we recommend:

1. Assess sequence quality using the provided QC metrics
2. Consider read length distribution when planning analyses
3. Verify data integrity using the provided checksums

## Data Access

For questions about this dataset, please contact:
AREA Science Park - {experiment_metadata.get('contact_email', 'info@areasciencepark.it')}

{experiment_metadata['copyright']}
"""
        
        results["readme_content"] = readme_content
        
        # write files for FAIR compliance
        with open(os.path.join(directory, "README.md"), 'w') as f:
            f.write(readme_content)
        
        # convert NumPy types to Python types for JSON
        python_metadata = numpy_to_python_type(experiment_metadata)
        with open(os.path.join(directory, "metadata.json"), 'w') as f:
            json.dump(python_metadata, f, indent=2)
        
        with open(os.path.join(directory, "checksums.md5"), 'w') as f:
            for file_path, checksum in checksums.items():
                f.write(f"{checksum}  {file_path}\n")
        
        results["status"] = "SUCCESS"
        results["message"] = "FAIR compliance enhanced successfully"
    except Exception as e:
        results["status"] = "ERROR"
        results["message"] = f"Error enhancing FAIR compliance: {str(e)}"
        errors.append(f"FAIR enhancement error: {str(e)}")
    
    return results, errors

# --- Main Analysis Functions ---

def extract_kpis(metrics):
    """
    extracts key performance indicators from metrics
    
    combines metrics from different sources to get key values
    """
    kpis = {}
    
    # total yield from various sources
    if "report_json" in metrics and "yield" in metrics["report_json"]:
        kpis["total_yield"] = metrics["report_json"]["yield"]
    elif "report_json" in metrics and "throughput" in metrics["report_json"]:
        kpis["total_yield"] = metrics["report_json"]["throughput"]
    elif "throughput" in metrics and metrics["throughput"]["total_yield"] > 0:
        kpis["total_yield"] = metrics["throughput"]["total_yield"]
    elif "final_summary" in metrics and "throughput" in metrics["final_summary"]:
        kpis["total_yield"] = metrics["final_summary"]["throughput"]
    
    # read count from various sources
    if "report_json" in metrics and "basecalled_passes" in metrics["report_json"]:
        kpis["read_count"] = metrics["report_json"]["basecalled_passes"]
    elif "report_json" in metrics and "run_basecalled_passes" in metrics["report_json"]:
        kpis["read_count"] = metrics["report_json"]["run_basecalled_passes"]
    elif "final_summary" in metrics and "sequences" in metrics["final_summary"]:
        kpis["read_count"] = metrics["final_summary"]["sequences"]
    elif "sequencing_summary" in metrics:
        if "row_count_sample" in metrics["sequencing_summary"]:
            kpis["read_count"] = metrics["sequencing_summary"]["row_count_sample"]
            kpis["read_count_note"] = "Based on sampled rows"
        elif "row_count_estimate" in metrics["sequencing_summary"]:
            # sanity check - typical ONT runs have <10M reads
            est_count = metrics["sequencing_summary"]["row_count_estimate"]
            if est_count > 10000000:  # suspiciously high
                kpis["read_count"] = est_count / 1000  # adjust down
                kpis["read_count_note"] = "Estimated and adjusted (original estimate was very high)"
            else:
                kpis["read_count"] = est_count
                kpis["read_count_note"] = "Estimated from file size"
    
    # run duration
    if "report_json" in metrics and "run_duration" in metrics["report_json"]:
        kpis["run_duration_hours"] = metrics["report_json"]["run_duration"] / 3600 if metrics["report_json"]["run_duration"] > 3600 else metrics["report_json"]["run_duration"]
    elif "throughput" in metrics and metrics["throughput"]["run_duration_hours"] > 0:
        kpis["run_duration_hours"] = metrics["throughput"]["run_duration_hours"]
    elif "final_summary" in metrics and "duration" in metrics["final_summary"]:
        # convert to hours if in seconds
        duration = metrics["final_summary"]["duration"]
        kpis["run_duration_hours"] = duration / 3600 if duration > 24 else duration
    
    # mean read length
    if "report_json" in metrics and "mean_read_length" in metrics["report_json"]:
        kpis["mean_read_length"] = metrics["report_json"]["mean_read_length"]
    elif "sequencing_summary" in metrics and "sample_stats" in metrics["sequencing_summary"]:
        stats = metrics["sequencing_summary"]["sample_stats"]
        if "sequence_length_template" in stats:
            kpis["mean_read_length"] = stats["sequence_length_template"]["mean"]
        elif "sequence_length" in stats:
            kpis["mean_read_length"] = stats["sequence_length"]["mean"]
    elif "final_summary" in metrics and "sequence_length_template" in metrics["final_summary"]:
        kpis["mean_read_length"] = metrics["final_summary"]["sequence_length_template"]
    
    # mean quality score
    if "report_json" in metrics and "mean_qscore" in metrics["report_json"]:
        kpis["mean_qscore"] = metrics["report_json"]["mean_qscore"]
    elif "sequencing_summary" in metrics and "sample_stats" in metrics["sequencing_summary"]:
        stats = metrics["sequencing_summary"]["sample_stats"]
        if "mean_qscore_template" in stats:
            kpis["mean_qscore"] = stats["mean_qscore_template"]["mean"]
        elif "mean_qscore" in stats:
            kpis["mean_qscore"] = stats["mean_qscore"]["mean"]
    elif "final_summary" in metrics and "mean_qscore_template" in metrics["final_summary"]:
        kpis["mean_qscore"] = metrics["final_summary"]["mean_qscore_template"]
    
    # active pore percentage
    if "report_json" in metrics and "active_channels" in metrics["report_json"]:
        # typical flowcells have 512, 1024, or 2048 channels
        active = metrics["report_json"]["active_channels"]
        total = 2048  # assume R9/R10 flowcell
        kpis["active_pore_percentage"] = (active / total) * 100
    elif "pore_activity" in metrics and "active_pore_percentage" in metrics["pore_activity"]:
        kpis["active_pore_percentage"] = metrics["pore_activity"]["active_pore_percentage"]
    
    # sanity checks
    if "read_count" in kpis and kpis["read_count"] > 100000000:  # too high
        kpis["read_count"] = kpis["read_count"] / 1000
        kpis["read_count_note"] = "Adjusted due to unrealistically high value"
    
    if "total_yield" in kpis:
        # typical range is millions to billions
        if kpis["total_yield"] < 1000 and "read_count" in kpis and kpis["read_count"] > 1000:
            # yield too low but read count good
            if "mean_read_length" in kpis:
                # estimate from count and length
                kpis["total_yield"] = kpis["read_count"] * kpis["mean_read_length"]
                kpis["total_yield_note"] = "Estimated from read count and mean length"
            else:
                # use typical average
                kpis["total_yield"] = kpis["read_count"] * 10000  # assume 10kb
                kpis["total_yield_note"] = "Estimated from read count with assumed average length"
    
    return kpis

def assess_run_quality(kpis, advanced_assessments=None):
    """
    assesses run quality based on key performance indicators
    
    checks yield, quality scores, pore activity, etc.
    """
    assessment = {
        "status": "UNKNOWN",
        "messages": [],
        "flags": []
    }
    
    # check for enough metrics
    if not kpis:
        assessment["status"] = "WARNING"
        assessment["messages"].append("Could not extract enough metrics for quality assessment")
        return assessment
    
    flags = []
    
    # check yield
    if "total_yield" in kpis and kpis["total_yield"] > 0:
        yield_gb = kpis["total_yield"] / 1e9
        if yield_gb >= 10:
            flags.append(("yield", "GOOD", f"Total yield: {yield_gb:.2f} Gb"))
        elif yield_gb >= 5:
            flags.append(("yield", "ACCEPTABLE", f"Total yield: {yield_gb:.2f} Gb"))
        else:
            flags.append(("yield", "POOR", f"Low total yield: {yield_gb:.2f} Gb (insufficient for many applications)"))
    
    # check quality score
    if "mean_qscore" in kpis:
        qscore = kpis["mean_qscore"]
        if qscore >= 12:
            flags.append(("mean_qscore", "GOOD", f"Mean Q-score: {qscore:.1f}"))
        elif qscore >= 9:
            flags.append(("mean_qscore", "ACCEPTABLE", f"Mean Q-score: {qscore:.1f}"))
        else:
            flags.append(("mean_qscore", "POOR", f"Low mean Q-score: {qscore:.1f} (high error rate)"))
    
    # check pore activity
    if "active_pore_percentage" in kpis:
        pore_pct = kpis["active_pore_percentage"]
        if pore_pct >= 70:
            flags.append(("active_pores", "GOOD", f"Active pore percentage: {pore_pct:.1f}%"))
        elif pore_pct >= 50:
            flags.append(("active_pores", "ACCEPTABLE", f"Active pore percentage: {pore_pct:.1f}%"))
        else:
            flags.append(("active_pores", "POOR", f"Low active pore percentage: {pore_pct:.1f}% (inefficient flowcell usage)"))
    
    # check read length
    if "mean_read_length" in kpis:
        read_len = kpis["mean_read_length"]
        if read_len >= 10000:
            flags.append(("read_length", "GOOD", f"Mean read length: {read_len:.0f} bases"))
        elif read_len >= 5000:
            flags.append(("read_length", "ACCEPTABLE", f"Mean read length: {read_len:.0f} bases"))
        else:
            flags.append(("read_length", "POOR", f"Low mean read length: {read_len:.0f} bases (possibly degraded sample)"))
    
    # check N50
    if advanced_assessments and "read_length_analysis" in advanced_assessments and "N50" in advanced_assessments["read_length_analysis"]:
        n50 = advanced_assessments["read_length_analysis"]["N50"]
        if n50 >= 15000:
            flags.append(("n50", "GOOD", f"N50 read length: {n50:,} bases"))
        elif n50 >= 8000:
            flags.append(("n50", "ACCEPTABLE", f"N50 read length: {n50:,} bases"))
        else:
            flags.append(("n50", "POOR", f"Low N50 read length: {n50:,} bases (suboptimal for assembly)"))
    
    # check high quality percentage
    if advanced_assessments and "quality_analysis" in advanced_assessments and "above_threshold" in advanced_assessments["quality_analysis"]:
        q10_pct = advanced_assessments["quality_analysis"]["above_threshold"].get("Q10", 0)
        if q10_pct >= 80:
            flags.append(("high_quality_reads", "GOOD", f"High quality reads (Q≥10): {q10_pct:.1f}%"))
        elif q10_pct >= 60:
            flags.append(("high_quality_reads", "ACCEPTABLE", f"High quality reads (Q≥10): {q10_pct:.1f}%"))
        else:
            flags.append(("high_quality_reads", "POOR", f"Low percentage of high quality reads (Q≥10): {q10_pct:.1f}% (accuracy concerns)"))
    
    # store flags
    assessment["flags"] = flags
    
    # determine overall status
    status_counts = {"GOOD": 0, "ACCEPTABLE": 0, "POOR": 0}
    for _, status, _ in flags:
        status_counts[status] += 1
    
    if status_counts["POOR"] > 0:
        assessment["status"] = "WARNING"
        assessment["messages"].append("Some metrics indicate potential issues with this sequencing run")
    elif status_counts["GOOD"] >= 2:
        assessment["status"] = "SUCCESS"
        assessment["messages"].append("Metrics indicate a successful sequencing run")
    else:
        assessment["status"] = "ACCEPTABLE"
        assessment["messages"].append("Metrics indicate an acceptable sequencing run")
    
    return assessment

def analyze_other_reports(parent_dir):
    """analyzes files in the other_reports folder"""
    results = {}
    errors = []
    
    # find other_reports folder
    other_reports_dir = os.path.join(parent_dir, "other_reports")
    
    if not os.path.isdir(other_reports_dir):
        # try subdirectories
        for item in os.listdir(parent_dir):
            potential_path = os.path.join(parent_dir, item, "other_reports")
            if os.path.isdir(potential_path):
                other_reports_dir = potential_path
                break
        else:
            return {}, ["Other reports folder not found"]
    
    results["directory"] = other_reports_dir
    results["files"] = {}
    
    # process each file
    for filename in os.listdir(other_reports_dir):
        file_path = os.path.join(other_reports_dir, filename)
        file_size = os.path.getsize(file_path) / 1024  # KB
        
        if "temperature" in filename.lower() and filename.endswith(".csv"):
            temp_data = analyze_temperature_file(file_path)
            if "error" in temp_data:
                errors.append(f"Error analyzing temperature file: {temp_data['error']}")
            else:
                results["temperature_data"] = temp_data
                results["files"]["temperature"] = {
                    "filename": filename,
                    "size_kb": round(file_size, 2)
                }
        
        elif "pore_scan" in filename.lower() and filename.endswith(".csv"):
            pore_data = analyze_pore_scan_file(file_path)
            if "error" in pore_data:
                errors.append(f"Error analyzing pore scan file: {pore_data['error']}")
            else:
                results["pore_scan_data"] = pore_data
                results["files"]["pore_scan"] = {
                    "filename": filename,
                    "size_kb": round(file_size, 2)
                }
    
    return results, errors

def analyze_temperature_file(file_path):
    """analyzes temperature adjustment data file"""
    results = {}
    
    try:
        df = pd.read_csv(file_path)
        
        # basic info
        results["shape"] = {"rows": df.shape[0], "columns": df.shape[1]}
        results["columns"] = df.columns.tolist()
        
        # extract temp columns
        temp_cols = [col for col in df.columns if 'temp' in col.lower()]
        
        if temp_cols:
            results["temperature_columns"] = {}
            
            for col in temp_cols:
                results["temperature_columns"][col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean())
                }
            
            # generate temp profile
            if df.shape[0] > 0:
                results["temperature_profile"] = {
                    "duration": df["acquisition_duration"].iloc[-1] if "acquisition_duration" in df.columns else None,
                    "initial_temperature": df[temp_cols[0]].iloc[0] if df.shape[0] > 0 else None,
                    "final_temperature": df[temp_cols[0]].iloc[-1] if df.shape[0] > 0 else None,
                    "adjustment_count": df.shape[0]
                }
            
            # try to generate plot
            try:
                plt.figure(figsize=(10, 6))
                for col in temp_cols:
                    plt.plot(df["acquisition_duration"] if "acquisition_duration" in df.columns else range(len(df)), 
                             df[col], label=col)
                plt.title('Temperature Profile')
                plt.xlabel('Acquisition Duration (s)')
                plt.ylabel('Temperature (°C)')
                plt.legend()
                plot_path = os.path.join(os.path.dirname(file_path), 'temperature_plot.png')
                plt.savefig(plot_path)
                plt.close()
                results["temperature_plot"] = plot_path
            except Exception as e:
                results["plot_error"] = str(e)
    
    except Exception as e:
        results["error"] = str(e)
    
    return results

def analyze_pore_scan_file(file_path):
    """analyzes pore scan data file"""
    results = {}
    
    try:
        # just read header and sample for large files
        df_sample = pd.read_csv(file_path, nrows=5000)
        
        # basic info
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        results["file_size_mb"] = round(file_size_mb, 2)
        results["sample_shape"] = {"rows": df_sample.shape[0], "columns": df_sample.shape[1]}
        results["columns"] = df_sample.columns.tolist()
        
        # count total rows efficiently
        line_count = 0
        with open(file_path, 'r') as f:
            # skip header
            next(f)
            for _ in f:
                line_count += 1
        results["total_rows"] = line_count
        
        # pore stats
        if "pore" in df_sample.columns:
            pore_stats = df_sample["pore"].value_counts(normalize=True) * 100
            results["pore_distribution"] = {
                str(k): float(v) for k, v in pore_stats.items() if not pd.isna(k)
            }
            
        # channel stats
        if "channel" in df_sample.columns and df_sample["channel"].nunique() > 0:
            results["channel_stats"] = {
                "unique_channels": df_sample["channel"].nunique(),
                "min_channel": int(df_sample["channel"].min()),
                "max_channel": int(df_sample["channel"].max())
            }
            
        # count active pores
        if "pore" in df_sample.columns:
            active_pores = df_sample[df_sample["pore"] > 0]["channel"].nunique()
            total_channels = df_sample["channel"].nunique()
            if total_channels > 0:
                results["active_pore_percentage"] = round((active_pores / total_channels) * 100, 2)
    
    except Exception as e:
        results["error"] = str(e)
    
    return results

def analyze_nanopore_data(parent_dir, enhance_fair=True, metadata=None, output_file=None):
    """
    performs comprehensive analysis of nanopore data
    
    processes all files, extracts metrics, and generates reports
    """
    # start timing
    start_time = time.time()
    
    # init results
    results = OrderedDict()
    results["metadata"] = {
        "timestamp": datetime.datetime.now().isoformat(),
        "script_version": "2.1.1",
        "parent_directory": os.path.abspath(parent_dir)
    }
    
    # find directories
    dirs = find_pod5_fastq_dirs(parent_dir)
    results["directories"] = {k: v for k, v in dirs.items()}
    
    # check parent dir
    if not os.path.isdir(parent_dir):
        results["status"] = "ERROR"
        results["message"] = f"Parent directory '{parent_dir}' does not exist"
        return results
    
    # find report directory (may be different from parent)
    report_dir = parent_dir
    for item in os.listdir(parent_dir):
        item_path = os.path.join(parent_dir, item)
        if os.path.isdir(item_path) and any(f.endswith(('.html', '.json')) and 'report' in f for f in os.listdir(item_path)):
            report_dir = item_path
            break
    
    results["report_directory"] = report_dir
    
    # find data files
    data_files = find_data_files(report_dir)
    results["data_files"] = {k: os.path.basename(v) if v else None for k, v in data_files.items()}
    
    # pod5/fastq analysis
    pod5_fastq_results = analyze_pod5_fastq(dirs)
    results["pod5_fastq_analysis"] = pod5_fastq_results
    
    # extract metrics
    metrics, extract_errors = extract_metrics(data_files)
    results["metrics"] = metrics
    
    # extract kpis
    kpis = extract_kpis(metrics)
    results["kpis"] = kpis
    
    # advanced assessments
    advanced_assessments, advanced_errors = perform_advanced_assessments(data_files)
    results["advanced_assessments"] = advanced_assessments
    
    # assess quality
    assessment = assess_run_quality(kpis, advanced_assessments)
    results["assessment"] = assessment
    
    # collect errors
    all_errors = extract_errors + advanced_errors
    if all_errors:
        results["errors"] = all_errors
    
    # enhance FAIR if requested
    if enhance_fair:
        fair_results, fair_errors = enhance_fair_compliance(report_dir, metrics, kpis, metadata, data_files)
        results["fair_enhancement"] = fair_results
        if fair_errors:
            if "errors" in results:
                results["errors"].extend(fair_errors)
            else:
                results["errors"] = fair_errors
    
    # overall status
    if "ERROR" in [pod5_fastq_results.get("status"), advanced_assessments.get("status")]:
        results["status"] = "ERROR"
        results["message"] = "Critical errors occurred during analysis"
    elif all_errors:
        results["status"] = "WARNING"
        results["message"] = f"Analysis completed with {len(all_errors)} non-critical errors"
    else:
        results["status"] = assessment["status"]
        results["message"] = assessment["messages"][0] if assessment["messages"] else "Analysis completed successfully"
    
    # write results to file if requested
    if output_file:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # convert numpy types
        python_results = numpy_to_python_type(results)
        with open(output_file, 'w') as f:
            json.dump(python_results, f, indent=2)

    # analyze other_reports
    other_reports_results, other_reports_errors = analyze_other_reports(parent_dir)
    if other_reports_results:
        results["other_reports"] = other_reports_results
    if other_reports_errors:
        all_errors.extend(other_reports_errors)
    
    # extract temp data for quality
    if "other_reports" in results and "temperature_data" in results["other_reports"]:
        temp_data = results["other_reports"]["temperature_data"]
        if "temperature_columns" in temp_data:
            for col_name, stats in temp_data["temperature_columns"].items():
                # add to kpis
                if "current_target_temperature" in col_name:
                    kpis["temperature"] = stats["mean"]
                    if stats["max"] - stats["min"] > 1.0:  # variation > 1°C
                        kpis["temperature_stability"] = "unstable"
                    else:
                        kpis["temperature_stability"] = "stable"
        
        # include temp plot if available
        if "temperature_plot" in temp_data and enhance_fair:
            # add reference for FAIR
            results["temperature_plot"] = os.path.basename(temp_data["temperature_plot"])

    # timing
    end_time = time.time()
    execution_time = end_time - start_time
    results["performance"] = {
        "execution_time_seconds": round(execution_time, 2)
    }
    
    print(f"Analysis completed in {execution_time:.2f} seconds")
    return results

# --- Print Results Function ---
def print_results(results):
    """prints analysis results in readable format"""
    # color codes for terminal
    try:
        BOLD = "\033[1m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RED = "\033[31m"
        BLUE = "\033[34m"
        CYAN = "\033[36m"
        RESET = "\033[0m"
        SECTION = BLUE
        HEADER = CYAN + BOLD
        colors_supported = True
    except:
        # fallback if no color support
        BOLD = GREEN = YELLOW = RED = BLUE = CYAN = RESET = SECTION = HEADER = ""
        colors_supported = False
    
    # status icons
    SUCCESS_ICON = "✓ " if colors_supported else "[OK] "
    WARNING_ICON = "⚠ " if colors_supported else "[WARNING] "
    ERROR_ICON = "✗ " if colors_supported else "[ERROR] "
    INFO_ICON = "ℹ " if colors_supported else "[INFO] "
    
    # status color mapping
    status_format = {
        "SUCCESS": GREEN + SUCCESS_ICON,
        "WARNING": YELLOW + WARNING_ICON,
        "ERROR": RED + ERROR_ICON,
        "GOOD": GREEN + SUCCESS_ICON,
        "ACCEPTABLE": YELLOW + WARNING_ICON,
        "POOR": RED + ERROR_ICON,
        "INFO": BLUE + INFO_ICON
    }
    
    # header
    print("\n" + "═" * 80)
    print(f"{HEADER}               OXFORD NANOPORE DATA ANALYSIS REPORT{RESET}")
    print(f"{HEADER}                  AREA Science Park © 2025{RESET}")
    print("═" * 80)
    
    # summary status
    status_color = status_format.get(results['status'], "")
    print(f"\n{status_color}{results['status']}{RESET}: {results['message']}")
    print(f"Analysis Time: {results['metadata']['timestamp']}")
    print(f"Directory: {results['metadata']['parent_directory']}")
    
    # files analyzed
    print(f"\n{SECTION}┌{'─' * 78}┐{RESET}")
    print(f"{SECTION}│{BOLD} DATA FILES ANALYZED{' ' * 59}│{RESET}")
    print(f"{SECTION}└{'─' * 78}┘{RESET}")
    
    for file_type, file_name in results.get("data_files", {}).items():
        status = "Found" if file_name else "Not found"
        status_icon = SUCCESS_ICON if file_name else ERROR_ICON
        print(f"{status_icon}{file_type}: {status}")
        if file_name:
            print(f"  {file_name}")
    
    # pod5/fastq comparison
    if "pod5_fastq_analysis" in results:
        pod5_fastq = results["pod5_fastq_analysis"]
        
        print(f"\n{SECTION}┌{'─' * 78}┐{RESET}")
        print(f"{SECTION}│{BOLD} POD5/FASTQ COMPARISON{' ' * 57}│{RESET}")
        print(f"{SECTION}└{'─' * 78}┘{RESET}")
        
        # pod5 info
        if "pod5" in pod5_fastq:
            pod5 = pod5_fastq["pod5"]
            print(f"{BOLD}POD5 files:{RESET} {pod5['total']['count']} files ({pod5['total']['size_gb']:.2f} GB)")
            print(f"  Regular .pod5: {pod5['regular_files']['count']} files ({pod5['regular_files']['size_gb']:.2f} GB)")
            print(f"  Other .pod5.*: {pod5['other_files']['count']} files ({pod5['other_files']['size_gb']:.2f} GB)")
        
        # fastq info
        if "fastq" in pod5_fastq:
            fastq = pod5_fastq["fastq"]
            if "total" in fastq:
                print(f"\n{BOLD}FASTQ files:{RESET} {fastq['total']['count']} files ({fastq['total']['size_gb']:.2f} GB)")
            
            # print by directory
            if "directories" in fastq:
                for dir_name, info in fastq["directories"].items():
                    print(f"  {dir_name}: {info['count']} files ({info['size_gb']:.2f} GB)")
        
        # ratio info
        if "ratio_analysis" in pod5_fastq:
            ratio = pod5_fastq["ratio_analysis"]
            print(f"\n{BOLD}POD5:FASTQ Size Ratio:{RESET} {ratio['actual_ratio']}:1 (Expected: {ratio['expected_ratio']}:1)")
            if ratio["within_expected_range"]:
                print(f"  {GREEN}✓ Ratio within expected range{RESET}")
            else:
                print(f"  {YELLOW}⚠ Ratio differs by {ratio['difference_percent']}% from expected{RESET}")
        
        # flow cell estimate
        if "flow_cell_estimate" in pod5_fastq:
            est = pod5_fastq["flow_cell_estimate"]
            print(f"\n{BOLD}Estimated flow cell output:{RESET} {est['gbases']} Gbases")
            print(f"  (based on {est['reference_scale']} scale)")
    
    # key performance indicators
    print(f"\n{SECTION}┌{'─' * 78}┐{RESET}")
    print(f"{SECTION}│{BOLD} KEY PERFORMANCE INDICATORS{' ' * 54}│{RESET}")
    print(f"{SECTION}└{'─' * 78}┘{RESET}")
    
    if "kpis" in results:
        kpis = results["kpis"]
        
        if "total_yield" in kpis:
            if kpis["total_yield"] >= 1e9:
                yield_str = f"{kpis['total_yield']/1e9:,.2f} Gb"
            elif kpis["total_yield"] >= 1e6:
                yield_str = f"{kpis['total_yield']/1e6:,.2f} Mb"
            else:
                yield_str = f"{kpis['total_yield']:,.0f} bases"
            print(f"{BOLD}Total Yield:{RESET} {yield_str}")
            if "total_yield_note" in kpis:
                print(f"  {BLUE}Note:{RESET} {kpis['total_yield_note']}")
        
        if "read_count" in kpis:
            print(f"{BOLD}Read Count:{RESET} {kpis['read_count']:,.0f} reads")
            if "read_count_note" in kpis:
                print(f"  {BLUE}Note:{RESET} {kpis['read_count_note']}")
        
        if "mean_read_length" in kpis:
            print(f"{BOLD}Mean Read Length:{RESET} {kpis['mean_read_length']:,.0f} bases")
        
        if "mean_qscore" in kpis:
            print(f"{BOLD}Mean Q-score:{RESET} {kpis['mean_qscore']:.1f}")
        
        if "run_duration_hours" in kpis:
            print(f"{BOLD}Run Duration:{RESET} {kpis['run_duration_hours']:.1f} hours")
            print(f"  {BLUE}Note:{RESET} This likely refers to the basecalling process, not the sequencing run")
        
        if "active_pore_percentage" in kpis:
            print(f"{BOLD}Active Pore Percentage:{RESET} {kpis['active_pore_percentage']:.1f}%")
    else:
        print("  No KPIs could be extracted")
    
    # advanced assessments
    if "advanced_assessments" in results:
        advanced = results["advanced_assessments"]
        
        if "quality_analysis" in advanced and "above_threshold" in advanced["quality_analysis"]:
            print(f"\n{BOLD}Quality Distribution:{RESET}")
            quality = advanced["quality_analysis"]
            for threshold, percent in quality["above_threshold"].items():
                print(f"  {threshold}+ reads: {percent:.1f}%")
            
            if "mean_accuracy" in quality:
                print(f"{BOLD}Mean base-calling accuracy:{RESET} {quality['mean_accuracy']*100:.2f}%")
        
        if "read_length_analysis" in advanced and "N50" in advanced["read_length_analysis"]:
            print(f"\n{BOLD}Advanced Read Metrics:{RESET}")
            length = advanced["read_length_analysis"]
            print(f"  N50 Read Length: {length['N50']:,} bases")
            
            if "distribution_percent" in length:
                print(f"\n{BOLD}Read Length Distribution:{RESET}")
                for length_range, percent in length["distribution_percent"].items():
                    print(f"  {length_range}: {percent:.1f}%")
    
    # quality assessment
    if "assessment" in results and "flags" in results["assessment"]:
        print(f"\n{SECTION}┌{'─' * 78}┐{RESET}")
        print(f"{SECTION}│{BOLD} QUALITY ASSESSMENT{' ' * 61}│{RESET}")
        print(f"{SECTION}└{'─' * 78}┘{RESET}")
        
        for metric, status, message in results["assessment"]["flags"]:
            status_icon = status_format.get(status, "")
            print(f"{status_icon}{message}{RESET}")
    
    # FAIR enhancement
    if "fair_enhancement" in results:
        fair = results["fair_enhancement"]
        print(f"\n{SECTION}┌{'─' * 78}┐{RESET}")
        print(f"{SECTION}│{BOLD} FAIR ENHANCEMENT{' ' * 63}│{RESET}")
        print(f"{SECTION}└{'─' * 78}┘{RESET}")
        
        status_icon = status_format.get(fair.get('status', 'INFO'), INFO_ICON)
        print(f"{status_icon}{fair.get('message', 'No message')}{RESET}")
        
        if "dataset_identifier" in fair:
            print(f"{BOLD}Dataset ID:{RESET} {fair['dataset_identifier']}")
        
        print(f"{BOLD}FAIR Files Created:{RESET}")
        print("  - README.md")
        print("  - metadata.json")
        print("  - checksums.md5")
    
    # other reports
    if "other_reports" in results:
        other = results["other_reports"]
        print(f"\n{SECTION}┌{'─' * 78}┐{RESET}")
        print(f"{SECTION}│{BOLD} AUXILIARY DATA ANALYSIS{' ' * 56}│{RESET}")
        print(f"{SECTION}└{'─' * 78}┘{RESET}")
    
        if "files" in other:
            print(f"{BOLD}Auxiliary files found:{RESET}")
            for file_type, file_info in other["files"].items():
                print(f"  • {file_type}: {file_info['filename']} ({file_info['size_kb']} KB)")
    
        if "temperature_data" in other:
            temp = other["temperature_data"]
            print(f"\n{BOLD}Temperature Data:{RESET}")
        
            if "temperature_columns" in temp:
                for col, stats in temp["temperature_columns"].items():
                    print(f"  {col}: {stats['min']:.2f}°C to {stats['max']:.2f}°C (avg: {stats['mean']:.2f}°C)")
        
            if "temperature_profile" in temp:
                profile = temp["temperature_profile"]
                if profile["duration"]:
                    print(f"  Temperature adjusted {profile['adjustment_count']} times over {profile['duration']} seconds")
                if "temperature_plot" in temp:
                    print(f"  Temperature plot saved: {os.path.basename(temp['temperature_plot'])}")
    
        if "pore_scan_data" in other:
            pore = other["pore_scan_data"]
            print(f"\n{BOLD}Pore Scan Data:{RESET}")
            print(f"  File size: {pore['file_size_mb']} MB with {pore['total_rows']} measurements")
        
            if "active_pore_percentage" in pore:
                pct = pore["active_pore_percentage"]
                status = ""
                if pct >= 70:
                    status = f"{GREEN}(good){RESET}"
                elif pct >= 50:
                    status = f"{YELLOW}(acceptable){RESET}"
                else:
                    status = f"{RED}(poor){RESET}"
                print(f"  Active pore percentage: {pct}% {status}")

    # errors
    if "errors" in results and results["errors"]:
        print(f"\n{SECTION}┌{'─' * 78}┐{RESET}")
        print(f"{SECTION}│{BOLD} ERRORS{' ' * 72}│{RESET}")
        print(f"{SECTION}└{'─' * 78}┘{RESET}")
        
        for error in results["errors"]:
            print(f"  {RED}•{RESET} {error}")
    
    # summary
    print("\n" + "═" * 80)
    print(f"{status_color}{results['status']}: {results['message']}{RESET}")
    print("═" * 80 + "\n")

# --- Main Function ---

def main():
    """parses args and runs analysis"""
    parser = argparse.ArgumentParser(
        description="""
        analyzer for oxford nanopore sequencing data
        
        analyzes ONT data including:
        - pod5/fastq comparison
        - metric extraction
        - quality assessment
        - fair compliance
        """,
        epilog="example: %(prog)s /path/to/nanopore_data"
    )
    parser.add_argument("directory", help="parent directory with ONT data")
    parser.add_argument("-o", "--output", help="output json file")
    parser.add_argument("--no-fair", action="store_true", help="skip fair enhancement")
    parser.add_argument("--metadata", help="json file with additional metadata")
    args = parser.parse_args()
    
    # load metadata if provided
    metadata = None
    if args.metadata:
        try:
            with open(args.metadata, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"error loading metadata file: {e}")
            return 1
    
    # run analysis
    results = analyze_nanopore_data(
        args.directory,
        enhance_fair=not args.no_fair,
        metadata=metadata,
        output_file=args.output
    )
    
    # print results
    print_results(results)
    
    # return code
    if results["status"] == "ERROR":
        return 1
    elif results["status"] == "WARNING":
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())

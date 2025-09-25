import os
import re
import pandas as pd
import numpy as np
from datetime import datetime
import argparse

def get_log_label(filename):
    """Map filename to a human-readable label."""
    labels = {
        "loud": "Our Scheduler",
        "stress": "StressTest",
        "round_robin": "Round Robin Scheduler",
        "random": "Random Scheduler",
        "fixed_batch": "Fixed Batch Scheduler",
        "interval": "Interval Scheduler",
        "transparent": "No Scheduler",
    }
    for key in labels:
        if key in filename:
            return labels[key]
    return filename

def calculate_energy(tegrastats_df, interval_ms):
    """Calculate total energy using a fixed interval between measurements."""
    if len(tegrastats_df) < 1:
        # This check is now more important as parsing can return empty DFs
        return 0.0
    # Calculate energy in joules (power in mW * interval / 1000)
    energy = (tegrastats_df['Power_Sum'] * (interval_ms / 1000)).sum() / 1000
    print(f"Calculated energy (J): {energy}")
    return energy

def parse_request_log(file_path, aggregation_level='S', aggregate=True):
    """Parse request log CSV and compute latency metrics with batch sizes."""
    df = pd.read_csv(file_path)
    # Convert timestamps and adjust timezone (assuming +2 hours correction)
    for col in ['Arrival Time', 'Queue Exit Time', 'Completion Time']:
        df[col] = pd.to_datetime(df[col], unit='s') + pd.Timedelta(hours=2)
    # Calculate time metrics
    df['Queue Time'] = (df['Queue Exit Time'] - df['Arrival Time']).dt.total_seconds()
    df['Excess Latency'] = df['Latency'] - df['Requested Latency']
    # Add batch size based on shared queue exit times
    df['Batch Size'] = df.groupby('Queue Exit Time')['Queue Exit Time'].transform('count')
    # Replace negative Excess Latency with 0
    df['Excess Latency'] = df['Excess Latency'].clip(lower=0)
    # Calculate percentage excess latency
    df['Percentage Excess Latency'] = (df['Excess Latency'] / df['Requested Latency']) * 100
    # Determine if within latency constraint
    df['Within Latency Constraint'] = df['Excess Latency'] <= 0
    if aggregate:
        # Aggregate by specified level (default is second)
        df['Rounded Arrival Time'] = df['Arrival Time'].dt.floor(aggregation_level)
        numeric_cols = df.select_dtypes(include='number').columns
        latency_grouped = df.groupby('Rounded Arrival Time')[numeric_cols].mean().reset_index()
    else:
        df['Rounded Arrival Time'] = df['Arrival Time']
        latency_grouped = df
    print(f"\nRequest log: {file_path}")
    print(latency_grouped.head())
    return latency_grouped

def parse_tegrastats_log(file_path, device, interval_ms):
    """
    Parse tegrastats log to extract power, temperature, and GPU frequency.
    Timestamps are generated from the filename and the known sampling interval.
    """
    # Extract base timestamp from the filename, which is consistent
    ts_match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2}:\d{2}:\d{2})', os.path.basename(file_path))
    if not ts_match:
        print(f"Warning: Could not extract base timestamp from filename {os.path.basename(file_path)}. Skipping file.")
        return pd.DataFrame()

    base_timestamp_str = f"{ts_match.group(1)} {ts_match.group(2)}"
    base_timestamp = datetime.strptime(base_timestamp_str, '%Y-%m-%d %H:%M:%S')

    timestamps, power_sum, temperatures, gpu_freqs = [], [], [], []
    line_number = 0

    with open(file_path, 'r') as file:
        for line in file:
            try:
                # A line is only valid if it contains expected metrics.
                # This check prevents parsing headers or malformed lines.
                gpu_freq_match = re.search(r'GR3D_FREQ\s+\d+%@(\d+)', line)
                temp_match = re.search(r'CPU@([\d.]+)C', line)
                if not gpu_freq_match or not temp_match:
                    continue

                # --- Power Parsing (Device-specific) ---
                power_components = {}
                if 'nano' in device:
                    power_components = {
                        'IN': r'POM_5V_IN (\d+)', 'GPU': r'POM_5V_GPU (\d+)', 'CPU': r'POM_5V_CPU (\d+)'
                    }
                elif 'nx' in device:
                    power_components = {
                        'IN': r'VDD_IN (\d+)mW', 'CPU_GPU_CV': r'VDD_CPU_GPU_CV (\d+)mW', 'SOC': r'VDD_SOC (\d+)mW'
                    }
                else:  # Default to AGX format
                    power_components = {
                        'CPU': r'CPU (\d+)mW', 'GPU': r'GPU (\d+)mW', 'SOC': r'SOC (\d+)mW',
                        'CV': r'CV (\d+)mW', 'VDDRQ': r'VDDRQ (\d+)mW', 'SYS5V': r'SYS5V (\d+)mW'
                    }

                total_power = sum(int(match.group(1)) for pattern in power_components.values() if (match := re.search(pattern, line)))
                
                # --- Append data for the valid line ---
                power_sum.append(total_power)
                gpu_freqs.append(int(gpu_freq_match.group(1)))
                temperatures.append(float(temp_match.group(1)))
                
                # Generate timestamp for this line
                current_timestamp = base_timestamp + pd.Timedelta(milliseconds=line_number * interval_ms)
                timestamps.append(current_timestamp)
                
                line_number += 1

            except Exception as e:
                print(f"Error parsing line in {file_path} for device {device}: {line}\n{e}")

    if not timestamps:  # If no valid lines were found
        return pd.DataFrame()
        
    tegrastats_df = pd.DataFrame({
        'Timestamp': pd.to_datetime(timestamps),
        'Power_Sum': power_sum,
        'Temperature': temperatures,
        'GPU_Freq': gpu_freqs
    })
    
    print(f"\nTegrastats log: {file_path} (Device: {device})")
    print(tegrastats_df.head())
    return tegrastats_df

def calculate_network_adjusted_metrics(df, network_cost_csv):
    """Calculate metrics using latency adjusted for network costs."""
    try:
        network_cost_df = pd.read_csv(network_cost_csv)
        network_cost_df['Network Cost (s)'] = network_cost_df['Network Cost (μs)'] / 1_000_000
        merged_df = df.merge(
            network_cost_df[['Batch Size', 'Network Cost (s)']], on='Batch Size', how='left'
        ).fillna({'Network Cost (s)': 0})
        merged_df['Network Cost (s)'] = np.ceil(merged_df['Network Cost (s)'] * 10) / 10 + 0.1
        merged_df['Latency Without Network'] = merged_df['Latency'] - merged_df['Network Cost (s)']
        merged_df['Excess Latency Without Network'] = (
            merged_df['Latency Without Network'] - merged_df['Requested Latency']
        ).clip(lower=0)
        merged_df['Percentage Excess Without Network'] = (
            merged_df['Excess Latency Without Network'] / merged_df['Requested Latency']
        ) * 100
        merged_df['Within Constraint Without Network'] = merged_df['Excess Latency Without Network'] <= 0
        return merged_df
    except Exception as e:
        print(f"Error processing network costs: {e}")
        return df

def extract_parameters(filename):
    """Extract scheduler type and parameters from filename."""
    label = get_log_label(filename)
    batch_size, interval, pred_mode = None, None, None
    batch_match = re.search(r'_fixed_batch_(\d+)', filename)
    if batch_match:
        batch_size = int(batch_match.group(1))
    interval_match = re.search(r'_interval_([\d.]+)', filename)
    if interval_match:
        try:
            interval = float(interval_match.group(1))
        except ValueError:
            print(f"Warning: Invalid interval value in {filename}")
    pred_mode_match = re.search(r'loud_([a-zA-Z]+)', filename)
    if pred_mode_match:
        pred_mode = pred_mode_match.group(1)
    return label, batch_size, interval, pred_mode

def process_experiment_folder(folder_path, interval_ms, exclude_ids=None, network_cost_path=None):
    """Process all log files in an experiment subfolder."""
    results = []
    exclude_ids = exclude_ids or []
    log_groups = {}
    
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        
        request_match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{2}:\d{2}:\d{2})_id(\d+)_(.*?)_request_log\.csv', file)
        if request_match:
            key = (request_match.group(1), request_match.group(2), request_match.group(3))
            log_groups.setdefault(key, {'request': None, 'tegrastats': {}})['request'] = file_path
            continue
            
        tegra_match = re.match(r'([a-zA-Z0-9.-]+)_(\d{4}-\d{2}-\d{2})_(\d{2}:\d{2}:\d{2})_id(\d+)_(.*?)_tegrastats', file)
        if tegra_match:
            device = tegra_match.group(1)
            key = (tegra_match.group(2), tegra_match.group(3), tegra_match.group(4))
            log_groups.setdefault(key, {'request': None, 'tegrastats': {}})['tegrastats'][device] = file_path

    for key, logs in log_groups.items():
        experiment_id = key[2]
        if experiment_id in exclude_ids or not logs['request'] or not logs['tegrastats']:
            continue
        try:
            req_df = parse_request_log(logs['request'], aggregate=False)
            if network_cost_path:
                req_df = calculate_network_adjusted_metrics(req_df, network_cost_path)

            completed_req_df = req_df[~req_df['Timed Out']]
            total_requests, total_frames, total_completed_frames = len(req_df), len(req_df), len(completed_req_df)

            mean_excess = completed_req_df['Excess Latency'].mean() if total_completed_frames > 0 else 0.0
            mean_percent_excess = completed_req_df['Percentage Excess Latency'].mean() if total_completed_frames > 0 else 0.0
            
            percent_requests_within_constraint = (completed_req_df['Within Latency Constraint'].sum() / total_requests) * 100 if total_requests > 0 else 0.0
            percent_frames_within_constraint = (req_df['Within Latency Constraint'].sum() / total_frames) * 100 if total_frames > 0 else 0.0
            percent_completed_frames_within_constraint = (completed_req_df['Within Latency Constraint'].sum() / total_completed_frames) * 100 if total_completed_frames > 0 else 0.0

            num_time_out = req_df['Timed Out'].sum() if total_requests > 0 else 0
            percent_time_out = (num_time_out / total_requests) * 100 if total_requests > 0 else 0.0
            network_metrics = {}
            if network_cost_path and 'Excess Latency Without Network' in req_df.columns:
                if total_completed_frames > 0:
                    network_metrics.update({
                        'mean_excess_latency_adj_s': completed_req_df['Excess Latency Without Network'].mean(),
                        'mean_percent_excess_adj': completed_req_df['Percentage Excess Without Network'].mean(),
                        'percent_requests_within_adj': (completed_req_df['Within Constraint Without Network'].sum() / total_requests) * 100,
                        'percent_frames_within_adj': (req_df['Within Constraint Without Network'].sum() / total_frames) * 100,
                        'percent_completed_frames_within_adj': (completed_req_df['Within Constraint Without Network'].sum() / total_completed_frames) * 100,
                    })
                else:
                    network_metrics.update({k: 0.0 for k in ['mean_excess_latency_adj_s', 'mean_percent_excess_adj', 'percent_requests_within_adj', 'percent_frames_within_adj', 'percent_completed_frames_within_adj']})
            else:
                network_metrics.update({k: None for k in ['mean_excess_latency_adj_s', 'mean_percent_excess_adj', 'percent_requests_within_adj', 'percent_frames_within_adj', 'percent_completed_frames_within_adj']})

            filename_base = os.path.basename(logs['request'])
            label, batch_size, interval_val, pred_mode = extract_parameters(filename_base)

            for device, tegra_path in logs['tegrastats'].items():
                try:
                    # Pass interval_ms to the parsing function
                    tegra_df = parse_tegrastats_log(tegra_path, device, interval_ms)
                    
                    if tegra_df.empty:
                        print(f"Warning: Tegrastats DataFrame is empty for {device} in {logs['request']}. Skipping device.")
                        continue

                    total_energy = calculate_energy(tegra_df, interval_ms)
                    frames_per_joule = total_frames / total_energy if total_energy > 0 else 0.0
                    requests_per_joule = total_requests / total_energy if total_energy > 0 else 0.0

                    results.append({
                        'experiment_id': experiment_id, 'timestamp': f"{key[0]} {key[1]}", 'scheduler': label,
                        'batch_size': batch_size, 'interval': interval_val, 'prediction_mode': pred_mode, 'device': device,
                        'mean_excess_latency_s': mean_excess, 'mean_percent_excess': mean_percent_excess,
                        'total_energy_j': total_energy, 'frames_per_joule': frames_per_joule, 'requests_per_joule': requests_per_joule,
                        'num_frames': total_frames, 'num_requests': req_df['Request ID'].nunique(),
                        'max_temperature_c': tegra_df['Temperature'].max(), 'mean_temperature_c': tegra_df['Temperature'].mean(), 'min_temperature_c': tegra_df['Temperature'].min(),
                        'avg_gpu_freq_mhz': tegra_df['GPU_Freq'].mean(), 'max_gpu_freq_mhz': tegra_df['GPU_Freq'].max(), 'min_gpu_freq_mhz': tegra_df['GPU_Freq'].min(),
                        'num_time_out': num_time_out, 'percent_time_out': percent_time_out,
                        'percent_requests_within_constraint': percent_requests_within_constraint,
                        'percent_frames_within_constraint': percent_frames_within_constraint,
                        'percent_completed_frames_within_constraint': percent_completed_frames_within_constraint,
                        **network_metrics
                    })
                except Exception as e:
                    print(f"Error processing device {device} for {logs['request']}: {e}")
        except Exception as e:
            print(f"Error processing experiment {logs['request']}: {e}")
    return results

def generate_report(top_folder, interval_ms=200, exclude_ids=None, network_cost_csv=None):
    """Generate CSV report for all experiments."""
    all_results = []
    for entry in os.listdir(top_folder):
        entry_path = os.path.join(top_folder, entry)
        if os.path.isdir(entry_path):
            experiment_type = entry
            experiment_results = process_experiment_folder(entry_path, interval_ms, exclude_ids=exclude_ids, network_cost_path=network_cost_csv)
            for result in experiment_results:
                result['experiment_type'] = experiment_type
                all_results.append(result)
    
    if not all_results:
        print("No valid experiment data found")
        return

    df = pd.DataFrame(all_results)
    df = df.sort_values(['experiment_id', 'scheduler', 'batch_size', 'interval', 'device'])
    
    columns_order = [
        'experiment_type', 'experiment_id', 'timestamp', 'scheduler', 'prediction_mode', 'device', 
        'batch_size', 'interval', 'num_requests', 'num_frames', 'mean_excess_latency_s', 'mean_percent_excess',
        'total_energy_j', 'requests_per_joule', 'frames_per_joule', 'max_temperature_c', 'mean_temperature_c',
        'min_temperature_c', 'max_gpu_freq_mhz', 'avg_gpu_freq_mhz', 'min_gpu_freq_mhz', 'num_time_out',
        'percent_time_out', 'percent_requests_within_constraint', 'percent_frames_within_constraint',
        'percent_completed_frames_within_constraint', 'mean_excess_latency_adj_s', 'mean_percent_excess_adj',
        'percent_requests_within_adj', 'percent_frames_within_adj', 'percent_completed_frames_within_adj'
    ]
    
    # Ensure all columns exist, fill missing with None
    for col in columns_order:
        if col not in df.columns:
            df[col] = None
            
    report_path = os.path.join(top_folder, 'experiment_report.csv')
    df[columns_order].to_csv(report_path, index=False, decimal=',', sep=';')
    print(f"Report generated: {report_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate experiment report CSV')
    parser.add_argument('--top-folder', required=True, help='Path to experiment_results folder')
    parser.add_argument('--interval-ms', type=int, default=200, help='Tegrastats sampling interval in milliseconds')
    parser.add_argument('--exclude-ids', nargs='+', type=str, default=[], help='Experiment IDs to exclude (space-separated)')
    parser.add_argument('--network-cost-csv', type=str, help='Optional path to network cost CSV')
    args = parser.parse_args()
    
    generate_report(
        args.top_folder,
        args.interval_ms,
        exclude_ids=set(args.exclude_ids),
        network_cost_csv=args.network_cost_csv
    )

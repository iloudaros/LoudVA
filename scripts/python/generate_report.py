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
        print("Insufficient data for energy calculation.")
        return 0.0
    
    # Calculate energy in joules (power in mW * interval / 1000)
    energy = (tegrastats_df['Power_Sum'] * (interval_ms / 1000)).sum() / 1000
    print("Calculated energy (J):", energy)
    
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

    # Debugging: print first few rows to verify
    print(f"\nRequest log: {file_path}")
    print(f"aggregation level: {aggregation_level}")
    print(f"Arrival time type: {df['Arrival Time'].dtype}")
    print(latency_grouped.head())

    return latency_grouped


def parse_tegrastats_log(file_path):
    """Parse tegrastats log to extract power, temperature, and GPU frequency."""
    timestamps = []
    power_sum = []
    temperatures = []
    gpu_freqs = []

    with open(file_path, 'r') as file:
        for line in file:
            try:
                # Extract timestamp
                time_str = line.split()[0] + ' ' + line.split()[1]
                timestamp = datetime.strptime(time_str, '%m-%d-%Y %H:%M:%S')
                timestamps.append(timestamp)

                # Extract power data (handle missing values)
                power_components = {
                    'CPU': r'CPU (\d+)mW',
                    'GPU': r'GPU (\d+)mW',
                    'SOC': r'SOC (\d+)mW',
                    'CV': r'CV (\d+)mW',
                    'VDDRQ': r'VDDRQ (\d+)mW',
                    'SYS5V': r'SYS5V (\d+)mW'
                }
                total_power = 0
                for component, pattern in power_components.items():
                    match = re.search(pattern, line)
                    total_power += int(match.group(1)) if match else 0

                power_sum.append(total_power)

                # Extract GPU frequency
                gpu_freq_match = re.search(r'GR3D_FREQ\s+\d+%@(\d+)', line)
                gpu_freq = int(gpu_freq_match.group(1)) if gpu_freq_match else 0
                gpu_freqs.append(gpu_freq)

                # Extract temperature
                temp_match = re.search(r'CPU@([\d.]+)C', line)
                temperatures.append(float(temp_match.group(1)) if temp_match else 0.0)

            except Exception as e:
                print(f"Error parsing line: {line}\n{e}")

    tegrastats_df = pd.DataFrame({
        'Timestamp': timestamps,
        'Power_Sum': power_sum,
        'Temperature': temperatures,
        'GPU_Freq': gpu_freqs
    })

    # Ensure the Timestamp column is of datetime type
    try:
        tegrastats_df['Timestamp'] = pd.to_datetime(tegrastats_df['Timestamp'])
    except Exception as e:
        print(f"Error converting Timestamp to datetime: {e}")

    # Debugging: print first few rows to verify
    print(f"\nTegrastats log: {file_path}")
    print(f"tegra timestamp type: {tegrastats_df['Timestamp'].dtype}")
    print(tegrastats_df.head())  # Debugging: print first few rows to verify

    return tegrastats_df

def calculate_network_adjusted_metrics(df, network_cost_csv):
    """Calculate metrics using latency adjusted for network costs."""
    try:
        network_cost_df = pd.read_csv(network_cost_csv)
        network_cost_df['Network Cost (s)'] = network_cost_df['Network Cost (μs)'] / 1_000_000
        
        merged_df = df.merge(
            network_cost_df[['Batch Size', 'Network Cost (s)']],
            on='Batch Size',
            how='left'
        ).fillna({'Network Cost (s)': 0})  # Handle missing batch sizes

        merged_df['Network Cost (s)'] = np.ceil(merged_df['Network Cost (s)'] * 10) / 10 + 0.1
        
        merged_df['Latency Without Network'] = merged_df['Latency'] - merged_df['Network Cost (s)']
        merged_df['Excess Latency Without Network'] = (
            merged_df['Latency Without Network'] - merged_df['Requested Latency']
        ).clip(lower=0)
        
        merged_df['Percentage Excess Without Network'] = (
            merged_df['Excess Latency Without Network'] / merged_df['Requested Latency']
        ) * 100
        
        merged_df['Within Constraint Without Network'] = (
            merged_df['Excess Latency Without Network'] <= 0
        )
        
        return merged_df
    except Exception as e:
        print(f"Error processing network costs: {e}")
        return df


def extract_parameters(filename):
    """Extract scheduler type and parameters from filename."""
    label = get_log_label(filename)
    batch_size = None
    interval = None
    pred_mode = None  

    # Extract batch size if present (integer values)
    batch_match = re.search(r'_fixed_batch_(\d+)', filename)
    if batch_match:
        batch_size = int(batch_match.group(1))
        
    # Extract interval if present (float values)
    interval_match = re.search(r'_interval_([\d.]+)', filename)
    if interval_match:
        try:
            interval = float(interval_match.group(1))
        except ValueError:
            print(f"Warning: Invalid interval value in {filename}")

    # Extract prediction mode for loud experiments
    pred_mode_match = re.search(r'loud_([a-zA-Z]+)', filename)
    if pred_mode_match:
        pred_mode = pred_mode_match.group(1)  # 'prof' or 'pred'

    return label, batch_size, interval, pred_mode

def process_experiment_folder(folder_path, interval_ms, exclude_ids=None, network_cost_path=None):
    """Process all log files in an experiment subfolder."""
    results = []
    exclude_ids = exclude_ids or []

    # Group files by experiment ID and timestamp
    log_groups = {}
    
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        
        # Match request logs
        request_match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{2}:\d{2}:\d{2})_id(\d+)_(.*?)_request_log\.csv', file)
        if request_match:
            key = (request_match.group(1), request_match.group(2), request_match.group(3))
            log_groups.setdefault(key, {'request': None, 'tegrastats': None})
            log_groups[key]['request'] = file_path
            continue
            
        # Match tegrastats logs
        tegra_match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{2}:\d{2}:\d{2})_id(\d+)_(.*?)_tegrastats', file)
        if tegra_match:
            key = (tegra_match.group(1), tegra_match.group(2), tegra_match.group(3))
            log_groups.setdefault(key, {'request': None, 'tegrastats': None})
            log_groups[key]['tegrastats'] = file_path

    # Process each log pair
    for key in log_groups:
        experiment_id = key[2]

        # skip excluded ids
        if experiment_id in exclude_ids:
            continue

        logs = log_groups[key]
        if not logs['request'] or not logs['tegrastats']:
            continue  # Skip incomplete pairs

        try:
            # Parse logs
            req_df = parse_request_log(logs['request'], aggregate=False)
            tegra_df = parse_tegrastats_log(logs['tegrastats'])

            if network_cost_path:
                req_df = calculate_network_adjusted_metrics(req_df, network_cost_path)

            
            # Latency metrics
            # Filter out timed-out requests for latency calculations
            completed_req_df = req_df[~req_df['Timed Out']] 
            
            # Calculate metrics using only successful requests
            if len(completed_req_df) > 0:
                mean_excess = completed_req_df['Excess Latency'].mean()
                mean_percent_excess = completed_req_df['Percentage Excess Latency'].mean()
            else:
                # Handle case where all requests timed out
                mean_excess = 0.0
                mean_percent_excess = 0.0

            # Calculate percentage of requests within latency constraint
            total_requests = len(req_df)
            requests_within_constraint = completed_req_df['Within Latency Constraint'].sum()
            percent_requests_within_constraint = (requests_within_constraint / total_requests) * 100 if total_requests > 0 else 0.0
            
            # Calculate percentage of frames within latency constraint
            total_frames = len(req_df)
            frames_within_constraint = req_df['Within Latency Constraint'].sum()
            percent_frames_within_constraint = (frames_within_constraint / total_frames) * 100 if total_frames > 0 else 0.0
            
            # Calculate percentage of frames within latency constraint, excluding timed out frames
            total_completed_frames = len(completed_req_df)
            completed_frames_within_constraint = completed_req_df['Within Latency Constraint'].sum()
            percent_completed_frames_within_constraint = (completed_frames_within_constraint / total_completed_frames) * 100 if total_completed_frames > 0 else 0.0

            # Energy metrics
            total_energy = calculate_energy(tegra_df, interval_ms)

            # Energy efficiency calculations
            if total_energy > 0 and total_frames > 0:
                frames_per_joule = total_frames / total_energy  # Frames per Joule
                requests_per_joule = total_requests / total_energy # Requests per Joule
            else:
                frames_per_joule = 0.0

            # GPU metrics
            max_gpu_freq = tegra_df['GPU_Freq'].max()
            mean_gpu_freq = tegra_df['GPU_Freq'].mean()
            min_gpu_freq = tegra_df['GPU_Freq'].min()
            
            # Timeout metrics
            if len(req_df) > 0:
                num_time_out = req_df['Timed Out'].sum()
                percent_time_out = (num_time_out / len(req_df)) * 100
            else:
                num_time_out = 0
                percent_time_out = 0.0

            # Temperature metrics
            max_temp = tegra_df['Temperature'].max()
            mean_temp = tegra_df['Temperature'].mean()
            min_temp = tegra_df['Temperature'].min()  

            # Network-adjusted metrics
            network_metrics = {}
            if network_cost_path and 'Excess Latency Without Network' in req_df.columns:
                if len(completed_req_df) > 0:
                     network_metrics.update({
                    'mean_excess_latency_adj_s': completed_req_df['Excess Latency Without Network'].mean(),
                    'mean_percent_excess_adj': completed_req_df['Percentage Excess Without Network'].mean(),
                    'percent_requests_within_adj': (completed_req_df['Within Constraint Without Network'].sum() / total_requests) * 100,
                    'percent_frames_within_adj': (req_df['Within Constraint Without Network'].sum() / total_frames) * 100,
                    'percent_completed_frames_within_adj': (completed_req_df['Within Constraint Without Network'].sum() / total_completed_frames) * 100,
                })
                else:
                    network_metrics.update({
                        'mean_excess_latency_adj_s': 0.0,
                        'mean_percent_excess_adj': 0.0,
                        'percent_requests_within_adj': 0.0,
                        'percent_frames_within_adj': 0.0,
                        'percent_completed_frames_within_adj': 0.0,
                    })
            else:
                network_metrics.update({
                    'mean_excess_latency_adj_s': None,
                    'mean_percent_excess_adj': None,
                    'percent_requests_within_adj': None,
                    'percent_frames_within_adj': None,
                    'percent_completed_frames_within_adj': None,
                })



            # Extract parameters from filename
            filename = os.path.basename(logs['request'])
            label, batch_size, interval_val, pred_mode = extract_parameters(filename)
            
            results.append({
                'experiment_id': key[2],
                'timestamp': f"{key[0]} {key[1]}",
                'scheduler': label,
                'batch_size': batch_size,
                'interval': interval_val,
                'prediction_mode': pred_mode,
                'mean_excess_latency_s': mean_excess,
                'mean_percent_excess': mean_percent_excess,
                'total_energy_j': total_energy,
                'frames_per_joule': frames_per_joule,
                'requests_per_joule': requests_per_joule,
                'num_frames': len(req_df),
                'num_requests': req_df['Request ID'].nunique(),
                'max_temperature_c': max_temp,
                'mean_temperature_c': mean_temp,
                'min_temperature_c': min_temp,
                'avg_gpu_freq_mhz': mean_gpu_freq,
                'max_gpu_freq_mhz': max_gpu_freq,
                'min_gpu_freq_mhz': min_gpu_freq,
                'num_time_out': num_time_out,
                'percent_time_out': percent_time_out,
                'percent_requests_within_constraint': percent_requests_within_constraint,
                'percent_frames_within_constraint': percent_frames_within_constraint,
                'percent_completed_frames_within_constraint': percent_completed_frames_within_constraint,
                **network_metrics
            })

            
        except Exception as e:
            print(f"Error processing {logs['request']}: {str(e)}")
    
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
    
    # Create DataFrame and save CSV
    df = pd.DataFrame(all_results)
    df = df.sort_values(['experiment_id', 'scheduler', 'batch_size', 'interval'])
    columns_order = [
        'experiment_type', 'experiment_id', 'timestamp', 'scheduler',
        'prediction_mode', 'batch_size', 'interval', 
        'num_requests', 'num_frames',
        'mean_excess_latency_s', 'mean_percent_excess', 
        'total_energy_j', 'requests_per_joule', 'frames_per_joule',
        'max_temperature_c', 'mean_temperature_c', 'min_temperature_c',
        'max_gpu_freq_mhz','avg_gpu_freq_mhz', 'min_gpu_freq_mhz',
        'num_time_out', 'percent_time_out',
        'percent_requests_within_constraint', 'percent_frames_within_constraint', 'percent_completed_frames_within_constraint',
        'mean_excess_latency_adj_s', 'mean_percent_excess_adj', 'percent_requests_within_adj', 'percent_frames_within_adj', 'percent_completed_frames_within_adj'
    ]
    report_path = os.path.join(top_folder, 'experiment_report.csv')
    df[columns_order].to_csv(report_path, index=False)
    print(f"Report generated: {report_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate experiment report CSV')
    parser.add_argument('--top-folder', required=True,
                        help='Path to experiment_results folder')
    parser.add_argument('--interval-ms', type=int, default=200,
                        help='Tegrastats sampling interval in milliseconds')
    parser.add_argument('--exclude-ids', nargs='+', type=str, default=[],
                        help='Experiment IDs to exclude (space-separated)')
    parser.add_argument('--network-cost-csv', type=str,
                        help='Optional path to network cost CSV')
    args = parser.parse_args()
    
    generate_report(
        args.top_folder, 
        args.interval_ms,
        exclude_ids=set(args.exclude_ids),
        network_cost_csv=args.network_cost_csv 
    )

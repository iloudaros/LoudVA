import os
import re
import pandas as pd
import numpy as np
from datetime import datetime
import argparse

# --- Core Functions Directly from the generate_report3.py Blueprint ---

def calculate_energy(tegrastats_df, interval_ms):
    """Calculate total energy in Joules from power data in mW."""
    if tegrastats_df.empty:
        return 0.0
    # Energy (J) = (Sum of Power (mW) * Interval (s)) / 1000
    energy = (tegrastats_df['Power_Sum_mW'].sum() * (interval_ms / 1000)) / 1000
    return energy

def parse_request_log(file_path):
    """Parse request log CSV and compute latency metrics."""
    try:
        df = pd.read_csv(file_path)
        if 'Latency' not in df.columns:
            df['Latency'] = df['Completion Time'] - df['Arrival Time']
        df['Excess Latency'] = (df['Latency'] - df['Requested Latency']).clip(lower=0)
        # Handle division by zero for Percentage Excess Latency
        df['Percentage Excess Latency'] = (df['Excess Latency'] / df['Requested Latency']).replace([np.inf, -np.inf], 0).fillna(0) * 100
        df['Within Latency Constraint'] = df['Excess Latency'] <= 0
        return df
    except Exception as e:
        print(f"Error parsing request log {file_path}: {e}")
        return pd.DataFrame()

def parse_tegrastats_log(file_path, device_type, interval_ms):
    """
    Parse tegrastats log using device-specific regex for power, temperature, and GPU frequency.
    This function is a direct copy of the logic from generate_report3.py.
    """
    ts_match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2}:\d{2}:\d{2})', os.path.basename(file_path))
    if not ts_match:
        ts_match_fallback = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2})', os.path.basename(file_path))
        if not ts_match_fallback:
            print(f"Warning: Could not extract base timestamp from {os.path.basename(file_path)}")
            return pd.DataFrame()
        base_timestamp = datetime.strptime(ts_match_fallback.group(1), '%Y-%m-%d_%H:%M:%S')
    else:
        base_timestamp_str = f"{ts_match.group(1)} {ts_match.group(2)}"
        base_timestamp = datetime.strptime(base_timestamp_str, '%Y-%m-%d %H:%M:%S')

    timestamps, power_sum, temperatures, gpu_freqs = [], [], [], []
    line_number = 0

    with open(file_path, 'r') as file:
        for line in file:
            try:
                gpu_freq_match = re.search(r'GR3D_FREQ\s+\d+%@(\d+)', line)
                temp_match = re.search(r'CPU@([\d.-]+)C', line)
                if not gpu_freq_match or not temp_match:
                    continue

                power_components = {}
                if 'nano' in device_type:
                    power_components = {'IN': r'POM_5V_IN (\d+)', 'GPU': r'POM_5V_GPU (\d+)', 'CPU': r'POM_5V_CPU (\d+)'}
                elif 'nx' in device_type:
                    power_components = {'IN': r'VDD_IN (\d+)', 'CPU_GPU': r'VDD_CPU_GPU_CV (\d+)', 'SOC': r'VDD_SOC (\d+)'}
                else:  # AGX format
                    power_components = {
                        'CPU': r'CPU (\d+)mW', 'GPU': r'GPU (\d+)mW', 'SOC': r'SOC (\d+)mW',
                        'CV': r'CV (\d+)mW', 'VDDRQ': r'VDDRQ (\d+)mW', 'SYS5V': r'SYS5V (\d+)mW'
                    }

                total_power = sum(int(match.group(1)) for pattern in power_components.values() if (match := re.search(pattern, line)))
                if total_power == 0: continue

                power_sum.append(total_power)
                gpu_freqs.append(int(gpu_freq_match.group(1)))
                temperatures.append(float(temp_match.group(1)))
                timestamps.append(base_timestamp + pd.Timedelta(milliseconds=line_number * interval_ms))
                line_number += 1
            except Exception:
                continue

    if not timestamps:
        return pd.DataFrame()
        
    return pd.DataFrame({
        'Timestamp': pd.to_datetime(timestamps),
        'Power_Sum_mW': power_sum,
        'Temperature_C': temperatures,
        'GPU_Freq_MHz': gpu_freqs
    })

# --- Main Logic Adapted for Experiment 4 ---

def generate_report(top_folder, interval_ms=200):
    all_results = []
    
    log_groups = {}
    for subdir, _, files in os.walk(top_folder):
        for file in files:
            match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2})_id(t\d+_s\d+)_', file)
            if match:
                key = (match.group(1), match.group(2))
                log_groups.setdefault(key, {'request': None, 'tegrastats': {}, 'folder': subdir})
                
                if file.endswith('_request_log.csv'):
                    log_groups[key]['request'] = os.path.join(subdir, file)
                elif file.endswith('_tegrastats'):
                    device_prefix = file.split('_')[0]
                    log_groups[key]['tegrastats'][device_prefix] = os.path.join(subdir, file)

    for key, logs in log_groups.items():
        if not logs['request'] or not logs['tegrastats']:
            continue
            
        req_df = parse_request_log(logs['request'])
        if req_df.empty:
            continue

        folder_name = os.path.basename(logs['folder'])
        scheduler_type = re.search(r'(loud_pred|loud_prof)', folder_name).group(1)
        throughput_level = int(re.search(r'throughput_(\d+)', folder_name).group(1))
        
        total_frames = total_requests = len(req_df)
        completed_req_df = req_df[~req_df['Timed Out']]
        total_completed_frames = len(completed_req_df)

        for device, tegra_path in logs['tegrastats'].items():
            tegra_df = parse_tegrastats_log(tegra_path, device, interval_ms)
            if tegra_df.empty:
                print(f"Warning: Empty tegrastats data for {device} in run {key}")
                continue

            total_energy = calculate_energy(tegra_df, interval_ms)
            
            all_results.append({
                'scheduler_type': scheduler_type, 'throughput_level': throughput_level, 'scenario_id': key[1],
                'timestamp': key[0], 'device': device, 'num_requests': total_requests, 'num_frames': total_frames,
                'num_time_out': req_df['Timed Out'].sum(),
                'percent_time_out': (req_df['Timed Out'].sum() / total_requests) * 100 if total_requests > 0 else 0,
                'mean_excess_latency_s': completed_req_df['Excess Latency'].mean() if total_completed_frames > 0 else 0,
                'mean_percent_excess': completed_req_df['Percentage Excess Latency'].mean() if total_completed_frames > 0 else 0,
                'total_energy_j': total_energy,
                'requests_per_joule': total_requests / total_energy if total_energy > 0 else 0,
                'frames_per_joule': total_frames / total_energy if total_energy > 0 else 0,
                'percent_requests_within_constraint': (req_df['Within Latency Constraint'].sum() / total_requests) * 100 if total_requests > 0 else 0,
                'percent_frames_within_constraint': (req_df['Within Latency Constraint'].sum() / total_frames) * 100 if total_frames > 0 else 0,
                'percent_completed_frames_within_constraint': (completed_req_df['Within Latency Constraint'].sum() / total_completed_frames) * 100 if total_completed_frames > 0 else 0,
                'max_temperature_c': tegra_df['Temperature_C'].max(),
                'mean_temperature_c': tegra_df['Temperature_C'].mean(),
                'min_temperature_c': tegra_df['Temperature_C'].min(),
                'max_gpu_freq_mhz': tegra_df['GPU_Freq_MHz'].max(),
                'avg_gpu_freq_mhz': tegra_df['GPU_Freq_MHz'].mean(),
                'min_gpu_freq_mhz': tegra_df['GPU_Freq_MHz'].min(),
            })
    
    if not all_results:
        print("No valid experiment data was processed.")
        return

    df = pd.DataFrame(all_results)
    
    columns_order = [
        'scheduler_type', 'throughput_level', 'scenario_id', 'timestamp', 'device', 
        'num_requests', 'num_frames', 'mean_excess_latency_s', 'mean_percent_excess', 
        'total_energy_j', 'requests_per_joule', 'frames_per_joule', 
        'max_temperature_c', 'mean_temperature_c', 'min_temperature_c', 
        'max_gpu_freq_mhz', 'avg_gpu_freq_mhz', 'min_gpu_freq_mhz', 
        'num_time_out', 'percent_time_out', 'percent_requests_within_constraint', 
        'percent_frames_within_constraint', 'percent_completed_frames_within_constraint'
    ]
    df = df.reindex(columns=columns_order).sort_values(['throughput_level', 'scheduler_type', 'scenario_id', 'device'])
            
    report_path = os.path.join(top_folder, 'experiment_report4.csv')
    df.to_csv(report_path, index=False, decimal=',', sep=';')
    print(f"\nReport for Experiment 4 generated successfully: {report_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate detailed report CSV for Experiment 4, modeled after generate_report3.py.')
    parser.add_argument('--top-folder', required=True, help='Path to the top-level Experiment 4 results folder.')
    parser.add_argument('--interval-ms', type=int, default=200, help='Tegrastats sampling interval in milliseconds.')
    args = parser.parse_args()
    
    generate_report(args.top_folder, args.interval_ms)

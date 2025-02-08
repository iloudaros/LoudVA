import pandas as pd
import argparse
import os

def aggregate_experiments(csv_path):
    # Read CSV data
    df = pd.read_csv(csv_path)
    
    # Create group key based on scheduler type and parameters
    def get_group_key(row):
        scheduler = row['scheduler']
        if scheduler == 'Fixed Batch Scheduler':
            return f"Fixed Batch ({int(row['batch_size'])})"
        elif scheduler == 'Interval Scheduler':
            return f"Interval ({row['interval']})"
        elif scheduler == 'Our Scheduler':
            return f"Our Scheduler ({row['prediction_mode']})"
        return scheduler
    
    df['group_key'] = df.apply(get_group_key, axis=1)
    
    # Calculate weighted averages and totals
    df['total_excess_latency'] = df['mean_excess_latency_s'] * df['num_requests']
    df['total_percent_excess'] = df['mean_percent_excess'] * df['num_requests']
    df['total_gpu_freq'] = df['avg_gpu_freq_mhz'] * df['num_requests']
    df['total_mean_temperature'] = df['mean_temperature_c'] * df['num_requests']
    
    # Aggregate metrics
    aggregated = df.groupby('group_key').agg({
        'num_requests': 'sum',
        'num_frames': 'sum',
        'total_excess_latency': 'sum',
        'total_percent_excess': 'sum',
        'total_energy_j': 'sum',
        'max_temperature_c': 'max',
        'total_mean_temperature': 'sum',
        'min_temperature_c': 'min',
        'total_gpu_freq': 'sum',
        'max_gpu_freq_mhz': 'max',
        'min_gpu_freq_mhz': 'min',
        'num_time_out': 'sum'
    }).reset_index()
    
    # Calculate final metrics
    aggregated['mean_excess_latency_s'] = aggregated['total_excess_latency'] / aggregated['num_frames']
    aggregated['mean_percent_excess'] = aggregated['total_percent_excess'] / aggregated['num_frames']
    aggregated['mean_temperature_c'] = aggregated['total_mean_temperature'] / aggregated['num_frames']
    aggregated['avg_gpu_freq_mhz'] = aggregated['total_gpu_freq'] / aggregated['num_frames']
    aggregated['requests_per_joule'] = aggregated['num_requests'] / aggregated['total_energy_j']
    aggregated['frames_per_joule'] = aggregated['num_frames'] / aggregated['total_energy_j']
    aggregated['percent_time_out'] = (aggregated['num_time_out'] / aggregated['num_frames']) * 100
    
    # Format final output
    result = aggregated[[
        'group_key', 'num_requests', 'num_frames', 'mean_excess_latency_s', 
        'mean_percent_excess', 'total_energy_j', 'requests_per_joule',
        'frames_per_joule', 'max_temperature_c', 'mean_temperature_c',
        'min_temperature_c', 'max_gpu_freq_mhz', 'avg_gpu_freq_mhz',
        'min_gpu_freq_mhz', 'num_time_out', 'percent_time_out'
    ]].rename(columns={'group_key': 'scheduler'})
    
    return result.sort_values('scheduler')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aggregate experiment results by scheduler type')
    parser.add_argument('report_path', help='Path to CSV file with experiment results')
    args = parser.parse_args()
    
    aggregated_results = aggregate_experiments(args.report_path)
    
    # Save results in same directory as input file
    input_dir = os.path.dirname(args.report_path)
    input_filename = os.path.basename(args.report_path)
    output_path = os.path.join(input_dir, f"{os.path.splitext(input_filename)[0]}_aggregated.csv")
    
    aggregated_results.to_csv(output_path, index=False, float_format='%.3f')
    print(f"Aggregated results saved to: {output_path}")

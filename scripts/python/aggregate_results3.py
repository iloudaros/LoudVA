import pandas as pd
import argparse
import os

def aggregate_overall_results(df):
    """
    Aggregates results to a system-wide level, correctly combining metrics
    from multiple devices per experiment run.
    """
    print("Generating overall aggregated report...")
    
    # Pre-aggregate by experiment_id to correctly handle per-device metrics
    # before the final aggregation by scheduler type.
    exp_agg = df.groupby(['experiment_id', 'group_key']).agg(
        # Sum energy from all devices
        total_energy_j=('total_energy_j', 'sum'),
        
        # Requests/Frames are the same for all devices in a run, so take the first
        num_requests=('num_requests', 'first'),
        num_frames=('num_frames', 'first'),
        num_time_out=('num_time_out', 'first'),

        # Latency is a per-request metric, so it's the same across devices for a run
        mean_excess_latency_s=('mean_excess_latency_s', 'first'),
        mean_percent_excess=('mean_percent_excess', 'first'),
        mean_excess_latency_adj_s=('mean_excess_latency_adj_s', 'first'),
        mean_percent_excess_adj=('mean_percent_excess_adj', 'first'),
        percent_requests_within_constraint=('percent_requests_within_constraint', 'first'),
        percent_frames_within_constraint=('percent_frames_within_constraint', 'first'),
        percent_completed_frames_within_constraint=('percent_completed_frames_within_constraint', 'first'),
        percent_requests_within_adj=('percent_requests_within_adj', 'first'),
        percent_frames_within_adj=('percent_frames_within_adj', 'first'),
        percent_completed_frames_within_adj=('percent_completed_frames_within_adj', 'first'),
        
        # For temps and freq, take the system-wide average, max, and min
        mean_temperature_c=('mean_temperature_c', 'mean'),
        max_temperature_c=('max_temperature_c', 'max'),
        min_temperature_c=('min_temperature_c', 'min'),
        avg_gpu_freq_mhz=('avg_gpu_freq_mhz', 'mean'),
        max_gpu_freq_mhz=('max_gpu_freq_mhz', 'max'),
        min_gpu_freq_mhz=('min_gpu_freq_mhz', 'min')
    ).reset_index()

    return perform_aggregation(exp_agg, ['group_key'])


def aggregate_per_device_results(df):
    """
    Aggregates results on a per-device basis, grouping by scheduler
    and device type.
    """
    print("Generating per-device aggregated report...")
    return perform_aggregation(df, ['group_key', 'device'])


def perform_aggregation(df, grouping_cols):
    """
    Core aggregation logic that can be applied to different groupings.
    """
    # Calculate weighted averages and totals for aggregation
    df['total_excess_latency'] = df['mean_excess_latency_s'] * df['num_frames']
    df['total_percent_excess'] = df['mean_percent_excess'] * df['num_frames']
    df['total_excess_latency_adj'] = df['mean_excess_latency_adj_s'].fillna(0) * df['num_frames']
    df['total_percent_excess_adj'] = df['mean_percent_excess_adj'].fillna(0) * df['num_frames']
    df['total_gpu_freq'] = df['avg_gpu_freq_mhz'] * df['num_frames']
    df['total_mean_temperature'] = df['mean_temperature_c'] * df['num_frames']
    
    df['total_requests_within_constraint'] = df['percent_requests_within_constraint'] * df['num_requests'] / 100
    df['total_frames_within_constraint'] = df['percent_frames_within_constraint'] * df['num_frames'] / 100
    df['total_completed_frames_within_constraint'] = df['percent_completed_frames_within_constraint'] * df['num_frames'] / 100
    
    df['total_requests_within_adj'] = df['percent_requests_within_adj'].fillna(0) * df['num_requests'] / 100
    df['total_frames_within_adj'] = df['percent_frames_within_adj'].fillna(0) * df['num_frames'] / 100
    df['total_completed_frames_within_adj'] = df['percent_completed_frames_within_adj'].fillna(0) * df['num_frames'] / 100

    # Define aggregation rules
    agg_rules = {
        'num_requests': 'sum',
        'num_frames': 'sum',
        'total_excess_latency': 'sum',
        'total_percent_excess': 'sum',
        'total_excess_latency_adj': 'sum',
        'total_percent_excess_adj': 'sum',
        'total_energy_j': 'sum',
        'max_temperature_c': 'max',
        'total_mean_temperature': 'sum',
        'min_temperature_c': 'min',
        'total_gpu_freq': 'sum',
        'max_gpu_freq_mhz': 'max',
        'min_gpu_freq_mhz': 'min',
        'num_time_out': 'sum',
        'total_requests_within_constraint': 'sum',
        'total_frames_within_constraint': 'sum',
        'total_completed_frames_within_constraint': 'sum',
        'total_requests_within_adj': 'sum',
        'total_frames_within_adj': 'sum',
        'total_completed_frames_within_adj': 'sum'
    }

    # If we are doing overall aggregation, we don't have per-device energy in the input df
    if 'total_energy_j' not in df.columns:
        if 'total_energy_j' in agg_rules:
             del agg_rules['total_energy_j']
        
    aggregated = df.groupby(grouping_cols).agg(agg_rules).reset_index()

    # Calculate final averaged/percentage metrics
    with pd.option_context('mode.chained_assignment', None):
        aggregated['mean_excess_latency_s'] = aggregated['total_excess_latency'] / aggregated['num_frames']
        aggregated['mean_percent_excess'] = aggregated['total_percent_excess'] / aggregated['num_frames']
        aggregated['mean_excess_latency_adj_s'] = aggregated['total_excess_latency_adj'] / aggregated['num_frames']
        aggregated['mean_percent_excess_adj'] = aggregated['total_percent_excess_adj'] / aggregated['num_frames']
        aggregated['mean_temperature_c'] = aggregated['total_mean_temperature'] / aggregated['num_frames']
        aggregated['avg_gpu_freq_mhz'] = aggregated['total_gpu_freq'] / aggregated['num_frames']
        
        if 'total_energy_j' in aggregated.columns:
            aggregated['requests_per_joule'] = aggregated['num_requests'] / aggregated['total_energy_j']
            aggregated['frames_per_joule'] = aggregated['num_frames'] / aggregated['total_energy_j']
        
        aggregated['percent_time_out'] = (aggregated['num_time_out'] / aggregated['num_requests']) * 100
        
        aggregated['percent_requests_within_constraint'] = (aggregated['total_requests_within_constraint'] / aggregated['num_requests']) * 100
        aggregated['percent_frames_within_constraint'] = (aggregated['total_frames_within_constraint'] / aggregated['num_frames']) * 100
        aggregated['percent_completed_frames_within_constraint'] = (aggregated['total_completed_frames_within_constraint'] / aggregated['num_frames']) * 100
        
        aggregated['percent_requests_within_adj'] = (aggregated['total_requests_within_adj'] / aggregated['num_requests']) * 100
        aggregated['percent_frames_within_adj'] = (aggregated['total_frames_within_adj'] / aggregated['num_frames']) * 100
        aggregated['percent_completed_frames_within_adj'] = (aggregated['total_completed_frames_within_adj'] / aggregated['num_frames']) * 100

    # Sort the results BEFORE renaming the grouping column
    aggregated = aggregated.sort_values(grouping_cols)
    
    # Clean up column names and select final set
    result = aggregated.rename(columns={'group_key': 'scheduler'})

    # Define final column order
    final_columns = [
        'scheduler', 'num_requests', 'num_frames',
        'mean_excess_latency_s', 'mean_percent_excess',
        'mean_excess_latency_adj_s', 'mean_percent_excess_adj',
        'total_energy_j', 'requests_per_joule', 'frames_per_joule',
        'max_temperature_c', 'mean_temperature_c', 'min_temperature_c',
        'max_gpu_freq_mhz', 'avg_gpu_freq_mhz', 'min_gpu_freq_mhz',
        'num_time_out', 'percent_time_out',
        'percent_requests_within_constraint', 'percent_frames_within_constraint',
        'percent_completed_frames_within_constraint',
        'percent_requests_within_adj', 'percent_frames_within_adj',
        'percent_completed_frames_within_adj'
    ]

    if 'device' in grouping_cols:
        final_columns.insert(1, 'device')
    
    # Ensure all expected columns exist, filling missing ones (like energy for some sub-calcs)
    for col in final_columns:
        if col not in result.columns:
            result[col] = pd.NA

    # Return final, ordered DataFrame
    return result[final_columns]


def main():
    parser = argparse.ArgumentParser(description='Aggregate experiment results by scheduler and device')
    parser.add_argument('report_path', help='Path to the detailed CSV file from generate_report.py')
    args = parser.parse_args()
    
    # Read the detailed report
    try:
        # Assuming the CSV from the previous script might use ';' and ','
        df = pd.read_csv(args.report_path, sep=';', decimal=',')
    except FileNotFoundError:
        print(f"Error: Input file not found at {args.report_path}")
        return
    except Exception as e:
        print(f"Trying to read as standard CSV due to error: {e}")
        try:
            # Fallback to standard comma separator
            df = pd.read_csv(args.report_path)
        except Exception as e2:
            print(f"Could not read CSV file. Error: {e2}")
            return


    # Create a consistent grouping key for all aggregations
    def get_group_key(row):
        scheduler = row['scheduler']
        if scheduler == 'Fixed Batch Scheduler':
            # Format batch_size as integer to avoid '.0'
            return f"Fixed Batch ({int(row['batch_size'])})"
        elif scheduler == 'Interval Scheduler':
            return f"Interval ({row['interval']})"
        elif scheduler == 'Our Scheduler' and pd.notna(row['prediction_mode']):
            return f"Our Scheduler ({row['prediction_mode']})"
        return scheduler
        
    df['group_key'] = df.apply(get_group_key, axis=1)

    # --- Generate and save Overall Aggregated Report ---
    overall_agg_df = aggregate_overall_results(df.copy())
    input_dir = os.path.dirname(args.report_path)
    input_filename = os.path.basename(args.report_path)
    base_filename = os.path.splitext(input_filename)[0]
    overall_output_path = os.path.join(input_dir, f"{base_filename}_aggregated_overall.csv")
    overall_agg_df.to_csv(overall_output_path, index=False, float_format='%.3f', sep=';', decimal=',')
    print(f"Overall aggregated results saved to: {overall_output_path}")

    # --- Generate and save Per-Device Aggregated Report ---
    per_device_agg_df = aggregate_per_device_results(df.copy())
    per_device_output_path = os.path.join(input_dir, f"{base_filename}_aggregated_per_device.csv")
    per_device_agg_df.to_csv(per_device_output_path, index=False, float_format='%.3f', sep=';', decimal=',')
    print(f"Per-device aggregated results saved to: {per_device_output_path}")


if __name__ == "__main__":
    main()

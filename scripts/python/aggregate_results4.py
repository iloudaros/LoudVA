import pandas as pd
import argparse
import os

def aggregate_overall_results(df):
    """
    Aggregates results to a system-wide level by first combining metrics
    from multiple devices for each individual experiment run.
    This is adapted from the Experiment 3 blueprint.
    """
    print("Generating overall system-wide aggregated report...")
    
    # Pre-aggregate by 'group_key' and 'scenario_id' to correctly handle per-device metrics.
    exp_agg = df.groupby(['group_key', 'scenario_id']).agg(
        # Sum energy from all devices for a single run
        total_energy_j=('total_energy_j', 'sum'),
        
        # These metrics are the same for all device rows in a run, so take the first
        num_requests=('num_requests', 'first'),
        num_frames=('num_frames', 'first'),
        num_time_out=('num_time_out', 'first'),
        mean_excess_latency_s=('mean_excess_latency_s', 'first'),
        mean_percent_excess=('mean_percent_excess', 'first'),
        percent_requests_within_constraint=('percent_requests_within_constraint', 'first'),
        percent_frames_within_constraint=('percent_frames_within_constraint', 'first'),
        percent_completed_frames_within_constraint=('percent_completed_frames_within_constraint', 'first'),
        
        # For temps and freq, take the system-wide average, max, and min across devices for the run
        mean_temperature_c=('mean_temperature_c', 'mean'),
        max_temperature_c=('max_temperature_c', 'max'),
        min_temperature_c=('min_temperature_c', 'min'),
        avg_gpu_freq_mhz=('avg_gpu_freq_mhz', 'mean'),
        max_gpu_freq_mhz=('max_gpu_freq_mhz', 'max'),
        min_gpu_freq_mhz=('min_gpu_freq_mhz', 'min')
    ).reset_index()

    # Now, perform the final aggregation across all scenarios
    return perform_aggregation(exp_agg, ['group_key'])


def aggregate_per_device_results(df):
    """
    Aggregates results on a per-device basis, grouping by scheduler, 
    throughput level, and device type.
    """
    print("Generating per-device aggregated report...")
    return perform_aggregation(df, ['group_key', 'device'])


def perform_aggregation(df, grouping_cols):
    """
    Core aggregation logic (from blueprint) that calculates weighted averages.
    """
    # Calculate "total" metrics to enable correct weighted averaging
    df['total_excess_latency'] = df['mean_excess_latency_s'] * df['num_frames']
    df['total_percent_excess'] = df['mean_percent_excess'] * df['num_frames']
    df['total_gpu_freq'] = df['avg_gpu_freq_mhz'] * df['num_frames']
    df['total_mean_temperature'] = df['mean_temperature_c'] * df['num_frames']
    
    df['total_requests_within_constraint'] = df['percent_requests_within_constraint'] * df['num_requests'] / 100
    df['total_frames_within_constraint'] = df['percent_frames_within_constraint'] * df['num_frames'] / 100
    df['total_completed_frames_within_constraint'] = df['percent_completed_frames_within_constraint'] * df['num_frames'] / 100

    agg_rules = {
        'num_requests': 'sum', 'num_frames': 'sum', 'total_excess_latency': 'sum',
        'total_percent_excess': 'sum', 'total_energy_j': 'sum', 'max_temperature_c': 'max',
        'total_mean_temperature': 'sum', 'min_temperature_c': 'min', 'total_gpu_freq': 'sum',
        'max_gpu_freq_mhz': 'max', 'min_gpu_freq_mhz': 'min', 'num_time_out': 'sum',
        'total_requests_within_constraint': 'sum', 'total_frames_within_constraint': 'sum',
        'total_completed_frames_within_constraint': 'sum'
    }

    aggregated = df.groupby(grouping_cols).agg(agg_rules).reset_index()

    # Calculate final averaged/percentage metrics from the summed totals
    with pd.option_context('mode.chained_assignment', None):
        aggregated['mean_excess_latency_s'] = aggregated['total_excess_latency'] / aggregated['num_frames']
        aggregated['mean_percent_excess'] = aggregated['total_percent_excess'] / aggregated['num_frames']
        aggregated['mean_temperature_c'] = aggregated['total_mean_temperature'] / aggregated['num_frames']
        aggregated['avg_gpu_freq_mhz'] = aggregated['total_gpu_freq'] / aggregated['num_frames']
        aggregated['requests_per_joule'] = aggregated['num_requests'] / aggregated['total_energy_j']
        aggregated['frames_per_joule'] = aggregated['num_frames'] / aggregated['total_energy_j']
        aggregated['percent_time_out'] = (aggregated['num_time_out'] / aggregated['num_requests']) * 100
        aggregated['percent_requests_within_constraint'] = (aggregated['total_requests_within_constraint'] / aggregated['num_requests']) * 100
        aggregated['percent_frames_within_constraint'] = (aggregated['total_frames_within_constraint'] / aggregated['num_frames']) * 100
        aggregated['percent_completed_frames_within_constraint'] = (aggregated['total_completed_frames_within_constraint'] / aggregated['num_frames']) * 100

    aggregated = aggregated.sort_values(grouping_cols)
    result = aggregated.rename(columns={'group_key': 'aggregation_group'})

    final_columns = [
        'aggregation_group', 'num_requests', 'num_frames', 'mean_excess_latency_s', 'mean_percent_excess',
        'total_energy_j', 'requests_per_joule', 'frames_per_joule',
        'max_temperature_c', 'mean_temperature_c', 'min_temperature_c',
        'max_gpu_freq_mhz', 'avg_gpu_freq_mhz', 'min_gpu_freq_mhz',
        'num_time_out', 'percent_time_out', 'percent_requests_within_constraint',
        'percent_frames_within_constraint', 'percent_completed_frames_within_constraint'
    ]
    if 'device' in grouping_cols:
        final_columns.insert(1, 'device')

    for col in final_columns:
        if col not in result.columns:
            result[col] = pd.NA
    return result[final_columns]

def main():
    parser = argparse.ArgumentParser(description='Aggregate Experiment 4 results using the Exp3 blueprint logic.')
    parser.add_argument('report_path', help='Path to the detailed experiment_report4.csv file.')
    args = parser.parse_args()
    
    try:
        df = pd.read_csv(args.report_path, sep=';', decimal=',')
    except Exception as e:
        print(f"Could not read CSV file. Error: {e}")
        return

    # Create a consistent grouping key for Experiment 4 aggregations
    def get_group_key(row):
        return f"{row['scheduler_type']} (T-{int(row['throughput_level'])})"
        
    df['group_key'] = df.apply(get_group_key, axis=1)

    # --- Generate and save Overall Aggregated Report ---
    overall_agg_df = aggregate_overall_results(df.copy())
    input_dir = os.path.dirname(args.report_path)
    base_filename = os.path.splitext(os.path.basename(args.report_path))[0]
    overall_output_path = os.path.join(input_dir, f"{base_filename}_aggregated_overall.csv")
    overall_agg_df.to_csv(overall_output_path, index=False, float_format='%.4f', sep=';', decimal=',')
    print(f"Overall aggregated results saved to: {overall_output_path}")

    # --- Generate and save Per-Device Aggregated Report ---
    per_device_agg_df = aggregate_per_device_results(df.copy())
    per_device_output_path = os.path.join(input_dir, f"{base_filename}_aggregated_per_device.csv")
    per_device_agg_df.to_csv(per_device_output_path, index=False, float_format='%.4f', sep=';', decimal=',')
    print(f"Per-device aggregated results saved to: {per_device_output_path}")

if __name__ == "__main__":
    main()

import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import datetime, timedelta
import argparse
import sys

def parse_request_log(file_path, aggregation_level='S', aggregate=True):
    """Parse request log CSV and compute latency metrics."""
    df = pd.read_csv(file_path)
    
    # Convert timestamps and adjust timezone (assuming +2 hours correction)
    for col in ['Arrival Time', 'Queue Exit Time', 'Completion Time']:
        df[col] = pd.to_datetime(df[col], unit='s') + pd.Timedelta(hours=2)
    
    # Calculate time metrics
    df['Queue Time'] = (df['Queue Exit Time'] - df['Arrival Time']).dt.total_seconds()
    df['Excess Latency'] = df['Latency'] - df['Requested Latency']
    
    # Replace negative Excess Latency with 0
    df['Excess Latency'] = df['Excess Latency'].clip(lower=0)

    # Calculate percentage excess latency
    df['Percentage Excess Latency'] = (df['Excess Latency'] / df['Requested Latency']) * 100

       
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


def analyze_logs(logs, plot_latency=True, plot_power=True, plot_temperature=True,
                 plot_gpu_freq=False, single_plot=False, align_zero=False, subplots=False,
                 aggregation_level='S', aggregate=True, interval_ms=200):
    """Analyze and plot log data based on specified parameters."""
    if single_plot and subplots:
        sys.exit("Error: --single-plot and --subplots cannot be used together.")

    # Determine global axis limits
    axis_limits = {
        'latency': (float('inf'), 0),
        'temperature': (float('inf'), 0),
        'power': (float('inf'), 0),
        'gpu_freq': (float('inf'), 0)
    }

    # Collect global min/max values
    for req_log, tegra_log in logs:
        req_df = parse_request_log(req_log, aggregation_level, aggregate)
        tegra_df = parse_tegrastats_log(tegra_log)

        if plot_latency:
            axis_limits['latency'] = (
                min(axis_limits['latency'][0], req_df[['Queue Time', 'Excess Latency', 'Latency']].min().min()),
                max(axis_limits['latency'][1], req_df[['Queue Time', 'Excess Latency', 'Latency']].max().max())
            )
        if plot_temperature:
            axis_limits['temperature'] = (
                min(axis_limits['temperature'][0], tegra_df['Temperature'].min()),
                max(axis_limits['temperature'][1], tegra_df['Temperature'].max())
            )
        if plot_power:
            axis_limits['power'] = (
                min(axis_limits['power'][0], tegra_df['Power_Sum'].min()),
                max(axis_limits['power'][1], tegra_df['Power_Sum'].max())
            )
        if plot_gpu_freq:
            axis_limits['gpu_freq'] = (
                min(axis_limits['gpu_freq'][0], tegra_df['GPU_Freq'].min()),
                max(axis_limits['gpu_freq'][1], tegra_df['GPU_Freq'].max())
            )

    # Determine which data to plot and their order
    plot_types = []
    if plot_latency:
        plot_types.append('latency')
    if plot_temperature:
        plot_types.append('temperature')
    if plot_power:
        plot_types.append('power')
    if plot_gpu_freq:
        plot_types.append('gpu_freq')

    # Initialize plot
    if single_plot:
        fig, main_ax = plt.subplots(figsize=(20, 10))
    elif subplots:
        fig, axs = plt.subplots(len(logs), 1, figsize=(16, 8 * len(logs)), sharex=True)
        if len(logs) == 1:
            axs = [axs]
    else:
        fig, main_ax = None, None

    # Process each log pair
    for idx, (req_log, tegra_log) in enumerate(logs):
        req_df = parse_request_log(req_log, aggregation_level, aggregate)
        tegra_df = parse_tegrastats_log(tegra_log)
        label = get_log_label(req_log)

        # Align timestamps to zero if requested
        if align_zero:
            req_start = req_df['Rounded Arrival Time'].iloc[0]
            tegra_start = tegra_df['Timestamp'].iloc[0]
            req_df['Rounded Arrival Time'] = (req_df['Rounded Arrival Time'] - req_start).dt.total_seconds()
            tegra_df['Timestamp'] = (tegra_df['Timestamp'] - tegra_start).dt.total_seconds()

        # Calculate statistics
        mean_excess = req_df['Excess Latency'].mean()
        total_energy = calculate_energy(tegra_df, interval_ms)
        mean_percentage_excess = req_df['Percentage Excess Latency'].mean()

        # Calculate percentages of requests and frames within latency constraint
        within_latency_requests = (req_df['Excess Latency'] == 0).mean() * 100
        within_latency_frames = within_latency_requests  # Assuming each request is a frame

        # Print stats
        print(f"\n{label} Stats:")
        print(f"Mean Excess Latency: {mean_excess:.2f}s")
        print(f"Mean Percentage Excess Latency: {mean_percentage_excess:.2f}%")
        print(f"Total Energy: {total_energy:.1f} J")
        print(f"Requests within Latency Constraint: {within_latency_requests:.2f}%")
        print(f"Frames within Latency Constraint: {within_latency_frames:.2f}%")

        # Select current axis
        if subplots:
            ax = axs[idx]
        else:
            ax = main_ax if single_plot else plt.gca()

        # Create twin axes for additional metrics
        axes = [ax]
        if len(plot_types) > 1:
            for i in range(1, len(plot_types)):
                new_ax = ax.twinx()
                new_ax.spines['right'].set_position(('outward', 60 * i))
                axes.append(new_ax)

        # Plot data based on type
        for i, plot_type in enumerate(plot_types):
            current_ax = axes[i]
            if plot_type == 'latency':
                current_ax.bar(req_df['Rounded Arrival Time'], req_df['Queue Time'], 
                               width=2, alpha=0.7, label=f'{label} Queue Time')
                current_ax.bar(req_df['Rounded Arrival Time'], req_df['Excess Latency'],
                               bottom=req_df['Latency'] - req_df['Excess Latency'],
                               width=2, alpha=0.7, label=f'{label} Excess Latency')
                current_ax.bar(req_df['Rounded Arrival Time'], req_df['Latency'],
                               width=2, alpha=0.1, label=f'{label} Total Latency')
                current_ax.set_ylabel('Latency (s)')
                current_ax.set_ylim(axis_limits['latency'])

            elif plot_type == 'temperature':
                current_ax.plot(tegra_df['Timestamp'], tegra_df['Temperature'], 'r-', label=f'{label} Temp')
                current_ax.set_ylabel('Temp (°C)', color='r')
                current_ax.set_ylim(axis_limits['temperature'])

            elif plot_type == 'power':
                current_ax.plot(tegra_df['Timestamp'], tegra_df['Power_Sum'], 'b-.', label=f'{label} Power')
                current_ax.set_ylabel('Power (mW)', color='b')
                current_ax.set_ylim(axis_limits['power'])

            elif plot_type == 'gpu_freq':
                current_ax.plot(tegra_df['Timestamp'], tegra_df['GPU_Freq'], 'g--', label=f'{label} GPU Freq')
                current_ax.set_ylabel('GPU Freq (MHz)', color='g')
                current_ax.set_ylim(axis_limits['gpu_freq'])

            current_ax.set_xlabel('Time (s)' if align_zero else 'Timestamp')
            current_ax.grid(True)

        # Combine legends
        handles, labels = [], []
        for a in axes:
            h, l = a.get_legend_handles_labels()
            handles.extend(h)
            labels.extend(l)
        ax.legend(handles, labels, loc='upper right')

        # Add stats annotation
        stats_text = (
            f"{label}\n"
            f"Energy: {total_energy:.1f} J\n"
            f"Mean Excess: {mean_excess:.2f}s\n"
            f"Mean % Excess: {mean_percentage_excess:.2f}%\n"
            f"Requests within Constraint: {within_latency_requests:.2f}%\n"
            f"Frames within Constraint: {within_latency_frames:.2f}%"
        )
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                va='top', ha='left', bbox=dict(facecolor='white', alpha=0.8))

        if not single_plot and not subplots:
            plt.title('Server Performance Analysis')
            plt.show()

    if single_plot or subplots:
        plt.tight_layout()
        plt.show()



def main():
    parser = argparse.ArgumentParser(description='Analyze server performance logs.')
    parser.add_argument('--logs', nargs='+', required=True,
                        help='List of (request_log,tegrastats_log) pairs')
    parser.add_argument('--plot-latency', action='store_true', help='Plot latency metrics')
    parser.add_argument('--plot-power', action='store_true', help='Plot power consumption')
    parser.add_argument('--plot-temperature', action='store_true', help='Plot CPU temperature')
    parser.add_argument('--plot-gpu-freq', action='store_true', help='Plot GPU frequency')
    parser.add_argument('--single-plot', action='store_true', help='Overlay all data in one plot')
    parser.add_argument('--align-zero', action='store_true', help='Align timestamps to start at 0')
    parser.add_argument('--subplots', action='store_true', help='Create separate subplots for each log pair')
    parser.add_argument('--aggregation-level', default='S', help='Set the aggregation level (e.g., S for seconds, T for minutes)')
    parser.add_argument('--no-aggregate', action='store_true', help='Disable aggregation of request logs')
    parser.add_argument('--tegrastats-interval', type=int, default=200, help='Sampling interval for tegrastats in milliseconds')
    args = parser.parse_args()

    logs = [tuple(pair.split(',')) for pair in args.logs]
    analyze_logs(
        logs,
        plot_latency=args.plot_latency,
        plot_power=args.plot_power,
        plot_temperature=args.plot_temperature,
        plot_gpu_freq=args.plot_gpu_freq,
        single_plot=args.single_plot,
        align_zero=args.align_zero,
        subplots=args.subplots,
        aggregation_level=args.aggregation_level,
        aggregate=not args.no_aggregate,
        interval_ms=args.tegrastats_interval
    )

if __name__ == '__main__':
    main()

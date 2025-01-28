import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import datetime, timedelta
import argparse
import sys

# Function to parse the latency CSV
def parse_latency_csv(file_path):
    df = pd.read_csv(file_path)
    return df

# Function to parse the tegrastats log
def parse_tegrastats_log(file_path):
    timestamps = []
    power_sum = []
    temperatures = []

    with open(file_path, 'r') as file:
        for line in file:
            # Extract timestamp
            time_str = line.split()[0] + ' ' + line.split()[1]
            timestamp = datetime.strptime(time_str, '%m-%d-%Y %H:%M:%S')
            timestamps.append(timestamp)

            # Extract power data
            cpu_power_match = re.search(r'CPU (\d+)mW', line)
            gpu_power_match = re.search(r'GPU (\d+)mW', line)
            soc_power_match = re.search(r'SOC (\d+)mW', line)
            cv_power_match = re.search(r'CV (\d+)mW', line)
            vddrq_power_match = re.search(r'VDDRQ (\d+)mW', line)
            sys5v_power_match = re.search(r'SYS5V (\d+)mW', line)

            # Handle missing power data
            cpu_power_val = int(cpu_power_match.group(1)) if cpu_power_match else 0
            gpu_power_val = int(gpu_power_match.group(1)) if gpu_power_match else 0
            soc_power_val = int(soc_power_match.group(1)) if soc_power_match else 0
            cv_power_val = int(cv_power_match.group(1)) if cv_power_match else 0
            vddrq_power_val = int(vddrq_power_match.group(1)) if vddrq_power_match else 0
            sys5v_power_val = int(sys5v_power_match.group(1)) if sys5v_power_match else 0

            # Calculate total power sum
            total_power = cpu_power_val + gpu_power_val + soc_power_val + cv_power_val + vddrq_power_val + sys5v_power_val
            power_sum.append(total_power)

            # Extract temperature
            temperature_match = re.search(r'CPU@([\d.]+)C', line)
            # Handle missing temperature data
            temperatures.append(float(temperature_match.group(1)) if temperature_match else 0)

    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Power_Sum': power_sum,
        'Temperature': temperatures
    })
    return df

def get_log_label(filename):
    if "loud_request_log" in filename:
        return "LoudScheduler"
    elif "stress_request_log" in filename:
        return "StressTest"
    elif "round_robin_request_log" in filename:
        return "RoundRobin"
    elif "random_request_log" in filename:
        return "RandomScheduler"
    elif "loud_tegrastats" in filename:
        return "LoudTegrastats"
    elif "stress_tegrastats" in filename:
        return "StressTegrastats"
    elif "round_robin_tegrastats" in filename:
        return "RoundRobinTegrastats"
    elif "random_tegrastats" in filename:
        return "RandomTegrastats"
    else:
        return filename

def analyze_logs(logs, plot_latency=True, plot_power=True, plot_temperature=True, single_plot=False, align_zero=False, subplots=False):
    # Ensure --single-plot and --subplots are not used together
    if single_plot and subplots:
        sys.exit("Error: --single-plot and --subplots cannot be used together.")

    # Determine global min and max values for consistent y-axis limits
    min_latency, max_latency = float('inf'), 0
    min_temperature, max_temperature = float('inf'), 0
    min_power, max_power = float('inf'), 0

    for request_log, tegrastats_log in logs:
        # Load the data
        latency_df = parse_latency_csv(request_log)
        power_temp_df = parse_tegrastats_log(tegrastats_log)

        # Calculate additional metrics for latency
        latency_df['Queue Time'] = (pd.to_datetime(latency_df['Queue Exit Time'], unit='s') - pd.to_datetime(latency_df['Arrival Time'], unit='s')).dt.total_seconds()
        latency_df['Excess Latency'] = (latency_df['Latency'] - latency_df['Requested Latency'])

        # Remove negative latency values
        latency_df = latency_df[(latency_df['Queue Time'] >= 0) & (latency_df['Excess Latency'] >= 0) & (latency_df['Latency'] >= 0)]

        # Update global min and max values
        min_latency = min(min_latency, latency_df[['Queue Time', 'Excess Latency', 'Latency']].min().min())
        max_latency = max(max_latency, latency_df[['Queue Time', 'Excess Latency', 'Latency']].max().max())
        min_temperature = min(min_temperature, power_temp_df['Temperature'].min())
        max_temperature = max(max_temperature, power_temp_df['Temperature'].max())
        min_power = min(min_power, power_temp_df['Power_Sum'].min())
        max_power = max(max_power, power_temp_df['Power_Sum'].max())

    if single_plot:
        fig, ax1 = plt.subplots(figsize=(16, 8))
        fig.suptitle('Server Latency, Temperature, and Power Consumption Analysis', fontsize=16, fontweight='bold')

    if subplots:
        fig, axs = plt.subplots(len(logs), 1, figsize=(16, 8 * len(logs)), sharex=True)
        fig.suptitle('Server Latency, Temperature, and Power Consumption Analysis', fontsize=16, fontweight='bold')

    for index, (request_log, tegrastats_log) in enumerate(logs):
        # Load the data
        latency_df = parse_latency_csv(request_log)
        power_temp_df = parse_tegrastats_log(tegrastats_log)

        # Convert timestamps to datetime for synchronization
        latency_df['Arrival Time'] = pd.to_datetime(latency_df['Arrival Time'], unit='s') + pd.Timedelta(hours=2)
        latency_df['Queue Exit Time'] = pd.to_datetime(latency_df['Queue Exit Time'], unit='s') + pd.Timedelta(hours=2)
        latency_df['Completion Time'] = pd.to_datetime(latency_df['Completion Time'], unit='s') + pd.Timedelta(hours=2)

        # Calculate additional metrics for latency
        latency_df['Queue Time'] = (latency_df['Queue Exit Time'] - latency_df['Arrival Time']).dt.total_seconds()
        latency_df['Excess Latency'] = (latency_df['Latency'] - latency_df['Requested Latency'])

        # Remove negative latency values
        latency_df = latency_df[(latency_df['Queue Time'] >= 0) & (latency_df['Excess Latency'] >= 0) & (latency_df['Latency'] >= 0)]

        # Group by rounded 'Arrival Time' to the nearest second or desired granularity
        latency_df['Rounded Arrival Time'] = latency_df['Arrival Time'].dt.floor('S')  # You can adjust the 'S' to 'min' or other as needed

        # Select only numeric columns for averaging
        numeric_cols = latency_df.select_dtypes(include='number').columns
        latency_grouped = latency_df.groupby('Rounded Arrival Time')[numeric_cols].mean().reset_index()

        # Use latency_grouped for plotting
        latency_df = latency_grouped

        # Align timestamps to start from zero if requested
        if align_zero:
            latency_start_time = latency_df['Rounded Arrival Time'].iloc[0]
            power_temp_start_time = power_temp_df['Timestamp'].iloc[0]
            latency_df['Rounded Arrival Time'] = (latency_df['Rounded Arrival Time'] - latency_start_time).dt.total_seconds()
            power_temp_df['Timestamp'] = (power_temp_df['Timestamp'] - power_temp_start_time).dt.total_seconds()

        # Calculate statistics
        mean_excess_latency = latency_df['Excess Latency'].mean()
        median_excess_latency = latency_df['Excess Latency'].median()

        # Determine the duration based on the type of Timestamp values
        if isinstance(power_temp_df['Timestamp'].iloc[0], (pd.Timestamp, datetime)):
            # If timestamps are datetime objects
            total_duration_seconds = (power_temp_df['Timestamp'].iloc[-1] - power_temp_df['Timestamp'].iloc[0]).total_seconds()
        else:
            # If timestamps are already in seconds
            total_duration_seconds = power_temp_df['Timestamp'].iloc[-1] - power_temp_df['Timestamp'].iloc[0]

        # Calculate total energy used
        total_energy_used = (power_temp_df['Power_Sum'].sum() / 1000) * (total_duration_seconds / len(power_temp_df))

        # Print the head of the dataframes
        print(f"\nHead of Latency DataFrame for {request_log}:")
        print(latency_df.head())

        print(f"\nHead of Power and Temperature DataFrame for {tegrastats_log}:")
        print(power_temp_df.head())

        # Determine which axis to use
        ax = ax1 if single_plot else (axs[index] if subplots else None)

        # Create a new plot for each log if not using a single plot or subplots
        if ax is None:
            fig, ax = plt.subplots(figsize=(16, 8))
            fig.suptitle(f'Server Latency, Temperature, and Power Consumption Analysis for {get_log_label(request_log)}', fontsize=16, fontweight='bold')

        # Plot latency data
        if plot_latency:
            ax.bar(latency_df['Rounded Arrival Time'], latency_df['Queue Time'], label=f'Queue Time ({get_log_label(request_log)})', width=2, alpha=0.7)
            ax.bar(latency_df['Rounded Arrival Time'], latency_df['Excess Latency'], 
                   label=f'Excess Latency ({get_log_label(request_log)})', 
                   width=2, alpha=0.7, 
                   bottom=latency_df['Latency'] - latency_df['Excess Latency'])
            ax.bar(latency_df['Rounded Arrival Time'], latency_df['Latency'], label=f'Total Latency ({get_log_label(request_log)})', width=2, alpha=0.1)
            ax.set_ylim(min_latency, max_latency)

        # Plot temperature data
        if plot_temperature:
            ax2 = ax.twinx()
            ax2.plot(power_temp_df['Timestamp'], power_temp_df['Temperature'], label=f'Temperature (°C) ({get_log_label(tegrastats_log)})', linewidth=2, color='tab:red')
            ax2.set_ylim(min_temperature, max_temperature)
            ax2.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold', color='tab:red')
            ax2.tick_params(axis='y', labelcolor='tab:red')

        # Plot power consumption data
        if plot_power:
            ax3 = ax.twinx()
            ax3.spines['right'].set_position(('outward', 60))
            ax3.plot(power_temp_df['Timestamp'], power_temp_df['Power_Sum'], label=f'Total Power (mW) ({get_log_label(tegrastats_log)})', linestyle='-.', linewidth=2, color='tab:blue')
            ax3.set_ylim(min_power, max_power)
            ax3.set_ylabel('Power (mW)', fontsize=12, fontweight='bold', color='tab:blue')
            ax3.tick_params(axis='y', labelcolor='tab:blue')

        # Set labels and format x-axis
        ax.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        
        # Set main y-axis label based on the data being plotted
        if plot_latency:
            ax.set_ylabel('Latency (s)', fontsize=12, fontweight='bold')
        elif plot_temperature:
            ax.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold', color='tab:red')
            ax.tick_params(axis='y', labelcolor='tab:red')
        elif plot_power:
            ax.set_ylabel('Power (mW)', fontsize=12, fontweight='bold', color='tab:blue')
            ax.tick_params(axis='y', labelcolor='tab:blue')

        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

        # Add legends for temperature and power
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        lines, labels = ax.get_legend_handles_labels()
        if plot_temperature:
            lines2, labels2 = ax2.get_legend_handles_labels()
        else:
            lines2, labels2 = [], []
        if plot_power:
            lines3, labels3 = ax3.get_legend_handles_labels()
        else:
            lines3, labels3 = [], []
        ax.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc='upper right', fontsize=10)

        # Add a text box for statistics
        textstr = (f'Energy Used: {total_energy_used:.2f} J\n'
                   f'Mean Excess Latency: {mean_excess_latency:.2f} s\n'
                   f'Median Excess Latency: {median_excess_latency:.2f} s')
        props = dict(boxstyle='round,pad=0.5', facecolor='lightgrey', edgecolor='grey', alpha=0.5)
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)

        # Show the plot if not using a single plot or subplots
        if not single_plot and not subplots:
            plt.show()

    # Show the combined plot if using a single plot or subplots
    if single_plot or subplots:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Analyze server logs for latency, power, and temperature.')
    parser.add_argument('--logs', nargs='+', help='List of tuples with request log and tegrastats log paths.', required=True)
    parser.add_argument('--plot-latency', action='store_true', help='Plot latency data.')
    parser.add_argument('--plot-power', action='store_true', help='Plot power data.')
    parser.add_argument('--plot-temperature', action='store_true', help='Plot temperature data.')
    parser.add_argument('--single-plot', action='store_true', help='Plot all logs on a single plot.')
    parser.add_argument('--align-zero', action='store_true', help='Align logs to start from time zero.')
    parser.add_argument('--subplots', action='store_true', help='Create vertical subplots for each log.')

    args = parser.parse_args()

    # Convert input logs to list of tuples
    logs = [tuple(log.split(',')) for log in args.logs]

    analyze_logs(logs, plot_latency=args.plot_latency, plot_power=args.plot_power, plot_temperature=args.plot_temperature, single_plot=args.single_plot, align_zero=args.align_zero, subplots=args.subplots)

if __name__ == '__main__':
    main()

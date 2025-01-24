import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
from datetime import datetime

# Function to parse the latency CSV
def parse_latency_csv(file_path):
    df = pd.read_csv(file_path)
    return df

# Function to parse the tegrastats log
def parse_tegrastats_log(file_path):
    timestamps = []
    cpu_power = []
    gpu_power = []
    soc_power = []
    cv_power = []
    vddrq_power = []
    sys5v_power = []
    power_sum = []
    temperatures = []

    with open(file_path, 'r') as file:
        for line in file:
            # Extract timestamp
            time_str = line.split()[0] + ' ' + line.split()[1]
            timestamp = datetime.strptime(time_str, '%m-%d-%Y %H:%M:%S')
            timestamps.append(timestamp)

            # Extract CPU and SOC power
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

logs = [('2025-01-24_18:33:28_loud_request_log.csv', 'measurements/power/agx-xavier-00/home/iloudaros/2025-01-24_18:28:38_loud_tegrastats'),
         ('2025-01-24_18:40:20_round_robin_request_log.csv','measurements/power/agx-xavier-00/home/iloudaros/2025-01-24_18:34:38_round_robin_tegrastats'),
         ('2025-01-24_18:47:13_random_request_log.csv','measurements/power/agx-xavier-00/home/iloudaros/2025-01-24_18:41:30_random_tegrastats')]


for request_log, tegrastats_log in logs:
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

    # Filter out rows with negative Excess Latency
    latency_df = latency_df[latency_df['Excess Latency'] >= 0]

    # Calculate statistics
    mean_excess_latency = latency_df['Excess Latency'].mean()
    median_excess_latency = latency_df['Excess Latency'].median()
    total_energy_used = (power_temp_df['Power_Sum'].sum() / 1000) * (power_temp_df['Timestamp'].iloc[-1] - power_temp_df['Timestamp'].iloc[0]).total_seconds() / len(power_temp_df)
    
    # Print the head of the dataframes
    print("\nHead of Latency DataFrame:")
    print(latency_df.head())

    print("\nHead of Power and Temperature DataFrame:")
    print(power_temp_df.head())

    # Plotting
    fig, ax1 = plt.subplots(figsize=(16, 8))
    fig.suptitle('Server Latency, Temperature, and Power Consumption Analysis', fontsize=16)

    # Plot latency data
    ax1.bar(latency_df['Arrival Time'], latency_df['Queue Time'], color='orange', label='Queue Time', width=0.0001, alpha=0.7)
    ax1.bar(latency_df['Arrival Time'], latency_df['Excess Latency'], color='red', label='Excess Latency', width=0.0001, alpha=0.7)
    ax1.bar(latency_df['Arrival Time'], latency_df['Latency'], color='lightblue', label='Total Latency', width=0.0001, alpha=0.1)

    # Set labels and format x-axis
    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Latency (s)', fontsize=12)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # Plot temperature data
    ax2 = ax1.twinx()
    ax2.plot(power_temp_df['Timestamp'], power_temp_df['Temperature'], color='green', label='Temperature (°C)', linewidth=2)
    ax2.set_ylabel('Temperature (°C)', color='green', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='green')

    # Plot power consumption data
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))
    ax3.plot(power_temp_df['Timestamp'], power_temp_df['Power_Sum'], color='brown', label='Total Power (mW)', linestyle='-.', linewidth=2)
    ax3.set_ylabel('Power (mW)', fontsize=12)
    ax3.tick_params(axis='y', labelcolor='purple')

    # Add legends for temperature and power
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc='upper right', fontsize=10)

    # Add a text box for statistics
    textstr = f'Energy Used: {total_energy_used:.2f} J\nMean Excess Latency: {mean_excess_latency:.2f} s\nMedian Excess Latency: {median_excess_latency:.2f} s'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)

    plt.show()

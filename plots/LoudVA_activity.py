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
    soc_power = []
    temperatures = []

    with open(file_path, 'r') as file:
        for line in file:
            # Extract timestamp
            time_str = line.split()[0] + ' ' + line.split()[1]
            timestamp = datetime.strptime(time_str, '%m-%d-%Y %H:%M:%S')
            timestamps.append(timestamp)

            # Extract CPU and SOC power
            cpu_power_match = re.search(r'CPU (\d+)mW', line)
            soc_power_match = re.search(r'SOC (\d+)mW', line)

            # Handle missing power data
            cpu_power.append(int(cpu_power_match.group(1)) if cpu_power_match else 0)
            soc_power.append(int(soc_power_match.group(1)) if soc_power_match else 0)

            # Extract temperature
            temperature_match = re.search(r'CPU@(\d+)C', line)
            # Handle missing temperature data
            temperatures.append(int(temperature_match.group(1)) if temperature_match else 0)

    df = pd.DataFrame({
        'Timestamp': timestamps,
        'CPU_Power': cpu_power,
        'SOC_Power': soc_power,
        'Temperature': temperatures
    })
    return df

# Load the data
latency_df = parse_latency_csv('/home/louduser/LoudVA/2025-01-24_12:21:06_loud_request_log.csv')
power_temp_df = parse_tegrastats_log('/home/louduser/LoudVA/measurements/power/agx-xavier-00/home/iloudaros/2025-01-24_12:16:08_loud_tegrastats')

# Convert timestamps to datetime for synchronization
latency_df['Arrival Time'] = pd.to_datetime(latency_df['Arrival Time'], unit='s')
latency_df['Queue Exit Time'] = pd.to_datetime(latency_df['Queue Exit Time'], unit='s')
latency_df['Completion Time'] = pd.to_datetime(latency_df['Completion Time'], unit='s')

# Calculate additional metrics for latency
latency_df['Queue Time'] = (latency_df['Queue Exit Time'] - latency_df['Arrival Time']).dt.total_seconds()
latency_df['Excess Latency'] = (latency_df['Latency'] - latency_df['Requested Latency']).clip(lower=0)

# Plotting
fig, ax1 = plt.subplots(figsize=(14, 7))

# Plot latency data
ax1.bar(latency_df['Arrival Time'], latency_df['Latency'], color='lightblue', label='Total Latency', width=0.0001)
ax1.bar(latency_df['Arrival Time'], latency_df['Queue Time'], color='orange', label='Queue Time', width=0.0001)
ax1.bar(latency_df['Arrival Time'], latency_df['Excess Latency'], color='red', label='Excess Latency', width=0.0001)

# Set labels and format x-axis
ax1.set_xlabel('Time')
ax1.set_ylabel('Latency (s)')
ax1.set_title('Server Latency, Temperature, and Power Consumption Analysis')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
fig.autofmt_xdate()

# Plot temperature data
ax2 = ax1.twinx()
ax2.plot(power_temp_df['Timestamp'], power_temp_df['Temperature'], color='green', label='Temperature (°C)')
ax2.set_ylabel('Temperature (°C)', color='green')
ax2.tick_params(axis='y', labelcolor='green')

# Plot power consumption data
ax3 = ax1.twinx()
ax3.spines['right'].set_position(('outward', 60))
ax3.plot(power_temp_df['Timestamp'], power_temp_df['CPU_Power'], color='purple', label='CPU Power (mW)')
ax3.plot(power_temp_df['Timestamp'], power_temp_df['SOC_Power'], color='brown', label='SOC Power (mW)')
ax3.set_ylabel('Power (mW)', color='purple')
ax3.tick_params(axis='y', labelcolor='purple')

# Add legends for temperature and power
fig.tight_layout()
fig.legend(loc='upper right', bbox_to_anchor=(1, 0.9), bbox_transform=ax1.transAxes)

plt.show()

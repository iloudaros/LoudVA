import pandas as pd
import matplotlib.pyplot as plt

# Define the path to the CSV log file
CSV_LOG_FILE = 'request_log.csv'

def plot_request_latency(csv_file):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Convert the arrival and completion times to datetime
    df['Arrival Time'] = pd.to_datetime(df['Arrival Time'], unit='s')
    df['Completion Time'] = pd.to_datetime(df['Completion Time'], unit='s')

    # Calculate latency in seconds
    df['Latency'] = (df['Completion Time'] - df['Arrival Time']).dt.total_seconds()

    # Plot the latency over time
    plt.figure(figsize=(12, 6))
    plt.plot(df['Arrival Time'], df['Latency'], marker='o', linestyle='-')
    plt.title('Request Latency Over Time')
    plt.xlabel('Arrival Time')
    plt.ylabel('Latency (seconds)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Show the plot
    plt.show()

# Call the function to plot the data
plot_request_latency(CSV_LOG_FILE)

import csv
from collections import defaultdict

# Device class to store the device information
class Device:
    def __init__(self, name, ip, frequencies, batch_sizes, profiles):
        self.name = name
        self.ip = ip
        self.frequencies = frequencies
        self.batch_sizes = batch_sizes
        self.profiles = profiles  # Dictionary of (freq, batch_size) -> (throughput, latency, energy)
        self.current_freq = min(frequencies)
        self.current_batch_size = 1
        self.max_freq = max(frequencies)
        self.min_freq = min(frequencies)
    
    def get_latency(self, freq, batch_size):
        return self.profiles[(freq, batch_size)][1]
    
    def get_energy_consumption(self, freq, batch_size):
        return self.profiles[(freq, batch_size)][2]
    
    def get_throughput(self, freq, batch_size):
        return self.profiles[(freq, batch_size)][0]

    def set_frequency(self, freq):
        self.current_freq = freq
    
    def set_batch_size(self, size):
        self.current_batch_size = size






# Function to read the CSV file and convert it to a dictionary
def csv_to_dict(file_path):
    # Initialize an empty dictionary to store the results
    result = defaultdict(list)

    # Open the CSV file
    with open(file_path, 'r') as csvfile:
        # Create a CSV reader object
        csvreader = csv.reader(csvfile)
        
        # Skip the header
        next(csvreader)
        
        # Iterate through each row in the CSV
        for row in csvreader:
            # Extract the frequency, label, throughput, and z from the row
            frequency = int(row[4])
            batch_size = int(row[3])
            throughput = float(row[0])
            energy = float(row[1])
            latency = float(row[2])
            
            # Use (frequency, label) as the key and (throughput, latency, z) as the value
            result[(frequency, batch_size)]=(throughput, latency, energy)
    
    return dict(result)








# Collect dictionary data from the CSV files
agx_path = '/home/louduser/LoudVA/measurements/archive/Representative/agx-xavier-00/measurements/agx-xavier-00_filtered_freqs.csv'
nx_path = '/home/louduser/LoudVA/measurements/archive/Representative/xavier-nx-00/measurements/xavier-nx-00_filtered_freqs.csv'
nano_path = '/home/louduser/LoudVA/measurements/archive/Representative/LoudJetson0/measurements/LoudJetson0_filtered_freqs.csv'

agx_dict = csv_to_dict(agx_path)
nx_dict = csv_to_dict(nx_path)
nano_dict = csv_to_dict(nano_path)


# Declare the frequencies
nano_freqs = [76800000, 153600000, 230400000, 307200000, 384000000, 460800000, 537600000, 614400000, 691200000, 768000000, 844800000, 921600000] 
agx_freqs = [ 114750000, 216750000, 318750000, 420750000, 522750000, 624750000, 675750000, 828750000, 905250000, 1032750000, 1198500000, 1236750000, 1338750000, 1377000000]
nx_freqs = [ 114750000, 204000000, 306000000, 408000000, 510000000, 599250000, 701250000, 752250000, 803250000, 854250000, 905250000, 956250000, 1007250000, 1058250000, 1109250000] 

# Define the devices
devices = [
    Device('agx-xavier-00', '192.168.0.112', nano_freqs, [1, 2, 4, 8, 16, 32], agx_dict),
    Device('xavier-nx-00', '192.168.0.110', nx_freqs, [1, 2, 4, 8, 16, 32], nx_dict),
    Device('xavier-nx-01', '192.168.0.111', nx_freqs, [1, 2, 4, 8, 16, 32], nx_dict),
    Device('LoudJetson0', '192.168.0.120', nano_freqs, [1, 2, 4, 8, 16, 32], nano_dict),
    Device('LoudJetson1', '192.168.0.121', nano_freqs, [1, 2, 4, 8, 16, 32], nano_dict),
    Device('LoudJetson2', '192.168.0.122', nano_freqs, [1, 2, 4, 8, 16, 32], nano_dict)
    ]


if __name__ == '__main__':
    print("Device data loaded successfully.")
    print("Devices:")
    for device in devices:
        print(f"Device: {device.name}, IP: {device.ip}, Frequencies: {device.frequencies}, Batch Sizes: {device.batch_sizes}")
        print(f"Profiles: {device.profiles}")
        print(f"Current Frequency: {device.current_freq}, Current Batch Size: {device.current_batch_size}")
        print(f"Max Frequency: {device.max_freq}, Min Frequency: {device.min_freq}")
        print("\n")
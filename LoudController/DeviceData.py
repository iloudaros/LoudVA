from collections import defaultdict
import os
import csv
import worker_client
import triton_client
import Settings
from logging_config import setup_logging

# Configure logger
logger = setup_logging()

# Device class to store the device information
class Device:
    def __init__(self, name, ip, frequencies, profile,
                 gpu_max_freq, gpu_min_freq, architecture, num_cores, memory_speed, dram, shared_memory, memory_size, tensor_cores):
        self.name = name
        self.ip = ip
        self.frequencies = frequencies
        self.profile = profile  # Dictionary of (freq, batch_size) -> (throughput, latency, energy)

        # GPU Specifications
        self.gpu_max_freq = gpu_max_freq
        self.gpu_min_freq = gpu_min_freq
        self.architecture = architecture
        self.num_cores = num_cores
        self.memory_speed = memory_speed
        self.dram = dram
        self.shared_memory = shared_memory
        self.memory_size = memory_size
        self.tensor_cores = tensor_cores

        # Calculate Max Batch Size from profile
        self.max_batch_size = max([batch_size for (freq, batch_size) in profile.keys()])

        # Set the current frequency and batch size to the first frequency and batch size in the profile
        self.__current_freq = frequencies[4]
        self.current_batch_size = 1

    def get_latency(self, freq, batch_size):
        try:
            return self.profile[(freq, batch_size)][1]
        except KeyError:
            logger.debug(f"Profile for frequency {freq} and batch size {batch_size} not found in {self.name}.")
            return float('inf')  # Return a high latency value as a fallback

    def get_energy_consumption(self, freq, batch_size):
        try:
            return self.profile[(freq, batch_size)][2]
        except KeyError:
            logger.debug(f"Profile for frequency {freq} and batch size {batch_size} not found in {self.name}.")
            return float('inf')  # Return a high energy value as a fallback

    def get_throughput(self, freq, batch_size):
        try:
            return self.profile[(freq, batch_size)][0]
        except KeyError:
            logger.debug(f"Profile for frequency {freq} and batch size {batch_size} not found in {self.name}.")
            return 0  # Return a low throughput value as a fallback

    def set_frequency(self, freq):
        worker_client.set_gpu_frequency(self.ip, freq)
        self.__current_freq = freq
        logger.info(f"Frequency change successful for device {self.name} to {freq}")

    def get_frequency(self):
        return self.__current_freq

    def inference(self, images, batch_size):
        url = f'{self.ip}:8000'  # Triton server URL

        # Prepare the arguments for the triton_client
        args = [
            '--model-name', Settings.model_name,
            '--model-version', str(Settings.model_version),
            '--batch-size', str(batch_size),
            '--classes', str(Settings.number_of_classes),
            '--scaling', Settings.scaling,
            '--url', url,
            '--protocol', 'HTTP'
        ]

        # Add image filenames to arguments
        args.extend(images)
        logger.debug(f"Image filenames added to arguments: {images}")


        # Call the triton_client's main function
        logger.debug(f"Running inference on device {self.name} with arguments: {args}")
        return triton_client.inference(args)  # Return the response directly

def initialize_devices():
    # Get the path of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the paths to the CSV files
    agx_path = os.path.join(script_dir, '../measurements/archive/Representative/agx-xavier-00/measurements/agx-xavier-00_filtered_freqs.csv')
    nx_path = os.path.join(script_dir, '../measurements/archive/Representative/xavier-nx-00/measurements/xavier-nx-00_filtered_freqs.csv')
    nano_path = os.path.join(script_dir, '../measurements/archive/Representative/LoudJetson0/measurements/LoudJetson0_filtered_freqs.csv')
    specs_path = os.path.join(script_dir, '../data/devices/gpu_specs.csv')

    agx_profile = csv_to_dict(agx_path)
    nx_profile = csv_to_dict(nx_path)
    nano_profile = csv_to_dict(nano_path)

    specs_dict = load_gpu_specs(specs_path)

    # Declare the frequencies
    nano_freqs = [76800000, 153600000, 230400000, 307200000, 384000000, 460800000, 537600000, 614400000, 691200000, 768000000, 844800000, 921600000] 
    agx_freqs = [114750000, 216750000, 318750000, 420750000, 522750000, 624750000, 675750000, 828750000, 905250000, 1032750000, 1198500000, 1236750000, 1338750000, 1377000000]
    nx_freqs = [114750000, 204000000, 306000000, 408000000, 510000000, 599250000, 701250000, 752250000, 803250000, 854250000, 905250000, 956250000, 1007250000, 1058250000, 1109250000]

    # Define the devices
    devices = [
        #Device('agx-xavier-00', '192.168.0.112', agx_freqs, agx_profile, **specs_dict['AGX']),
        Device('xavier-nx-00', '192.168.0.110', nx_freqs, nx_profile, **specs_dict['NX']),
        Device('xavier-nx-01', '192.168.0.111', nx_freqs, nx_profile, **specs_dict['NX']),
        Device('LoudJetson0', '192.168.0.120', nano_freqs, nano_profile, **specs_dict['Nano']),
        Device('LoudJetson1', '192.168.0.121', nano_freqs, nano_profile, **specs_dict['Nano']),
        Device('LoudJetson2', '192.168.0.122', nano_freqs, nano_profile, **specs_dict['Nano'])
    ]
    logger.info("Devices initialized successfully")
    return devices

def csv_to_dict(file_path):
    # Initialize an empty dictionary to store the results
    result = defaultdict(list)

    try:
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
                result[(frequency, batch_size)] = (throughput, latency, energy)
        logger.info(f"Loaded profile from {file_path}")
    
    except Exception as e:
        logger.error(f"Failed to load profile from {file_path}: {e}")
    return dict(result)
    

def load_gpu_specs(file_path):
    specs = {}
    try:
        with open(file_path, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                device_type = row['Device']
                specs[device_type] = {
                    'gpu_max_freq': float(row['GPU Max Frequency (MHz)']),
                    'gpu_min_freq': float(row['GPU Min Frequency (MHz)']),
                    'architecture': row['GPU Architecture'],
                    'num_cores': int(row['GPU Number of Cores']),
                    'memory_speed': float(row['Memory Speed (GB/s)']),
                    'dram': row['DRAM'] == 'Yes',
                    'shared_memory': row['Shared Memory'] == 'Yes',
                    'memory_size': float(row['Memory Size (GB)']),
                    'tensor_cores': int(row['Tensor Cores']) if row['Tensor Cores'] != 'N/A' else None
                }
        logger.info(f"Loaded GPU specs from {file_path}")
    except Exception as e:
        logger.error(f"Failed to load GPU specs from {file_path}: {e}")

    return specs

if __name__ == '__main__':
    devices = initialize_devices()
    print("Device data loaded successfully.")
    print("Devices:")
    for device in devices:
        print(f"Device: {device.name}, IP: {device.ip}, Frequencies: {device.frequencies}")
        print(f"Profile: {device.profile}")
        print(f"Current Frequency: {device.current_freq}, Current Batch Size: {device.current_batch_size}")
        print(f"Max Frequency: {device.gpu_max_freq}, Min Frequency: {device.gpu_min_freq}")
        print(f"GPU Max Frequency: {device.gpu_max_freq} MHz, GPU Min Frequency: {device.gpu_min_freq} MHz")
        print(f"Architecture: {device.architecture}, Number of Cores: {device.num_cores}")
        print(f"Memory Speed: {device.memory_speed} GB/s, DRAM: {device.dram}, Shared Memory: {device.shared_memory}")
        print(f"Memory Size: {device.memory_size} GB, Tensor Cores: {device.tensor_cores}")
        print("\n")

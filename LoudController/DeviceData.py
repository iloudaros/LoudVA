from collections import defaultdict
import os
import csv
import json
import worker_client
import triton_client
import Settings as settings
import time
from logging_config import setup_logging
from LoudPredictor.costs.agnostic.LoudCostPredictor import LoudCostPredictor
import threading


# Configure logger
logger = setup_logging()

# Initialize and train the LoudCostPredictor
 
predictor = LoudCostPredictor('/home/louduser/LoudVA/LoudController/LoudPredictor/costs/agnostic/data.csv')
logger.info("Training the LoudCostPredictor...")
start_time = time.time()
predictor.train()
end_time = time.time()
logger.info(f"LoudCostPredictor training complete. Training time: {end_time - start_time} seconds.")


if settings.use_prediction:
    logger.info("Using prediction model for decision making.")
else:
    logger.info("Using profiling data for decision making.")

if settings.fill_missing_profile_data:
    logger.info("Filling missing profile data with predictions.")
else:
    logger.info("Not filling missing profile data with predictions.")

# Device class to store the device information
class Device:
    def __init__(self, name, ip, frequencies, profile, frequency_change_delay, batch_size_change_delay,
                 gpu_max_freq, gpu_min_freq, architecture, num_cores, memory_speed, dram, shared_memory, memory_size, tensor_cores, max_batch_size=None, model_instances=1):
        
        self.name = name
        self.ip = ip
        self.frequencies = frequencies
        self.profile = profile  # Dictionary of (freq, batch_size) -> (throughput, latency, energy)
        self.last_available_time = time.time() 


        # GPU Specifications
        self.gpu_max_freq = gpu_max_freq
        self.gpu_min_freq = gpu_min_freq
        self.architecture = architecture
        self.num_cores = num_cores
        self.memory_speed = memory_speed
        self.dram = dram
        self.shared_memory = shared_memory
        self.memory_size = memory_size
        self.tensor_cores = tensor_cores if isinstance(tensor_cores, int) else 0     

        # Calculate Max Batch Size from profile
        self.max_batch_size = max([batch_size for (freq, batch_size) in profile.keys()]) if max_batch_size is None else max_batch_size

        # Set the current frequency and batch size 
        self.__current_freq = self.request_frequency()
        logger.info(f"Initial frequency on {self.name}: {self.__current_freq}")
        self.current_batch_size = 1

        # Other delays
        self.frequency_change_delay = frequency_change_delay
        self.batch_size_change_delay = batch_size_change_delay

        # Status
        self.__status = 'AVAILABLE'
        self.model_instances = model_instances
        self.current_requests = 0
        self.lock = threading.Lock()

        # Cache for storing the predicted energy and latency
        self.prediction_cache = {}        

        # Fill missing profile data or calculate prediction_cache
        if settings.use_prediction:
            self.calculate_prediction_cache()
        elif settings.fill_missing_profile_data:
            self.fill_missing_profile_data()

    def calculate_prediction_cache(self):
        # Populate the prediction cache with the predicted energy and latency for all batch sizes and frequencies
        for freq in self.frequencies:
            for batch_size in range(1, self.max_batch_size + 1):
                predicted_energy, predicted_latency = self.predict(freq, batch_size)
                self.prediction_cache[(freq, batch_size)] = (predicted_energy, predicted_latency)
                logger.debug(f"{self.name} : Predicted energy and latency for profile (f:{freq}, b:{batch_size})")

    def fill_missing_profile_data(self):
        # Fill the missing profile data with the predicted energy and latency
        for freq in self.frequencies:
            for batch_size in range(1, self.max_batch_size + 1):
                if (freq, batch_size) not in self.profile:
                    predicted_energy, predicted_latency = self.predict(freq, batch_size)
                    self.profile[(freq, batch_size)] = (self.get_throughput(freq, batch_size), predicted_latency, predicted_energy)
                    logger.debug(f"{self.name} : Filled missing profile data for (f:{freq}, b:{batch_size})")
        
        logger.info(f"{self.name} : Missing profile data filled with predictions.")


    def predict(self, freq, batch_size):
        # Check if the prediction is already in the cache
        if (freq, batch_size) in self.prediction_cache:
            return self.prediction_cache[(freq, batch_size)]

        # Use the predictor to predict the energy and latency
        predicted_energy, predicted_latency = predictor.predict({
                        'Batch Size': batch_size,
                        'Frequency': freq,
                        'GPU Max Frequency (MHz)': self.gpu_max_freq,
                        'GPU Min Frequency (MHz)': self.gpu_min_freq,
                        'GPU Number of Cores': self.num_cores,
                        'Memory Speed (GB/s)': self.memory_speed,
                        'Memory Size (GB)': self.memory_size,
                        'Tensor Cores': self.tensor_cores
                    })
        
        # Cache the prediction
        self.prediction_cache[(freq, batch_size)] = (predicted_energy, predicted_latency)
        
        return predicted_energy, predicted_latency

    def get_latency(self, freq, batch_size):
        try:
            return self.profile[(freq, batch_size)][1]
        except KeyError:
            logger.debug(f"{self.name} : No latency for profile (f:{freq}, b:{batch_size}).")
            return float('inf')  # Return a high latency value as a fallback

    def get_energy_consumption(self, freq, batch_size):
        try:
            return self.profile[(freq, batch_size)][2]
        except KeyError:
            logger.debug(f"{self.name} : No energy for profile (f:{freq}, b:{batch_size}).")
            return float('inf')  # Return a high energy value as a fallback

    def get_throughput(self, freq, batch_size):
        try:
            return self.profile[(freq, batch_size)][0]
        except KeyError:
            logger.debug(f"{self.name} : No throughput for profile (f:{freq}, b:{batch_size}).")
            return 0  # Return a low throughput value as a fallback

    def set_frequency(self, freq):
        if freq != self.__current_freq:    
            response = worker_client.set_gpu_frequency(self.ip, freq)
            self.__current_freq = freq

            if response['status_code'] == 200:
                logger.info(f"Frequency set to {freq} MHz on {self.name}")
            else:
                logger.error(f"Failed to set frequency on {self.name}: {response['message']}")
        else:
            logger.debug(f"Frequency already set to {freq} MHz on {self.name}")

    def get_frequency(self):
        return self.__current_freq

    def request_frequency(self):
        response = worker_client.get_gpu_frequency(self.ip)
        if response['status_code'] == 200:
            frequency = json.loads(response['message'])['message'].strip()
            logger.debug(f"Current frequency on {self.name}: {frequency} MHz")
            return frequency
        else:
            logger.error(f"Failed to get frequency on {self.name}: {response['message']}")
            return None
        
    def set_status(self, status):
        self.__status = status
        logger.debug(f"Device {self.name} status set to {status}")
        if status == 'AVAILABLE':
            self.last_available_time = time.time()

    def is_available(self):
        return self.__status == 'AVAILABLE'
    
    def get_status(self):
        return self.__status
    
    def health_check(self):
        response = worker_client.health_check(self.ip)
        if response['status_code'] == 200:
            logger.debug(f"Health check passed for {self.name}")
            return True
        else:
            logger.error(f"Health check failed for {self.name}: {response['message']}")
            return False
        
    def add_request(self):
        with self.lock:
            self.current_requests += 1
            logger.debug(f"Request added to {self.name}. Current requests: {self.current_requests}/{self.model_instances}")
            if self.current_requests >= self.model_instances:
                self.set_status('BUSY')
            else:
                logger.debug(f"{self.name} is still AVAILABLE")


    def end_request(self):
        with self.lock:
            self.current_requests -= 1
            logger.debug(f"Request completed on {self.name}. Current requests: {self.current_requests}/{self.model_instances}")
            if self.current_requests < self.model_instances:
                self.set_status('AVAILABLE')


    def inference(self, images, batch_size):
        url = f'{self.ip}:8000'  # Triton server URL
        # Prepare the arguments for the triton_client
        args = {
            'image_sources': images,
            'model_name': settings.model_name,
            'model_version': str(settings.model_version),
            'batch_size': batch_size,
            'classes': settings.number_of_classes,
            'scaling': settings.scaling,
            'url': url,
            'protocol': 'HTTP',
            'verbose': False,  # Set to True if you want verbose logging
            'async_set': False,
            'streaming': False
        }

        # Call the triton_client's main function
        logger.debug(f"Running inference on device {self.name}")
        response = triton_client.inference(**args)
        logger.debug(f"Response from Triton server: {response}")

        return response



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

    # Other delays
    agx_frequency_change_delay = 0.56
    agx_batch_size_change_delay = 0.5

    nx_frequency_change_delay = 0.8
    nx_batch_size_change_delay = 0.5

    nano_frequency_change_delay = 0.65
    nano_batch_size_change_delay = 0.5

    # Define the devices
    devices = [
        Device('agx-xavier-00', '147.102.37.108', agx_freqs, agx_profile, agx_frequency_change_delay, agx_batch_size_change_delay,  **specs_dict['AGX'], max_batch_size=64),
        #Device('xavier-nx-00', '192.168.0.110', nx_freqs, nx_profile, nx_frequency_change_delay, nx_batch_size_change_delay, **specs_dict['NX'], max_batch_size=8),
        #Device('xavier-nx-01', '147.102.37.122', nx_freqs, nx_profile,  nx_frequency_change_delay, nx_batch_size_change_delay, **specs_dict['NX'], max_batch_size=8),
        #Device('LoudJetson0', '192.168.0.120', nano_freqs, nano_profile, nano_frequency_change_delay, nano_batch_size_change_delay, **specs_dict['Nano'], max_batch_size=4),
        #Device('LoudJetson1', '192.168.0.121', nano_freqs, nano_profile, nano_frequency_change_delay, nano_batch_size_change_delay, **specs_dict['Nano'], max_batch_size=4),
        #Device('LoudJetson2', '192.168.0.122', nano_freqs, nano_profile, nano_frequency_change_delay, nano_batch_size_change_delay, **specs_dict['Nano'], max_batch_size=4)
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

# if __name__ == '__main__':
#     devices = initialize_devices()
#     print("Device data loaded successfully.")
#     print("Devices:")
#     for device in devices:
#         print(f"Device: {device.name}, IP: {device.ip}, Frequencies: {device.frequencies}")
#         print(f"Profile: {device.profile}")
#         print(f"Current Frequency: {device.get_frequency}, Current Batch Size: {device.current_batch_size}")
#         print(f"Max Frequency: {device.gpu_max_freq}, Min Frequency: {device.gpu_min_freq}")
#         print(f"GPU Max Frequency: {device.gpu_max_freq} MHz, GPU Min Frequency: {device.gpu_min_freq} MHz")
#         print(f"Architecture: {device.architecture}, Number of Cores: {device.num_cores}")
#         print(f"Memory Speed: {device.memory_speed} GB/s, DRAM: {device.dram}, Shared Memory: {device.shared_memory}")
#         print(f"Memory Size: {device.memory_size} GB, Tensor Cores: {device.tensor_cores}")
#         print(f'Health Check: {device.health_check()}')
#         print("\n")

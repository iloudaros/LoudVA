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
if settings.use_prediction or settings.fill_missing_profile_data:
    predictor = LoudCostPredictor('/home/iloudaros/Desktop/LoudVA/LoudController/LoudPredictor/costs/agnostic/data.csv')
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
                 gpu_max_freq, gpu_min_freq, architecture, num_cores, memory_speed, dram, shared_memory, memory_size, tensor_cores,
                 max_batch_size=None, model_instances=1, network_cost=None):
        
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

        # Initialize current frequency and batch size
        self.__current_freq = self.request_frequency()
        logger.info(f"Initial frequency on {self.name}: {self.__current_freq}")

        # Other delays
        self.frequency_change_delay = frequency_change_delay
        self.batch_size_change_delay = batch_size_change_delay

        # Status
        self.__status = 'AVAILABLE'
        self.model_instances = model_instances
        self.allowed_buffer = settings.allowed_buffer if settings.allowed_buffer is not None else 0
        self.current_requests = 0

        # Locks for thread safety. Please maintain the order of locks to avoid deadlocks.
        self.cache_lock = threading.Lock()
        self.requests_lock = threading.Lock()
        self.status_lock = threading.Lock()
        self.freq_lock = threading.Lock()


        # Cache for storing the predicted energy and latency
        self.prediction_cache = {}

        # Network cost
        self.network_cost = network_cost or []
        logger.debug(f"Initialized network costs for batch sizes 1-{len(self.network_cost)-1}")

        # Log the device initialization parameters
        logger.info(f"Device {self.name} initialized with IP {self.ip}, Frequencies: {self.frequencies}, "
                    f"Max Batch Size: {self.max_batch_size}, "
                    f"GPU Max Frequency: {self.gpu_max_freq} MHz, GPU Min Frequency: {self.gpu_min_freq} MHz, "
                    f"Architecture: {self.architecture}, Number of Cores: {self.num_cores}, "
                    f"Memory Speed: {self.memory_speed} GB/s, DRAM: {self.dram}, Shared Memory: {self.shared_memory}, "
                    f"Memory Size: {self.memory_size} GB, Tensor Cores: {self.tensor_cores}, "
                    f"Model Instances: {self.model_instances}, Allowed Buffer: {self.allowed_buffer}, "
                    f"Network Cost: {self.network_cost}")

        # Fill missing profile data or calculate prediction_cache
        if settings.use_prediction:
            logger.info(f"{self.name} : Calculating prediction cache...")
            self.calculate_prediction_cache()
        elif settings.fill_missing_profile_data:
            logger.info(f"{self.name} : Filling missing profile data...")
            self.fill_missing_profile_data()

    def calculate_prediction_cache(self):
        total_profiles = len(self.frequencies) * self.max_batch_size
        processed_profiles = 0  
        for freq in self.frequencies:
            for batch_size in range(1, self.max_batch_size + 1):
                predicted_energy, predicted_latency = self.predict(freq, batch_size)
                processed_profiles += 1
                if processed_profiles % 50 == 0:
                    logger.debug(f"{self.name} : Processed {processed_profiles}/{total_profiles} profiles.")  
        logger.info(f"{self.name} : Prediction cache calculated.")

    def fill_missing_profile_data(self):
        for freq in self.frequencies:
            for batch_size in range(1, self.max_batch_size + 1):
                if (freq, batch_size) not in self.profile:
                    predicted_energy, predicted_latency = self.predict(freq/1000000, batch_size)
                    self.profile[(freq, batch_size)] = (self.get_throughput(freq, batch_size), predicted_latency, predicted_energy)
                    logger.debug(f"{self.name} : Filled missing profile data for (f:{freq}, b:{batch_size})")
        logger.info(f"{self.name} : Missing profile data filled with predictions.")

    def predict(self, freq, batch_size):
        try:
            with self.cache_lock:
                if (freq, batch_size) in self.prediction_cache:
                    return self.prediction_cache[(freq, batch_size)]

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

                self.prediction_cache[(freq, batch_size)] = (predicted_energy, predicted_latency)

                return predicted_energy, predicted_latency
        except Exception as e:
            logger.error(f"{self.name} : Failed to predict energy and latency for profile (f:{freq}, b:{batch_size}): {e}")
            return float('inf'), float('inf')

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
        with self.freq_lock:
            # Determine the target frequency
            target_freq = freq
            if self.current_requests > 0:
                target_freq = max(freq, self.__current_freq)
                logger.debug(f"{self.name}: Pending requests detected. Setting frequency to max({freq}, {self.__current_freq}) = {target_freq} MHz")
            else:
                logger.debug(f"{self.name}: No pending requests. Setting frequency to {freq} MHz")

            # Only set frequency if it is different from the current frequency
            if target_freq != self.__current_freq:
                logger.debug(f"Setting frequency on {self.name} to {target_freq} MHz")
                response = worker_client.set_gpu_frequency(self.ip, target_freq)
                self.__current_freq = target_freq

                if response.get('status_code') == 200:
                    logger.info(f"Frequency set to {target_freq} MHz on {self.name}")
                else:
                    logger.error(f"Failed to set frequency on {self.name}: {response.get('message')}")



    def get_frequency(self):
        with self.freq_lock:
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
        with self.status_lock:
            self.__status = status
            logger.debug(f"Device {self.name} status set to {status}")
            if status == 'AVAILABLE':
                self.last_available_time = time.time()

    def is_available(self):
        with self.status_lock:
            return self.__status == 'AVAILABLE'
    
    def get_status(self):
        with self.status_lock:
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
        with self.requests_lock:
            self.current_requests += 1
            logger.debug(f"Request added to {self.name}. Current requests: {self.current_requests}/{self.model_instances}")
            if self.current_requests >= self.model_instances + self.allowed_buffer:
                self.set_status('BUSY')
                logger.debug(f"{self.name} is now BUSY with {self.current_requests} requests.")
            else:
                logger.debug(f"{self.name} is still AVAILABLE")

    def end_request(self):
        with self.requests_lock:
            self.current_requests -= 1
            logger.debug(f"Request completed on {self.name}. Current requests: {self.current_requests}/{self.model_instances}")
            if self.current_requests < self.model_instances + self.allowed_buffer:
                self.set_status('AVAILABLE')

    def add_request_for_duration(self, duration):
        """Starts a new thread to process a request for a specified duration."""
        def request_thread():
            self.add_request()  # Add a request
            time.sleep(duration)  # Wait for the specified duration
            self.end_request()  # End the request

        # Start a new thread for the request
        thread = threading.Thread(target=request_thread)
        thread.start()


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

    # Add network cost path
    network_cost_path = os.path.join(script_dir, '../measurements/network/network_cost.csv')
    network_cost = load_network_cost(network_cost_path)

    # Define the paths to the Profiling
    agx_path = os.path.join(script_dir, '../measurements/agx-xavier-00_filtered_freqs.csv')
    nx_path = os.path.join(script_dir, '../measurements/archive/Representative/xavier-nx-00/measurements/xavier-nx-00_filtered_freqs.csv')
    nano_path = os.path.join(script_dir, '../measurements/archive/Representative/LoudJetson0/measurements/LoudJetson0_filtered_freqs.csv')

    profiling_path = os.path.join(script_dir, '../measurements/archive/Representative/Profiling.csv')
    specs_path = os.path.join(script_dir, '../data/devices/gpu_specs.csv')

    agx_profile = csv_to_dict(profiling_path, 'agx')
    nx_profile = csv_to_dict(profiling_path, 'nx')
    nano_profile = csv_to_dict(profiling_path, 'nano')

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
        # AGX Xavier
        Device(
            name='agx-xavier-00',
            ip='147.102.37.108',
            frequencies=agx_freqs,
            profile=agx_profile,
            frequency_change_delay=agx_frequency_change_delay,
            batch_size_change_delay=agx_batch_size_change_delay,
            max_batch_size=64,
            network_cost=network_cost,
            **specs_dict['AGX']
        ),

        # Xavier NX 00
        Device(
            name='xavier-nx-00',
            ip='192.168.0.110',
            frequencies=nx_freqs,
            profile=nx_profile,
            frequency_change_delay=nx_frequency_change_delay,
            batch_size_change_delay=nx_batch_size_change_delay,
            max_batch_size=8,
            network_cost=network_cost,
            **specs_dict['NX']
        ),

        # Xavier NX 01
        Device(
            name='xavier-nx-01',
            ip='147.102.37.122',
            frequencies=nx_freqs,
            profile=nx_profile,
            frequency_change_delay=nx_frequency_change_delay,
            batch_size_change_delay=nx_batch_size_change_delay,
            max_batch_size=8,
            network_cost=network_cost,
            **specs_dict['NX']
        ),

        # LoudJetson0
        Device(
            name='LoudJetson0',
            ip='192.168.0.120',
            frequencies=nano_freqs,
            profile=nano_profile,
            frequency_change_delay=nano_frequency_change_delay,
            batch_size_change_delay=nano_batch_size_change_delay,
            max_batch_size=4,
            network_cost=network_cost,
            **specs_dict['Nano']
        ),

        # LoudJetson1
        Device(
            name='LoudJetson1',
            ip='192.168.0.121',
            frequencies=nano_freqs,
            profile=nano_profile,
            frequency_change_delay=nano_frequency_change_delay,
            batch_size_change_delay=nano_batch_size_change_delay,
            max_batch_size=4,
            network_cost=network_cost,
            **specs_dict['Nano']
        ),

        # LoudJetson2
        # Device(
        #     name='LoudJetson2',
        #     ip='192.168.0.122',
        #     frequencies=nano_freqs,
        #     profile=nano_profile,
        #     frequency_change_delay=nano_frequency_change_delay,
        #     batch_size_change_delay=nano_batch_size_change_delay,
        #     max_batch_size=4,
        #     network_cost=network_cost,
        #     **specs_dict['Nano']
        # ),
    ]

    logger.info("Devices initialized successfully")
    return devices

def csv_to_dict(file_path, model=None):
    # Initialize an empty dictionary to store the results
    result = defaultdict(list)

    try:
        # Open the CSV file
        with open(file_path, 'r') as csvfile:
            # Create a CSV DictReader object
            csvreader = csv.DictReader(csvfile)
            
            # Iterate through each row in the CSV
            for row in csvreader:
                # Check if the "Directory" column exists and if its value is the same as the model
                if 'Directory' in row and row['Directory'].strip().lower() == model:
                    # Extract the frequency, batch size, throughput, energy, and latency using column names
                    frequency = int(row['Frequency'])
                    batch_size = int(row['Batch Size'])
                    throughput = float(row['Throughput'])
                    energy = float(row['Energy'])
                    latency = float(row['Latency'])
                    
                    # Use (frequency, batch size) as the key and (throughput, latency, energy) as the value
                    result[(frequency, batch_size)] = (throughput, latency, energy)
        
        logger.info(f"Loaded profile from {file_path}")
    
    except Exception as e:
        logger.error(f"Failed to load profile from {file_path}: {e}")
    
    return dict(result)

def load_network_cost(file_path):
    """Load network costs from CSV into a list where index corresponds to batch size."""
    network_cost = [0.0]  # index 0 is unused
    try:
        with open(file_path, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                batch_size = int(row['Batch Size'])
                cost = float(row['Network Cost (μs)']) / 1_000_000
                network_cost.append(cost)
        logger.info(f"Loaded network costs from {file_path}")
    except Exception as e:
        logger.error(f"Failed to load network costs from {file_path}: {e}")
        network_cost = [0.0]
    return network_cost
       
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
        print(f"Profile: {list(device.profile.items())[0]} ... {list(device.profile.items())[-1]}")
        print(f"Max Batch Size: {device.max_batch_size}")
        print(f"Profile size: {len(device.profile)}")
        print(f"Current GPU Frequency: {device.get_frequency()} Hz")
        print(f"GPU Max Frequency: {device.gpu_max_freq} MHz, GPU Min Frequency: {device.gpu_min_freq} MHz")
        print(f"Architecture: {device.architecture}, Number of Cores: {device.num_cores}")
        print(f"Memory Speed: {device.memory_speed} GB/s, DRAM: {device.dram}, Shared Memory: {device.shared_memory}")
        print(f"Memory Size: {device.memory_size} GB, Tensor Cores: {device.tensor_cores}")
        print(f'Health Check: {device.health_check()}')
        print("\n")

    print("Checking process_request_for_duration method...")
    devices[0].add_request_for_duration(5)
    print("Request started for 5 seconds.")
    print(f"Device {devices[0].name} currently has {devices[0].current_requests} requests.")
    print("And as you can see, execution continues while the request is being processed.")
    time.sleep(6)
    print("Request completed.")
    print(f"Device {devices[0].name} currently has {devices[0].current_requests} requests.")


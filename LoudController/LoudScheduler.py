import time
import threading
from collections import deque
from DeviceData import initialize_devices
from logging_config import setup_logging

# Initialize devices
devices = initialize_devices()

# Request queue
request_queue = deque() # Queue to store incoming requests
response_dict = {}  # Dictionary to store responses

# Configure logging
logger = setup_logging()

def select_best_device_config(devices, latency_constraint, batch_size):
    best_device = None
    best_freq = None
    min_energy = float('inf')

    logger.debug("Selecting best device configuration")
    for device in devices:
        for freq in device.frequencies:
            latency = device.get_latency(freq, batch_size)
            if latency <= latency_constraint:
                energy = device.get_energy_consumption(freq, batch_size)
                if energy < min_energy:
                    min_energy = energy
                    best_device = device
                    best_freq = freq

    if best_device:
        logger.info(f"Selected device: {best_device.name} with frequency: {best_freq}")
    else:
        logger.warning("No suitable device configuration found")

    return best_device, best_freq

def manage_batches(max_wait_time=1.0):
    while True:
        if request_queue:
            # Process each request with its specific latency constraint
            images, request_ids, latency_constraints = zip(*request_queue)
            
            # Determine the batch size based on the smallest latency constraint
            batch_sizes = [device.current_batch_size for device in devices]
            for batch_size in sorted(set(batch_sizes), reverse=True):
                if len(request_queue) >= batch_size:
                    # Find the minimum latency constraint in the batch
                    min_latency_constraint = min(latency_constraints[:batch_size])
                    
                    # Select the best device configuration based on the minimum latency constraint
                    best_device, best_freq = select_best_device_config(devices, min_latency_constraint, batch_size)
                    if best_device:
                        best_device.set_frequency(best_freq)
                        threading.Thread(target=dispatch_request, args=(best_device, best_freq, images[:batch_size], request_ids[:batch_size])).start()
                    
                    # Remove processed requests from the queue
                    for _ in range(batch_size):
                        request_queue.popleft()

        time.sleep(0.01)

def dispatch_request(device, freq, images, request_ids):
    batch_size = len(images)
    
    logger.debug(f"Dispatching request to device {device.name} with frequency {freq} and batch size {batch_size}")

    # Set the GPU frequency on the device
    device.set_frequency(freq)

    # Dispatch the batch to the device's Triton server using the device's method
    response = device.inference(images, batch_size)
    
    # Store the server response in the response dictionary for each request_id
    for request_id in request_ids:
        response_dict[request_id] = response

    logger.info(f"Request dispatched and processed for IDs: {request_ids}")


# Start the batch manager in a separate thread
def start_scheduler(max_wait_time=1.0):
    logger.info("Starting scheduler...")
    threading.Thread(target=manage_batches, args=(max_wait_time,), daemon=True).start()

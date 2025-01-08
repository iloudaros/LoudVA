import time
import threading
from collections import deque
from DeviceData import initialize_devices
from logging_config import setup_logging
from LoudPredictor.costs.agnostic.LoudCostPredictor import LoudCostPredictor
import Settings as settings
from shared_resources import request_queue, response_dict, shared_queue_lock, shared_response_lock

# Initialize devices
devices = initialize_devices()

# Lock for synchronizing access to shared resources
internal_queue_lock = threading.Lock()
internal_response_lock = threading.Lock()

# Configure logging
logger = setup_logging()

# Get Debug mode of the logger
debug_mode = 1 if logger.getEffectiveLevel() == 10 else 0

if debug_mode:
    logger.info("Debug mode enabled.")

# Initialize and train the LoudCostPredictor
if settings.use_prediction:
    
    predictor = LoudCostPredictor('/home/louduser/LoudVA/LoudController/LoudPredictor/costs/agnostic/data.csv')
    logger.info("Training the LoudCostPredictor...")
    start_time = time.time()
    predictor.train()
    end_time = time.time()
    logger.info(f"LoudCostPredictor training complete. Training time: {end_time - start_time} seconds.")

else:
        logger.info("Using profiling data for decision making.")


def select_best_device_config(devices, latency_constraint, queue_size):
    """
    Selects the best device configuration based on latency constraints and energy consumption.
    If no configuration meets the constraints, returns the closest match.

    Args:
        devices (list): List of available devices.
        latency_constraint (float): The maximum allowable latency in seconds.

    Returns:
        tuple: Selected device, frequency, and batch size.
    """
    best_device = None
    best_freq = None
    best_batch_size = 0
    min_energy = float('inf')  # Initialize with infinity to find the minimum energy
    closest_device = None
    closest_freq = None
    closest_batch_size = 0
    closest_latency = float('inf')  # Initialize with infinity to find the closest latency

    logger.debug("Selecting best device configuration")

    available_devices = [device for device in devices if device.is_available()]

    if not available_devices:
        logger.warning("No available devices found.")
        return None, None, 0

    if settings.use_prediction:
        # Use prediction model to estimate energy and latency
        for device in available_devices:
            for freq in device.frequencies:
                for batch_size in range(min(queue_size, device.max_batch_size), 0, -1):
                    # Predict energy and latency for the current configuration
                    predicted_energy, predicted_latency = predictor.predict({
                        'Batch Size': batch_size,
                        'Frequency': freq,
                        'GPU Max Frequency (MHz)': device.gpu_max_freq,
                        'GPU Min Frequency (MHz)': device.gpu_min_freq,
                        'GPU Number of Cores': device.num_cores,
                        'Memory Speed (GB/s)': device.memory_speed,
                        'Memory Size (GB)': device.memory_size,
                        'Tensor Cores': device.tensor_cores
                    })

                    # Check if the configuration meets the latency constraint and is energy efficient
                    if predicted_latency <= latency_constraint and predicted_energy < min_energy:
                        min_energy = predicted_energy
                        best_device = device
                        best_freq = freq
                        best_batch_size = batch_size
                    elif predicted_latency < closest_latency:
                        # Track the closest configuration if it doesn't meet the latency constraint
                        closest_latency = predicted_latency
                        closest_device = device
                        closest_freq = freq
                        closest_batch_size = batch_size

    else:
        # Use profiling data for decision making
        for device in available_devices:
            for freq in device.frequencies:
                for batch_size in range(min(queue_size, device.max_batch_size), 0, -1):
                    # Get latency and energy from profiling data
                    latency = device.get_latency(freq, batch_size)
                    energy = device.get_energy_consumption(freq, batch_size)
                    
                    # Check if the configuration meets the latency constraint and is energy efficient
                    if latency <= latency_constraint and energy < min_energy:
                        min_energy = energy
                        best_device = device
                        best_freq = freq
                        best_batch_size = batch_size
                    elif latency < closest_latency:
                        # Track the closest configuration if it doesn't meet the latency constraint
                        closest_latency = latency
                        closest_device = device
                        closest_freq = freq
                        closest_batch_size = batch_size

    if best_device:
        logger.info(f"Selected device: {best_device.name} with frequency: {best_freq} and batch size: {best_batch_size}")
        return best_device, best_freq, best_batch_size
    else:
        logger.warning("No suitable device configuration found within constraints. Using closest match.")
        return closest_device, closest_freq, closest_batch_size

def manage_batches(max_wait_time=1.0):
    """
    Manages the batching of requests and dispatches them to the selected device configuration.

    Args:
        max_wait_time (float): Maximum time to wait before processing the batch.
    """
    while True:
        with internal_queue_lock:
            if request_queue:
                logger.debug(f"Queue: {request_queue}")

                # Collect all images and all ids from the queue
                all_images = []
                all_image_ids = []
                latency_constraints = []

                for images, image_id, latency_constraint in request_queue:
                    all_images.append(images)  
                    all_image_ids.append(image_id)  
                    latency_constraints.append(latency_constraint)  


                if debug_mode:
                    image_info = [(img.filename, img.content_length) for img in all_images]
                    logger.debug(f"Images: {image_info}")
                    logger.debug(f"Image IDs: {all_image_ids}")
                    logger.debug(f"Latency constraints: {latency_constraints}")
                    logger.debug(f"Queue size: {len(all_images)}")


                # Determine the minimum latency constraint in the queue
                min_latency_constraint = min(latency_constraints)

                # Select the best device configuration and batch size
                best_device, best_freq, best_batch_size = select_best_device_config(devices, min_latency_constraint, len(all_images))

                if best_device and best_batch_size > 0:
                    # Prepare the batch for dispatch
                    batch_images = all_images[:best_batch_size]
                    batch_image_ids = all_image_ids[:best_batch_size]

                    # Dispatch the request
                    threading.Thread(target=dispatch_request, args=(best_device, best_freq, batch_images, batch_image_ids)).start()

                    # Remove processed requests from the queue
                    for _ in range(best_batch_size):
                        request_queue.popleft()

        # Wait for the next batch depending on the debug mode of the logger
        if debug_mode:
            time.sleep(2) 
        else:
            time.sleep(0.01)



def dispatch_request(device, freq, images, image_ids):
    batch_size = len(images)
    
    # Set the device status to BUSY
    device.set_status('BUSY')
    
    logger.debug(f"Dispatching request to device {device.name} with frequency {freq}, batch size {batch_size} and images {images}") 

    # Set the GPU frequency on the device
    device.set_frequency(freq)

    # Dispatch the batch to the device's Triton server using the device's method
    response = device.inference(images, batch_size)
    
    # Store the server response in the response dictionary for each request_id
    with internal_response_lock:
        for image_id, image_response in zip(image_ids, response):
            response_dict[image_id] = response
    logger.info(f"Response stored in the response dictionary for image IDs: {image_ids}")

    # Set the device status back to AVAILABLE
    device.set_status('AVAILABLE')


def health_check():
    while True:
        for device in devices:
            try:
                # Implement a simple check, e.g., ping or a test inference request
                healthy = device.health_check()
                if healthy:
                    if device.get_status == 'OFFLINE':
                        device.set_status('AVAILABLE')
                else:
                    device.set_status('OFFLINE')
            except Exception as e:
                device.set_status('OFFLINE')
                logger.error(f"Health check failed for {device.name}: {e}")
        
        time.sleep(settings.health_check_interval)  




# Start the batch manager in a separate thread
def start_scheduler(max_wait_time=1.0):
    logger.info("Starting scheduler...")
    threading.Thread(target=manage_batches, args=(max_wait_time,), daemon=True).start()

    if settings.health_checks_enabled:
        # Start the health check in a separate thread
        threading.Thread(target=health_check, daemon=True).start()


if __name__ == '__main__':
    start_scheduler(settings.max_wait_time)
    logger.info("Scheduler started.")
    while True:
        time.sleep(1)
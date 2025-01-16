import time
import threading
from DeviceData import initialize_devices
from logging_config import setup_logging
import Settings as settings

# Initialize devices
devices = initialize_devices()

# Configure logging
logger = setup_logging()

# Get Debug mode of the logger
debug_mode = 1 if logger.getEffectiveLevel() == 10 else 0

if debug_mode:
    logger.info("Debug mode enabled.")


def select_best_device_config(devices, latency_constraint, queue_size):
    """
    Selects the best device configuration based on latency constraints and energy efficiency (energy per frame).
    If no configuration meets the constraints, returns the closest match.

    Args:
        devices (list): List of available devices.
        latency_constraint (float): The maximum allowable latency in seconds.
        queue_size (int): The number of requests currently in the queue.

    Returns:
        tuple: Selected device, frequency, and batch size.
    """
    best_config = {
        'device': None,
        'freq': None,
        'batch_size': 0,
        'energy_per_frame': float('inf'),
        'latency': float('inf')
    }
    
    closest_config = {
        'device': None,
        'freq': None,
        'batch_size': 0,
        'latency': float('inf')
    }

    logger.debug("Selecting best device configuration")

    # Filter available devices
    available_devices = [device for device in devices if device.is_available()]
    if not available_devices:
        logger.warning("No available devices found.")
        return None, None, 0, float('inf')

    # Iterate over each device and its possible configurations
    for device in available_devices:
        for freq in device.frequencies:
            for batch_size in range(min(queue_size, device.max_batch_size), 0, -1):
                # Predict or retrieve energy and latency
                if settings.use_prediction:
                    energy, latency = device.predict(freq, batch_size)
                else:
                    latency = device.get_latency(freq, batch_size)
                    energy = device.get_energy_consumption(freq, batch_size)

                # Calculate energy per frame
                energy_per_frame = energy / batch_size if batch_size > 0 else float('inf')

                # Check if configuration meets latency constraint and is energy efficient (energy per frame)
                if latency <= latency_constraint and energy_per_frame < best_config['energy_per_frame']:
                    best_config.update({'device': device, 'freq': freq, 'batch_size': batch_size, 'energy_per_frame': energy_per_frame, 'latency': latency})
                elif latency < closest_config['latency']:
                    # Track the closest configuration if it doesn't meet the latency constraint
                    closest_config.update({'device': device, 'freq': freq, 'batch_size': batch_size, 'latency': latency})

    if best_config['device']:
        logger.debug(f"Selected device: {best_config['device'].name} with frequency: {best_config['freq']} and batch size: {best_config['batch_size']}")
        return best_config['device'], best_config['freq'], best_config['batch_size'], best_config['latency']
    else:
        logger.warning("No suitable device configuration found within constraints. Using closest match.")
        return closest_config['device'], closest_config['freq'], closest_config['batch_size'], closest_config['latency']





def manage_batches(queue, response_dict):
    """
    Manages the batching of requests and dispatches them to the selected device configuration.

    Args:
        max_wait_time (float): Maximum time to wait before processing the batch.
    """
    queue_list = []

    while True:
        if not (queue.empty() and not queue_list):
            logger.debug(f"Queue: {queue}")

            # Add the contents of the queue to the queue_list. Caution, queue is not iterable
            while not queue.empty():
                queue_list.append(queue.get())



            # Calculate remaining time in seconds for each request in the queue and sort based on it
            logger.debug("Calculating remaining time for each request in the queue.")
            current_time = time.time()
            remaining_time_list = []

            for image_bytes, image_id, latency_constraint, arrival_time in queue_list:
                time_elapsed = current_time - arrival_time
                remaining_time = latency_constraint - time_elapsed
                remaining_time_list.append((remaining_time, image_bytes, image_id, latency_constraint, arrival_time))

            remaining_time_list.sort(key=lambda x: x[0])

            # Collect all images and all ids from the queue.
            all_remaining_times = []
            all_images = []
            all_image_ids = []
            latency_constraints = []
            arrival_times = []

            for remaining_time, images, image_id, latency_constraint, arrival_time in remaining_time_list:
                all_remaining_times.append(remaining_time)
                all_images.append(images)  
                all_image_ids.append(image_id)  
                latency_constraints.append(latency_constraint)  
                arrival_times.append(arrival_time)

            if debug_mode:
                logger.debug(f"Image IDs: {all_image_ids}")
                logger.debug(f"Latency constraints: {latency_constraints}")

            # Determine the minimum remaining time 
            min_remaining_time = min(all_remaining_times)

            # Select the best device configuration and batch size
            best_device, best_freq, best_batch_size, expected_latency = select_best_device_config(devices, min_remaining_time, len(all_images))

            if best_device and best_batch_size > 0:
                # We have a valid configuration, dispatch the batch
                logger.debug(f"Best device configuration found. Proceeding.")

                # If the remaining time is greater than the expected latency, wait for more images
                logger.debug(f"Min remaining time: {min_remaining_time}, Expected latency: {expected_latency}")
                if min_remaining_time > expected_latency * settings.batching_wait_strictness:
                    logger.debug(f"Latency constraint allows for waiting, holding for more images.")
                    time.sleep(0.01)
                    continue

                # Prepare the batch for dispatch
                batch_images = all_images[:best_batch_size]
                batch_image_ids = all_image_ids[:best_batch_size]

                # Dispatch the request
                threading.Thread(target=dispatch_request, args=(best_device, best_freq, batch_images, batch_image_ids, response_dict)).start()

                # Remove the dispatched batch from the queue
                queue_list = queue_list[best_batch_size:]
                logger.debug(f"Batch dispatched. Remaining number of items in the queue: {len(queue_list)}")


        # Wait for the next batch depending on the debug mode of the logger
        if debug_mode:
            time.sleep(2) 
        else:
            time.sleep(0.01)



def dispatch_request(device, freq, images, image_ids, response_dict):
    batch_size = len(images)
    
    # Set the device status to BUSY
    device.set_status('BUSY')
    
    logger.debug(f"Dispatching request to device {device.name} with frequency {freq}, batch size {batch_size}") 

    # Set the GPU frequency on the device
    device.set_frequency(freq)

    # Dispatch the batch to the device's Triton server using the device's method
    [response] = device.inference(images, batch_size)
    
    logger.debug(f"Received response ({response}) from device {device.name} for image IDs: {image_ids}")
    
    # Store the server response in the response dictionary for each request_id
    for image_id, image_response in zip(image_ids, response):

        response_dict[image_id] = image_response

    logger.debug(f"Response stored in the response dictionary for image IDs: {image_ids}")

    # Set the device status back to AVAILABLE
    device.set_status('AVAILABLE')



def health_check():
    while True:
        for device in devices:
            try:
                # Use the device's health check method to determine if the device is healthy
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



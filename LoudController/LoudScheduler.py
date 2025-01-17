# loud_scheduler.py
import time
import threading
from DeviceData import initialize_devices
from logging_config import setup_logging
import Settings as settings

# Initialize devices
devices = initialize_devices()

# Configure logging
logger = setup_logging()

class LoudScheduler:
    def __init__(self):
        self.devices = devices
        self.debug_mode = 1 if logger.getEffectiveLevel() == 10 else 0

    def select_best_device_config(self, latency_constraint, queue_size):
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

        available_devices = [device for device in self.devices if device.is_available()]
        if not available_devices:
            logger.warning("No available devices found.")
            return None, None, 0, float('inf')

        for device in available_devices:
            for freq in device.frequencies:
                for batch_size in range(min(queue_size, device.max_batch_size), 0, -1):
                    if settings.use_prediction:
                        energy, latency = device.predict(freq, batch_size)
                    else:
                        latency = device.get_latency(freq, batch_size)
                        energy = device.get_energy_consumption(freq, batch_size)

                    energy_per_frame = energy / batch_size if batch_size > 0 else float('inf')

                    if latency <= latency_constraint and energy_per_frame < best_config['energy_per_frame']:
                        best_config.update({'device': device, 'freq': freq, 'batch_size': batch_size, 'energy_per_frame': energy_per_frame, 'latency': latency})
                    elif latency < closest_config['latency']:
                        closest_config.update({'device': device, 'freq': freq, 'batch_size': batch_size, 'latency': latency})

        if best_config['device']:
            logger.debug(f"Selected device: {best_config['device'].name} with frequency: {best_config['freq']} and batch size: {best_config['batch_size']}")
            return best_config['device'], best_config['freq'], best_config['batch_size'], best_config['latency']
        else:
            logger.warning("No suitable device configuration found within constraints. Using closest match.")
            return closest_config['device'], closest_config['freq'], closest_config['batch_size'], closest_config['latency']

    def start(self, queue, response_dict):
        queue_list = []

        while True:
            if not (queue.empty() and not queue_list):
                logger.debug(f"Queue: {queue}")

                while not queue.empty():
                    queue_list.append(queue.get())

                logger.debug("Calculating remaining time for each request in the queue.")
                current_time = time.time()
                remaining_time_list = []

                for image_bytes, image_id, latency_constraint, arrival_time in queue_list:
                    time_elapsed = current_time - arrival_time
                    remaining_time = latency_constraint - time_elapsed
                    remaining_time_list.append((remaining_time, image_bytes, image_id, latency_constraint, arrival_time))

                remaining_time_list.sort(key=lambda x: x[0])

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

                if self.debug_mode:
                    logger.debug(f"Image IDs: {all_image_ids}")
                    logger.debug(f"Latency constraints: {latency_constraints}")

                min_remaining_time = min(all_remaining_times)

                best_device, best_freq, best_batch_size, expected_latency = self.select_best_device_config(min_remaining_time, len(all_images))

                if best_device and best_batch_size > 0:
                    logger.debug(f"Best device configuration found. Proceeding.")

                    logger.debug(f"Min remaining time: {min_remaining_time}, Expected latency: {expected_latency}")
                    if min_remaining_time > expected_latency * settings.batching_wait_strictness:
                        logger.debug(f"Latency constraint allows for waiting, holding for more images.")
                        time.sleep(0.01)
                        continue

                    batch_images = all_images[:best_batch_size]
                    batch_image_ids = all_image_ids[:best_batch_size]

                    threading.Thread(target=self.dispatch_request, args=(best_device, best_freq, batch_images, batch_image_ids, response_dict)).start()

                    queue_list = queue_list[best_batch_size:]
                    logger.debug(f"Batch dispatched. Remaining number of items in the queue: {len(queue_list)}")

            if self.debug_mode:
                time.sleep(2) 
            else:
                time.sleep(0.01)

    def dispatch_request(self, device, freq, images, image_ids, response_dict):
        batch_size = len(images)
        
        device.set_status('BUSY')
        
        logger.debug(f"Dispatching request to device {device.name} with frequency {freq}, batch size {batch_size}") 

        device.set_frequency(freq)

        [response] = device.inference(images, batch_size)
        
        logger.debug(f"Received response ({response}) from device {device.name} for image IDs: {image_ids}")
        
        for image_id, image_response in zip(image_ids, response):
            response_dict[image_id] = image_response

        logger.debug(f"Response stored in the response dictionary for image IDs: {image_ids}")

        device.set_status('AVAILABLE')

    def health_check(self):
        while True:
            for device in self.devices:
                try:
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

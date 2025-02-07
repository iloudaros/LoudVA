import time
import threading
from DeviceData import initialize_devices
from logging_config import setup_logging
import Settings as settings

# Initialize devices
devices = initialize_devices()

# Configure logging
logger = setup_logging()

# Find the maximum batch size among all devices
max_batch_size = max([device.max_batch_size for device in devices])

class LoudScheduler:
    def __init__(self):
        self.devices = devices
        self.debug_mode = 1 if logger.getEffectiveLevel() == 10 else 0
        self.last_frequency_scaling_check = time.time()
        self.waiting_flag = False
        self.available_devices_flag = False

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
            'latency': float('inf'),
            'throughput': 0
        }

        logger.debug("Selecting best device configuration")

        available_devices = [device for device in self.devices if device.is_available()]

        if settings.debug:
            current_request_count = [device.current_requests for device in available_devices]
            model_instances = [device.model_instances for device in available_devices]
            current_request_count = [f"{current_request_count[i]}/{model_instances[i]}" for i in range(len(current_request_count))]
            device_request_counts = dict(zip([device.name for device in available_devices], current_request_count))
            logger.debug(f'There are {len(available_devices)} available devices.')
            logger.debug(f"Device request counts: {device_request_counts}")

        if not available_devices:
            if self.available_devices_flag:
                logger.warning("No available devices found. Returning None. Waiting for devices to become available.")
                self.available_devices_flag = False
            return None, None, 0, float('inf')

        self.available_devices_flag = True

        for device in available_devices:
            for freq in device.frequencies:
                for batch_size in range(min(queue_size, device.max_batch_size), 0, -1):
                    if settings.use_prediction:
                        energy, latency = device.predict(freq, batch_size)
                    else:
                        latency = device.get_latency(freq, batch_size)
                        energy = device.get_energy_consumption(freq, batch_size)

                    energy_per_frame = energy / batch_size if batch_size > 0 else float('inf')
                    
                    # Calculate throughput as inversely proportional to latency
                    throughput = batch_size / latency if latency > 0 else 0

                    # Add the safety margin to the latency and the frequency change delay if the frequency is different than the current one
                    latency = latency + settings.safety_margin + (device.frequency_change_delay if device.get_frequency() != freq else 0)
                    
                    # We are within the latency constraint, select the configuration with minimum energy per frame
                    if latency <= latency_constraint and energy_per_frame < best_config['energy_per_frame']:
                        best_config.update({'device': device, 'freq': freq, 'batch_size': batch_size, 'energy_per_frame': energy_per_frame, 'latency': latency})
                        logger.debug(f"Best configuration updated: {best_config}")

                    # We have fallen behind the latency constraint, we need to find the closest configuration and process the queue asap
                    else:
                        # Handle configurations that don't meet latency constraints
                        new_throughput = throughput
                        new_latency = latency
                        current_closest_throughput = closest_config['throughput']
                        current_closest_latency = closest_config['latency']
                        
                        update_closest = False
                        
                        if new_throughput >= queue_size:
                            # New config meets throughput requirement
                            if current_closest_throughput < queue_size:
                                # Current config doesn't meet requirement - update
                                update_closest = True
                            else:
                                # Both meet requirement - prioritize lower latency
                                if new_latency < current_closest_latency:
                                    update_closest = True
                        else:
                            # New config doesn't meet throughput requirement
                            if current_closest_throughput < queue_size:
                                # Neither meets requirement - prioritize higher throughput, then lower latency
                                if (new_throughput > current_closest_throughput or 
                                    (new_throughput == current_closest_throughput and 
                                    new_latency < current_closest_latency)):
                                    update_closest = True
                        
                        if update_closest:
                            closest_config.update({
                                'device': device,
                                'freq': freq,
                                'batch_size': batch_size,
                                'latency': new_latency,
                                'throughput': new_throughput
                            })
                            logger.debug(f"Closest configuration updated: {closest_config}")

        if best_config['device']:
            logger.debug(f"Selected device: {best_config['device'].name} with frequency: {best_config['freq']} and batch size: {best_config['batch_size']}")
            return best_config['device'], best_config['freq'], best_config['batch_size'], best_config['latency']
        else:
            logger.warning("No suitable device configuration found within constraints. Using closest match.")
            logger.debug(f"Selected device: {closest_config['device'].name} with frequency: {closest_config['freq']} and batch size: {closest_config['batch_size']}")
            return closest_config['device'], closest_config['freq'], closest_config['batch_size'], closest_config['latency']


    def start(self, queue, response_dict):
        queue_list = []
        last_added_time = None

        while True:
            current_time = time.time()


            # Frequency scaling Logic
            if current_time - self.last_frequency_scaling_check >= 2:
                for device in self.devices:
                    if device.is_available() and (current_time - device.last_available_time) >= settings.frequency_scaling_idle_limit:
                        device.set_frequency(min(device.frequencies))
                        logger.debug(f"Frequency scaling check for device {device.name}. Set frequency to minimum: {min(device.frequencies)}")

                self.last_frequency_scaling_check = current_time


            # Queue Processing Logic
            if not (queue.empty() and not queue_list):
                logger.debug(f"Queue: {queue.qsize()+len(queue_list)}")

                # Add all new requests to the queue list
                initial_length = len(queue_list)
                while not queue.empty():
                    queue_list.append(queue.get())
                    last_added_time = time.time() # Capture the time of the last addition

                time_since_last_add = current_time - (last_added_time or 0) # Time since the last image was added to the queue

                # Did we add new items to the queue?
                if len(queue_list) > initial_length:
                    logger.debug(f"Added {len(queue_list) - initial_length} new items to the queue.")

                # Calculate the remaining time for each request in the queue
                logger.debug("Calculating remaining time for each request in the queue.")
                current_time = time.time()
                remaining_time_list = []

                for image_bytes, image_id, latency_constraint, arrival_time in queue_list:
                    time_elapsed = current_time - arrival_time
                    remaining_time = latency_constraint - time_elapsed
                    remaining_time_list.append((remaining_time, image_bytes, image_id, latency_constraint, arrival_time))

                # Sort the queue based on the remaining time
                remaining_time_list.sort(key=lambda x: x[0])
                queue_list = [(image_bytes, image_id, latency_constraint, arrival_time) for _, image_bytes, image_id, latency_constraint, arrival_time in remaining_time_list]

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

                # Select the best device configuration
                best_device, best_freq, best_batch_size, expected_latency = self.select_best_device_config(min_remaining_time, len(all_images))

                if best_device and best_batch_size > 0:
                    logger.debug(f"Device configuration decided. Proceeding.")

                    logger.debug(f"Min remaining time: {min_remaining_time}, Expected latency: {expected_latency}, Queue: {len(queue_list)}, Max batch size: {max_batch_size}")

                    # Should we wait for more images?
                    if (min_remaining_time > expected_latency * settings.batching_wait_looseness 
                        and len(queue_list) < max_batch_size
                        and time_since_last_add < settings.batching_max_wait_time
                        ): # Αυτό μπορεί να γίνει πιο έξυπνο αν βάλουμε έναν πρεντικτορα
                        
                        if not self.waiting_flag:
                            logger.info(f"Latency constraint allows for waiting, holding for more images.")
                            self.waiting_flag = True


                        time.sleep(settings.scheduler_wait_time)
                        continue
                    
                    # We have enough images to dispatch
                    else:
                        self.waiting_flag = False
                        batch_images = all_images[:best_batch_size]
                        batch_image_ids = all_image_ids[:best_batch_size]

                        threading.Thread(target=self.dispatch_request, args=(best_device, best_freq, batch_images, batch_image_ids, response_dict, expected_latency)).start()

                        queue_list = queue_list[best_batch_size:]
                        logger.debug(f"Batch dispatched. Remaining number of items in the queue: {len(queue_list)}")
            

            if self.debug_mode:
                time.sleep(2) 
            else:
                time.sleep(settings.scheduler_wait_time)

    def dispatch_request(self, device, freq, images, image_ids, response_dict, expected_latency=None):
        device.add_request_for_duration(expected_latency)
        batch_size = len(images)

        logger.info(f"Dispatching to {device.name} with frequency {freq}, batch size {batch_size}")

        device.set_frequency(freq)

        # Capture the queue exit time
        queue_exit_time = time.time()

        # Get the response from the device inference
        [response] = device.inference(images, batch_size)

        logger.debug(f"Received response ({response}) from device {device.name} for image IDs: {image_ids}")

        for image_id, image_response in zip(image_ids, response):
            # Assuming image_response is a list, append the queue_exit_time
            image_response.append(queue_exit_time)
            logger.debug(f"Response: {image_response}")
            response_dict[image_id] = image_response

        logger.debug(f"Response stored in the response dictionary for image IDs: {image_ids}")

        
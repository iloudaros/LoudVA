# random_scheduler.py
import random
import time
import threading
from DeviceData import initialize_devices
from logging_config import setup_logging

# Initialize devices
devices = initialize_devices()

# Configure logging
logger = setup_logging()

class RandomScheduler:
    def __init__(self):
        self.devices = devices

    def start(self, queue, response_dict):
        while True:
            if not queue.empty():
                queue_list = []

                # Gather all requests from the queue
                while not queue.empty():
                    queue_list.append(queue.get())

                # Ensure there are available devices
                available_devices = [device for device in self.devices if device.is_available()]
                if not available_devices:
                    logger.warning("No available devices found.")
                    continue

                # Randomly select a device and configuration
                device = random.choice(available_devices)
                freq = random.choice(device.frequencies)
                batch_size = random.randint(1, min(len(queue_list), device.max_batch_size))

                # Dispatch the batch
                self.dispatch_request(device, freq, queue_list[:batch_size], response_dict)

                # Remove dispatched items from the queue list
                queue_list = queue_list[batch_size:]

            time.sleep(0.01)

    def dispatch_request(self, device, freq, batch, response_dict):
        device.add_request()
        batch_size = len(batch)
        images = [item[0] for item in batch]
        image_ids = [item[1] for item in batch]
        
        logger.debug(f"Dispatching request to device {device.name} with frequency {freq}, batch size {batch_size}")

        device.set_frequency(freq)

        queue_exit_time = time.time()

        [response] = device.inference(images, batch_size)

        logger.debug(f"Received response ({response}) from device {device.name} for image IDs: {image_ids}")

        for image_id, image_response in zip(image_ids, response):
            image_response.append(queue_exit_time)
            response_dict[image_id] = image_response

        logger.debug(f"Response stored in the response dictionary for image IDs: {image_ids}")

        device.end_request()

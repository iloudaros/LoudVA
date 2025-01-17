# rotation_scheduler.py
from itertools import cycle
import time
import threading
from DeviceData import initialize_devices
from logging_config import setup_logging

# Initialize devices
devices = initialize_devices()

# Configure logging
logger = setup_logging()

class RoundRobinScheduler:
    def __init__(self, fixed_batch_size):
        self.fixed_batch_size = fixed_batch_size
        self.device_cycle = cycle(devices)

    def start(self, queue, response_dict):
        while True:
            if not queue.empty():
                queue_list = []

                # Gather all requests from the queue
                while not queue.empty():
                    queue_list.append(queue.get())

                # Ensure there are available devices
                available_devices = [device for device in devices if device.is_available()]
                if not available_devices:
                    logger.warning("No available devices found.")
                    continue

                # Rotate to the next available device
                device = next(self.device_cycle)
                while not device.is_available():
                    device = next(self.device_cycle)

                freq = device.frequencies[0]  # Use the first frequency as default
                batch_size = min(self.fixed_batch_size, len(queue_list), device.max_batch_size)

                # Dispatch the batch
                self.dispatch_request(device, freq, queue_list[:batch_size], response_dict)

                # Remove dispatched items from the queue list
                queue_list = queue_list[batch_size:]

            time.sleep(0.01)

    def dispatch_request(self, device, freq, batch, response_dict):
        batch_size = len(batch)
        images = [item[0] for item in batch]
        image_ids = [item[1] for item in batch]

        device.set_status('BUSY')
        
        logger.debug(f"Dispatching request to device {device.name} with frequency {freq}, batch size {batch_size}")

        device.set_frequency(freq)

        [response] = device.inference(images, batch_size)

        logger.debug(f"Received response ({response}) from device {device.name} for image IDs: {image_ids}")

        for image_id, image_response in zip(image_ids, response):
            response_dict[image_id] = image_response

        logger.debug(f"Response stored in the response dictionary for image IDs: {image_ids}")

        device.set_status('AVAILABLE')

from itertools import cycle
import time
import threading
from DeviceData import initialize_devices
from logging_config import setup_logging

response_dict_lock = threading.Lock()


# Initialize devices
devices = initialize_devices()

# Configure logging
logger = setup_logging()

class FixedBatchScheduler:

    def __init__(self, fixed_batch_size, max_waiting_time):
        self.fixed_batch_size = fixed_batch_size
        self.max_waiting_time = max_waiting_time
        self.device_cycle = cycle(devices)
        self.small_queue_flag = False

    def start(self, queue, response_dict):
        queue_list = []
        first_item_time = None

        while True:
            if not (queue.empty() and not queue_list):

                # Gather all requests from the queue
                while not queue.empty():
                    queue_list.append(queue.get())
                    if first_item_time is None:
                        first_item_time = time.time()

                # Rotate to the next device
                device = next(self.device_cycle)

                target_batch_size = min(self.fixed_batch_size, device.max_batch_size)


                # Check if the queue_list is smaller than the fixed batch size
                if len(queue_list) < target_batch_size:
                    # Check if the max waiting time is surpassed
                    if first_item_time and (time.time() - first_item_time >= self.max_waiting_time):
                        self.small_queue_flag = True
                    else:
                        continue

                # Set the batch size 
                batch_size = target_batch_size if not self.small_queue_flag else len(queue_list)
                self.small_queue_flag = False

                # Dispatch the batch
                threading.Thread(target=self.dispatch_request, args=(device, queue_list[:batch_size], response_dict)).start()

                # Remove dispatched items from the queue list
                queue_list = queue_list[batch_size:]
                first_item_time = None if not queue_list else time.time()

            time.sleep(0.1)

    def dispatch_request(self, device, batch, response_dict):
        device.add_request()
        batch_size = len(batch)
        images = [item[0] for item in batch]
        image_ids = [item[1] for item in batch]
        
        logger.debug(f"Dispatching request to device {device.name}, batch size {batch_size}")

        queue_exit_time = time.time()

        [response] = device.inference(images, batch_size)

        logger.debug(f"Received response ({response}) from device {device.name} for image IDs: {image_ids}")

        for image_id, image_response in zip(image_ids, response):
            with response_dict_lock:
                image_response.extend([device.name, queue_exit_time])
                response_dict[image_id] = image_response

        logger.debug(f"Response stored in the response dictionary for image IDs: {image_ids}")

        device.end_request()

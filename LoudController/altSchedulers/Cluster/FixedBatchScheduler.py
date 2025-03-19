import time
import threading
from DeviceData import initialize_devices
from logging_config import setup_logging

# Initialize devices
devices = initialize_devices()

# Configure logging
logger = setup_logging()

class FixedBatchScheduler:

    def __init__(self, fixed_batch_size, max_waiting_time):
        self.fixed_batch_size = fixed_batch_size
        self.max_waiting_time = max_waiting_time

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

                # Check if the queue_list is smaller than the fixed batch size
                if len(queue_list) < self.fixed_batch_size:
                    # Check if the max waiting time is surpassed
                    if first_item_time and (time.time() - first_item_time >= self.max_waiting_time):
                        # Dispatch the batch
                        threading.Thread(target=self.dispatch_request, args=(devices[0], queue_list, response_dict)).start()
                        queue_list = []
                        first_item_time = None
                    continue

                # The batch size is the size of the queue list with max batch size as the upper limit
                batch_size = self.fixed_batch_size

                # Dispatch the batch
                threading.Thread(target=self.dispatch_request, args=(devices[0], queue_list[:batch_size], response_dict)).start()

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
            image_response.append(queue_exit_time)
            response_dict[image_id] = image_response

        logger.debug(f"Response stored in the response dictionary for image IDs: {image_ids}")

        device.end_request()

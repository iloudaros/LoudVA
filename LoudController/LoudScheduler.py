import time
import threading
from DeviceData import initialize_devices
import triton_client  

# Initialize devices
devices = initialize_devices()

# Request queue
request_queue = []
response_dict = {}  # Dictionary to store responses

def select_best_device_config(devices, max_latency, batch_size):
    best_device = None
    best_freq = None
    min_energy = float('inf')

    for device in devices:
        for freq in device.frequencies:
            latency = device.get_latency(freq, batch_size)
            if latency <= max_latency:
                energy = device.get_energy_consumption(freq, batch_size)
                if energy < min_energy:
                    min_energy = energy
                    best_device = device
                    best_freq = freq

    return best_device, best_freq

def manage_batches(max_latency, max_wait_time=1.0):
    while True:
        if request_queue:
            # Determine the largest batch size possible
            batch_sizes = [device.current_batch_size for device in devices]
            max_batch_size = max(batch_sizes)
            for batch_size in sorted(set(batch_sizes), reverse=True):
                if len(request_queue) >= batch_size:
                    images, request_ids = zip(*request_queue[:batch_size])
                    request_queue[:] = request_queue[batch_size:]

                    best_device, best_freq = select_best_device_config(devices, max_latency, batch_size)
                    if best_device:
                        best_device.set_frequency(best_freq)
                        threading.Thread(target=dispatch_request, args=(best_device, images, request_ids)).start()

        time.sleep(0.01)

def dispatch_request(device, images, request_ids):
    batch_size = len(images)
    device.set_batch_size(batch_size)
    # Dispatch the batch to the device's Triton server using triton_client
    response = send_to_triton_server(device.ip, images, device.current_freq, batch_size)
    
    # Store the server response in the response dictionary for each request_id
    for request_id in request_ids:
        response_dict[request_id] = response

def send_to_triton_server(ip, images, freq, batch_size):
    # Use the triton_client to send images to the Triton server
    model_name = 'your_model_name'  # Replace with your actual model name
    model_version = '1'  # Replace with your model version if needed
    classes = 1  # Define the number of classes
    scaling = 'NONE'  # Define the type of scaling
    url = f'{ip}:8000'  # Triton server URL
    
    # Prepare the arguments for the triton_client
    args = [
        '--model-name', model_name,
        '--model-version', model_version,
        '--batch-size', str(batch_size),
        '--classes', str(classes),
        '--scaling', scaling,
        '--url', url,
        '--protocol', 'HTTP'
    ]

    # Add image filenames to arguments
    args.extend(images)

    # Call the triton_client's main function
    return triton_client.main(args)  # Return the response directly

# Start the batch manager in a separate thread
def start_scheduler(max_latency=0.5, max_wait_time=1.0):
    print("Starting scheduler...")
    threading.Thread(target=manage_batches, args=(max_latency, max_wait_time)).start()

import time
import threading
from DeviceData import initialize_devices
import triton_client  
import Settings

# Initialize devices
devices = initialize_devices()

# Request queue
request_queue = []
response_dict = {}  # Dictionary to store responses

def select_best_device_config(devices, latency_constraint, batch_size):
    best_device = None
    best_freq = None
    min_energy = float('inf')

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
        print(f"Selected device: {best_device.name}, frequency: {best_freq}, batch size: {batch_size}")
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
                        threading.Thread(target=dispatch_request, args=(best_device, images[:batch_size], request_ids[:batch_size])).start()
                    
                    # Remove processed requests from the queue
                    request_queue[:] = request_queue[batch_size:]

        time.sleep(0.01)

def dispatch_request(device, images, request_ids):
    batch_size = len(images)
    # Dispatch the batch to the device's Triton server using triton_client
    response = send_to_triton_server(device.ip, images, device.current_freq, batch_size)
    
    # Store the server response in the response dictionary for each request_id
    for request_id in request_ids:
        response_dict[request_id] = response

def send_to_triton_server(ip, images, freq, batch_size):
    url = f'{ip}:8000'  # Triton server URL
    
    # Prepare the arguments for the triton_client
    args = [
        '--model-name', Settings.model_name,
        '--model-version', Settings.model_version,
        '--batch-size', str(batch_size),
        '--classes', Settings.number_of_classes,
        '--scaling', Settings.scaling,
        '--url', url,
        '--protocol', 'HTTP'
    ]

    # Add image filenames to arguments
    args.extend(images)

    # Call the triton_client's main function
    return triton_client.main(args)  # Return the response directly

# Start the batch manager in a separate thread
def start_scheduler(max_wait_time=1.0):
    print("Starting scheduler...")
    threading.Thread(target=manage_batches, args=(max_wait_time,)).start()

import time
from flask import Flask, request, jsonify
import threading
import DeviceData

devices = DeviceData.devices

request_queue = []

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
        current_time = time.time()
        
        if request_queue:
            batch_sizes = [device.batch_sizes for device in devices]
            max_batch_size = max(max(batch) for batch in batch_sizes)
            for batch_size in sorted(set(sum(batch_sizes, [])), reverse=True):
                if len(request_queue) >= batch_size:
                    images, _ = zip(*request_queue[:batch_size])
                    request_queue[:] = request_queue[batch_size:]

                    best_device, best_freq = select_best_device_config(devices, max_latency, batch_size)
                    if best_device:
                        best_device.set_frequency(best_freq)
                        threading.Thread(target=dispatch_request, args=(best_device, images)).start()

        time.sleep(0.01)

def dispatch_request(device, images):
    batch_size = len(images)
    device.set_batch_size(batch_size)
    # Dispatch the batch to the device's Triton server
    response = send_to_triton_server(device.ip, images)
    # Handle the server response as needed

def send_to_triton_server(ip, images):
    # Implement communication logic with Triton server
    pass

app = Flask(__name__)

@app.route('/infer', methods=['POST'])
def infer():
    image = request.get_json().get('image')
    request_queue.append((image, time.time()))
    return jsonify({"status": "queued"})

if __name__ == '__main__':
    threading.Thread(target=manage_batches, args=(max_latency, max_wait_time)).start()
    app.run(host='0.0.0.0', port=5000)

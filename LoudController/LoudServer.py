import csv
import os
import time
import uuid
import fcntl  # For file locking on Linux, used for the logging in the csv

from flask import Flask, request, jsonify
import Settings as settings
from logging_config import setup_logging



logger = setup_logging()

CSV_LOG_FILE = 'request_log.csv'

# Columns we expect in our CSV:
CSV_HEADERS = [
    'Request ID',
    'Image ID',
    'Device',
    'Arrival Time',
    'Queue Exit Time',
    'Completion Time',
    'Latency',
    'Requested Latency',
    'Timed Out'
]


def init_csv():
    """Initialize the CSV file with headers if it doesn't already exist."""
    if not os.path.exists(CSV_LOG_FILE):
        with open(CSV_LOG_FILE, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def lock_and_read_csv():
    """
    Opens the CSV in read-write mode and acquires an exclusive lock.
    Reads all rows into a list of dicts, returns (file_object, rows).
    The caller is responsible for eventually writing rows back and releasing the lock.
    """
    f = open(CSV_LOG_FILE, mode='r+', newline='')  
    # Acquire an exclusive lock, blocking until we can get it
    fcntl.flock(f, fcntl.LOCK_EX)

    reader = csv.DictReader(f)
    rows = list(reader)  # read entire file into memory

    return f, rows


def write_csv_and_unlock(f, rows):
    """
    Rewinds the file, truncates it, writes out all rows (with headers),
    then releases the lock and closes the file.
    """
    # Go back to the start
    f.seek(0)
    f.truncate(0)
    writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    # Flush and unlock
    f.flush()
    fcntl.flock(f, fcntl.LOCK_UN)
    f.close()


def log_arrival(request_id, image_id, arrival_time, requested_latency):
    """
    Creates a new row for this Request ID + Image ID, with partial information.
    If the row already exists (very unlikely), we skip creation to prevent duplicates.
    """
    init_csv()

    # Acquire lock and read
    f, rows = lock_and_read_csv()

    # Check if row for (request_id, image_id) already exists
    for row in rows:
        if row['Request ID'] == request_id and row['Image ID'] == image_id:
            logger.warning(f"Row for {request_id} / {image_id} already exists. Skipping arrival log.")
            write_csv_and_unlock(f, rows)
            return

    new_row = {
        'Request ID': request_id,
        'Image ID': image_id,
        'Device': '',
        'Arrival Time': str(arrival_time),
        'Queue Exit Time': '',
        'Completion Time': '',
        'Latency': '',
        'Requested Latency': str(requested_latency),
        'Timed Out': ''
    }
    rows.append(new_row)

    # Write updated rows back, unlock, and close
    write_csv_and_unlock(f, rows)


def log_completion(request_id, image_id, device, queue_exit_time, completion_time, timed_out):
    """
    Finds the row matching (request_id, image_id), updates it with completion info,
    calculates latency, and marks timed_out as needed.
    """
    # Acquire lock and read
    f, rows = lock_and_read_csv()

    found = False
    for row in rows:
        if row['Request ID'] == request_id and row['Image ID'] == image_id:
            found = True
            row['Device'] = str(device)
            row['Queue Exit Time'] = str(queue_exit_time) if queue_exit_time else ''
            row['Completion Time'] = str(completion_time)
            row['Timed Out'] = 'True' if timed_out else 'False'

            # Compute latency
            try:
                arr = float(row['Arrival Time'])
                comp = float(completion_time)
                row['Latency'] = str(round(comp - arr, 5))
            except ValueError:
                # If any parse fails, leave it blank
                row['Latency'] = ''
            break

    if not found:
        logger.warning(f"No existing row for {request_id}/{image_id} to update completion info.")

    # Write updated rows back, unlock, and close
    write_csv_and_unlock(f, rows)


def LoudServer(queue, response_dict, response_dict_lock):
    app = Flask(__name__)
    init_csv()  # Ensure CSV is ready at startup

    @app.route('/')
    def home():
        return "Welcome to LoudVA!"

    @app.route('/info', methods=['GET'])
    def info():
        return (
            "This API is used to perform inference on images.\n"
            "POST to /inference with 'images' and optional 'latency' parameter.\n"
        )

    @app.route('/inference', methods=['POST'])
    def inference():
        try:
            if 'images' not in request.files:
                logger.error("No 'images' part in the request.")
                return jsonify({"status": "error", "message": "No file part"}), 400

            images = request.files.getlist('images')
            request_id = str(uuid.uuid4())
            latency_constraint = request.form.get('latency', type=float, default=settings.default_latency)
            arrival_time = time.time()

            image_ids = [f"{request_id}_{i}" for i in range(len(images))]
            logger.info(f"Received request {request_id} with {len(images)} images (latency={latency_constraint}).")

            # Log arrival for each image
            for image_id in image_ids:
                log_arrival(request_id, image_id, arrival_time, latency_constraint)

            # Enqueue images for the Scheduler/Workers
            image_data = [
                (image.read(), img_id, latency_constraint, arrival_time)
                for image, img_id in zip(images, image_ids)
            ]
            for data_item in image_data:
                queue.put(data_item)

            responses = {}
            timeout = 90  # 1 minutes 30 seconds
            start_time = time.time()

            # Wait for responses
            while len(responses) < len(image_ids):
                if time.time() - start_time > timeout:
                    logger.warning(f"Timeout reached for request {request_id}")
                    break

                for img_id in image_ids:
                    with response_dict_lock:
                        if img_id in response_dict:
                            responses[img_id] = response_dict.pop(img_id)
                time.sleep(0.01)

            completion_time = time.time()

            # Update CSV with device/queue exit times or mark them timed out
            for img_id in image_ids:
                if img_id not in responses:
                    log_completion(
                        request_id,
                        img_id,
                        device='N/A',
                        queue_exit_time='',
                        completion_time=completion_time,
                        timed_out=True
                    )
                else:
                    # e.g. [result, something_else, device, queue_exit_time]
                    device = responses[img_id][-2]
                    q_exit = responses[img_id][-1]
                    log_completion(
                        request_id,
                        img_id,
                        device=device,
                        queue_exit_time=q_exit,
                        completion_time=completion_time,
                        timed_out=False
                    )

            total_latency = round(completion_time - arrival_time, 5)
            return jsonify({
                "status": "completed",
                "response": responses,
                "latency": total_latency
            }), 200

        except Exception as e:
            logger.error("Error during inference", exc_info=True)
            return jsonify({
                "status": "error",
                "message": "Internal server error"
            }), 500

    @app.route('/resources', methods=['GET'])
    def resources():
        with response_dict_lock:
            return jsonify({
                "queue_size": queue.qsize(),
                "response_dict": dict(response_dict)
            }), 200

    return app

def run_server(queue, response_dict, response_dict_lock):
    logger.info("Starting LoudVA server with concurrency-safe CSV logging...")
    app = LoudServer(queue, response_dict, response_dict_lock)
    # This is typically run by gunicorn externally, or you could do:
    # app.run(debug=False, port=5000, threaded=True)
    app.run(debug=False, port=5000, threaded=True)

if __name__ == '__main__':
    pass

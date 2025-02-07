import csv
import os
import time
import uuid
from flask import Flask, request, jsonify
import Settings as settings
from logging_config import setup_logging

# Configure logging
logger = setup_logging()

# Define CSV log file path
CSV_LOG_FILE = 'request_log.csv'

# Initialize CSV file and write headers if it doesn't exist
if not os.path.exists(CSV_LOG_FILE):
    with open(CSV_LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Request ID', 'Image ID', 'Arrival Time', 'Queue Exit Time', 
                        'Completion Time', 'Latency', 'Requested Latency', 'Timed Out'])

def log_request_to_csv(request_id, image_id, arrival_time, queue_exit_time, 
                       completion_time, requested_latency, timed_out):
    actual_latency = completion_time - arrival_time
    with open(CSV_LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            request_id,
            image_id,
            arrival_time,
            queue_exit_time,
            completion_time,
            actual_latency,
            requested_latency,
            timed_out
        ])

def LoudServer(queue, response_dict):
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Welcome to LoudVA!"

    @app.route('/info', methods=['GET'])
    def info():
        return "This API is used to perform inference on images. Send a POST request to the /inference endpoint with the 'images' part containing the images to be processed. Optionally, you can provide a 'latency' parameter to specify the maximum latency in seconds for the inference process.\n"

    @app.route('/inference', methods=['POST'])
    def inference():
        try:
            # Check if the POST request has the 'images' part
            if 'images' not in request.files:
                logger.error("No file part in the request")
                return jsonify({"status": "error", "message": "No file part"}), 400

            images = request.files.getlist('images')
            request_id = str(uuid.uuid4())

            # Extract latency constraint from the request, default to a reasonable value if not provided
            latency_constraint = request.form.get('latency', type=float, default=settings.default_latency)
            logger.info(f"Received inference request with latency constraint: {latency_constraint}")

            # Create a unique ID for every image in the request
            image_ids = [f"{request_id}_{i}" for i in range(len(images))]

            # Record arrival time of the request
            arrival_time = time.time()

            # Convert images to bytes
            image_data = [(image.read(), image_id, latency_constraint, arrival_time) for image, image_id in zip(images, image_ids)]

            # Add each image to the scheduler's queue with its unique ID
            for data in image_data:
                queue.put(data)

            # Wait for all responses to be available in the response dictionary
            logger.debug(f"Waiting for responses for images: {image_ids}")
            responses = {}
            timeout = 300  # 5 minutes timeout
            start_time = time.time()

            while len(responses) < len(image_ids):
                if time.time() - start_time > timeout:
                    logger.warning(f"Timeout reached for request {request_id}")
                    break
                
                for image_id in image_ids:
                    if image_id in response_dict:
                        responses[image_id] = response_dict.pop(image_id)
                        logger.debug(f"Response received for image: {image_id}")
                
                time.sleep(0.01)

            end_time = time.time()

            # Log all images, marking timed out ones
            for image_id in image_ids:
                if image_id in responses:
                    queue_exit_time = responses[image_id][-1]
                    log_request_to_csv(request_id, image_id, arrival_time, 
                                      queue_exit_time, end_time, latency_constraint, False)
                else:
                    log_request_to_csv(request_id, image_id, arrival_time, 
                                      None, end_time, latency_constraint, True)

            logger.info(f"Inference completed. Request ID: {request_id}")
            return jsonify({"status": "completed", "response": responses, "latency": end_time - arrival_time}), 200
        
        except Exception as e:
            logger.error("An error occurred during inference", exc_info=True)
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/resources', methods=['GET'])
    def resources():
        return jsonify({"queue_size": queue.qsize(), "response_dict": dict(response_dict)}), 200

    return app

def run_server(queue, response_dict):
    app = LoudServer(queue, response_dict)
    app.run(debug=False, port=5000, threaded=True)

if __name__ == '__main__':
    pass

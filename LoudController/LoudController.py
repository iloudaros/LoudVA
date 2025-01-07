from flask import Flask, request, jsonify
import LoudScheduler as scheduler
import Settings as settings
import time
from logging_config import setup_logging

app = Flask(__name__)

# Configure logging
logger = setup_logging()

@app.route('/')
def home():
    return "Welcome to LoudVA!"

@app.route('/inference', methods=['POST'])
def inference():
    try:
        # Check if the POST request has the 'images' part
        if 'images' not in request.files:
            logger.error("No file part in the request")
            return jsonify({"status": "error", "message": "No file part"}), 400

        images = request.files.getlist('images')
        request_id = str(time.time())

        # Extract latency constraint from the request, default to a reasonable value if not provided
        latency_constraint = request.form.get('latency', type=float, default=settings.default_latency)

        logger.info(f"Received inference request with latency constraint: {latency_constraint}")
        logger.debug(f"Images: {images}")

        # Create a unique ID for every image in the request
        image_ids = [f"{request_id}_{i}" for i in range(len(images))]


        # Add each image to the scheduler's queue with its unique ID
        for image, image_id in zip(images, image_ids):
            scheduler.request_queue.append((image, image_id, latency_constraint))



        # Wait for all responses to be available in the response dictionary
        responses = {}
        while len(responses) < len(image_ids):
            for image_id in image_ids:
                if image_id in scheduler.response_dict:
                    responses[image_id] = scheduler.response_dict.pop(image_id)
            time.sleep(0.01)
        
        # Wait for the response to be available in the response dictionary
        while request_id not in scheduler.response_dict:
            time.sleep(0.01)
        
        logger.info(f"Inference completed for request ID: {request_id}")
        return jsonify({"status": "completed", "response": responses})
    except Exception as e:
        logger.error("An error occurred during inference", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


if __name__ == '__main__':

    logger.info("Starting LoudController")

    # Start the scheduler
    scheduler.start_scheduler(settings.max_wait_time)

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)

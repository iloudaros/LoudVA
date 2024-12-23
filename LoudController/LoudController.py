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
        logger.debug(f"Received inference request: {images}")
        request_id = str(time.time())

        # Extract latency constraint from the request, default to a reasonable value if not provided
        latency_constraint = request.form.get('latency', type=float, default=settings.default_latency)

        logger.info(f"Received inference request with latency constraint: {latency_constraint}")


        # Add the request to the scheduler's queue with the latency constraint
        scheduler.request_queue.append((images, request_id, latency_constraint))
        
        # Wait for the response to be available in the response dictionary
        while request_id not in scheduler.response_dict:
            time.sleep(0.01)
        
        response = scheduler.response_dict.pop(request_id)
        logger.info(f"Inference completed for request ID: {request_id}")
        return jsonify({"status": "completed", "response": response})
    except Exception as e:
        logger.error("An error occurred during inference", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


if __name__ == '__main__':

    logger.info("Starting LoudController")

    # Start the scheduler
    scheduler.start_scheduler(settings.max_wait_time)

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, request, jsonify
import LoudScheduler as scheduler
import Settings as settings
import time
import uuid
from logging_config import setup_logging

# Configure logging
logger = setup_logging()

def LoudServer(queue, response_dict):
    app = Flask(__name__)



    @app.route('/')
    def home():
        return "Welcome to LoudVA!"

    @app.route('/info', methods=['GET'])
    def info():
        # return instructions on how to use the API
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
            logger.debug(f"Images: {images}")

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
            while len(responses) < len(image_ids):
                for image_id in image_ids:
                    if image_id in response_dict:
                        logger.debug(f"Response received for image: {image_id}")
                        responses[image_id] = response_dict.pop(image_id)
                        logger.debug(f"Responses: {responses}")
                time.sleep(0.1)
            
            end_time = time.time()

            logger.info(f"Inference completed for request ID: {request_id}")
            return jsonify({"status": "completed", "response": responses, "latency": end_time - arrival_time}), 200
        except Exception as e:
            logger.error("An error occurred during inference", exc_info=True)
            return jsonify({"status": "error", "message": "Internal server error"}), 500
        
    return app
    


def run_server(queue, response_dict):
    app = LoudServer(queue, response_dict)
    app.run(debug=False, port=5000, threaded=True)

if __name__ == '__main__':

   pass

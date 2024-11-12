from flask import Flask, request, jsonify
import LoudScheduler as scheduler
import Settings as settings
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to LoudVA!"

@app.route('/infer', methods=['POST'])
def infer():
    image = request.get_json().get('image')
    request_id = str(time.time())
    scheduler.request_queue.append((image, request_id))
    
    # Wait for the response to be available in the response dictionary
    while request_id not in scheduler.response_dict:
        time.sleep(0.01)
    
    response = scheduler.response_dict.pop(request_id)
    return jsonify({"status": "completed", "response": response})

if __name__ == '__main__':
    # Start the scheduler
    scheduler.start_scheduler(settings.max_latency, settings.max_wait_time)

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)

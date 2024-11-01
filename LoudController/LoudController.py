from flask import Flask, request, jsonify
import LoudScheduler as scheduler
import Settings as settings

app = Flask(__name__)

@app.route('/test/<string:name>', methods=['GET'])
def test(name):
    return f"Hello, {name}!"

@app.route('/')
def home():
    return "Welcome to LoudVA!"

@app.route('/infer', methods=['POST'])
def infer():
    image = request.get_json().get('image')
    scheduler.request_queue.append((image, time.time()))
    return jsonify({"status": "queued"})

if __name__ == '__main__':
    # Start the scheduler
    scheduler.start_scheduler(settings.max_latency, settings.max_wait_time)

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)

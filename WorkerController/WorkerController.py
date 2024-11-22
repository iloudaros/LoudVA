from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to WorkerController!"

@app.route('/set_gpu_freq/<int:freq>', methods=['GET'])
def set_gpu_freq(freq):
    try:
        # Execute the bash script with the provided frequency
        result = subprocess.run(['../scripts/shell/set_gpu_freq.sh', str(freq)], capture_output=True, text=True, check=True)
        
        # Return the script's output
        return jsonify({"message": result.stdout}), 200

    except subprocess.CalledProcessError as e:
        # Return the error if the script fails
        return jsonify({"error": e.stderr}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


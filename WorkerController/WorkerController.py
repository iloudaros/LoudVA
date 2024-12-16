from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return 'running'

@app.route('/set_gpu_freq/<int:freq>', methods=['GET'])
def set_gpu_freq(freq):
    try:
        # Run the shell script with the provided frequency
        result = subprocess.run(
            ['/home/iloudaros/LoudVA/scripts/shell/set_frequency.sh', str(freq)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,  # Use this instead of text=True
            check=True
        )
        return jsonify({"message": result.stdout}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500
    

def current_gpu_freq():
    # Run the shell script to get the current GPU frequency
    result = subprocess.run(
        ['/home/iloudaros/LoudVA/scripts/shell/get_frequency.sh'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,  # Use this instead of text=True
        check=True
    )
    return result.stdout

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

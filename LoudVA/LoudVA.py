from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)
UPLOAD_FOLDER = '/home/louduser/incoming'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# Queue for Jetson
queue = []

turn = 0 

def get_turn(turn):
    turn
    turn = turn + 1
    if turn ==3:
        turn = 0
    return turn
###################






# Routes
@app.route('/')
def home():
    return "Welcome to LoudVA!"

@app.route('/get-user/<user_id>')
def get_user(user_id):
    user_data = {
        'user_id': user_id,
        'name': 'John Doe',
        'email': 'example@example.com'
    }

    extra = request.args.get('extra')
    if extra:
        user_data['extra'] = extra

    return jsonify(user_data), 200

@app.route('/create-user', methods=['POST'])
def create_user():
    data = request.get_json()

    return jsonify(data), 201   


@app.route('/classify/<model>/<classes>/<scaling>', methods=['POST'])
def classify_image(model, classes, scaling):
    global turn
    file = request.files['file']
    print("Request to LoudJetson"+str(turn)+f" with model {model}, classes {classes}, scaling {scaling}. Filname: {file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    p = subprocess.run([f"python3 ~/LoudVA/LoudVA/image_client.py -m {model} -c {classes} -s {scaling} ~/incoming/{file.filename} --url 192.168.0.12{str(turn)}:8000 --protocol HTTP "],shell=True, capture_output=True, text=True) 
    turn = get_turn(turn)
    print("Result \n"+p.stdout)
    return p.stdout, 200

@app.route('/now')
def now():
    p = subprocess.run(["date"],shell=True, capture_output=True, text=True) 
    print("Result \n"+p.stdout)
    return p.stdout, 200






# Run Server
if __name__ == '__main__':
    app.run(debug=True)

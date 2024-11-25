import os
import requests

# Define the server URL
SERVER_URL = 'http://localhost:5000/inference'

# Define the path to the images directory
IMAGES_DIR = '/home/louduser/LoudVA/data/images/'

def test_inference():
    # Collect all image files in the directory
    image_files = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]

    if not image_files:
        print("No images found in the directory.")
        return

    # Prepare the files for the POST request
    files = [('images', open(os.path.join(IMAGES_DIR, image), 'rb')) for image in image_files]

    # Define the latency constraint (optional)
    latency_constraint = 0.8  

    # Make the POST request to the inference endpoint
    try:
        response = requests.post(SERVER_URL, files=files, data={'latency': latency_constraint})

        # Check if the request was successful
        if response.status_code == 200:
            print("Inference successful.")
            print("Response:", response.json())
        else:
            print("Inference failed with status code:", response.status_code)
            print("Response:", response.text)

    except requests.exceptions.RequestException as e:
        print("An error occurred while making the request:", e)

if __name__ == '__main__':
    test_inference()

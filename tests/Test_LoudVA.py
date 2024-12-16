import os
import requests

# Check if the server is running on any of the specified URLs
SERVER_URLS = ['http://localhost:5000/', 'http://localhost:8000/']
respones = []
server_is_active = False

for server_url in SERVER_URLS:
    try:
        response = requests.get(server_url)
        respones.append(response)
    except requests.exceptions.RequestException as e:
        respones.append(e)

for response in respones:
    if isinstance(response, requests.models.Response):
        print("Server is running on port:", response.url)
        active_url = response.url
        server_is_active = True

if not server_is_active:
    print("No server is running. Exiting the test.")
    exit()

# Define the server URL as the one that is running
SERVER_URL = active_url + 'inference'

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
    latency_constraint = 4

    # Make the POST request to the inference endpoint
    try:
        response = requests.post(SERVER_URL, files=files, data={'latency': latency_constraint})

        # Check if the request was successful
        if response.status_code == 200:
            print("Inference successful.")
            response_json = response.json()
            print("Response:", response_json)
            # Verify that the response contains results for all images
            assert len(response_json['response'][0]) == len(image_files), "Mismatch in number of results"
            print("Number of results matches the number of images.")
        else:
            print("Inference failed with status code:", response.status_code)
            print("Response:", response.text)

    except requests.exceptions.RequestException as e:
        print("An error occurred while making the request:", e)

if __name__ == '__main__':
    test_inference()

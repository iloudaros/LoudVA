import os
import requests
import random
import time

# Check if the server is running on any of the specified URLs
SERVER_URLS = ['http://localhost:5000/', 'http://localhost:8000/']
responses = []
server_is_active = False

for server_url in SERVER_URLS:
    try:
        response = requests.get(server_url)
        responses.append(response)
    except requests.exceptions.RequestException as e:
        responses.append(e)

for response in responses:
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

    # Send requests with a random number of images per second
    while True:
        # Select a random number of images to send
        num_images = random.randint(1, len(image_files))
        selected_images = random.sample(image_files, num_images)

        # Prepare the files for the POST request
        files = [('images', open(os.path.join(IMAGES_DIR, image), 'rb')) for image in selected_images]

        # Define a random latency constraint
        latency_constraint = random.randint(1, 20)

        # Print the selected images and latency constraint
        print(f"Selected images: {selected_images}")
        print(f"Latency constraint: {latency_constraint}")

        # Make the POST request to the inference endpoint
        try:
            response = requests.post(SERVER_URL, files=files, data={'latency': latency_constraint})
            print(f'Response: {response}')

            # Check if the request was successful
            if response.status_code == 200:
                print("Inference successful.")
                response_json = response.json()
                print("Response:", response_json)
                # Verify that the response contains results for all images
                assert len(response_json['response']) == len(selected_images), "❌ Mismatch in number of results"
                print("✅ Number of results matches the number of images.")
            else:
                print("❌ Inference failed with status code:", response.status_code)
                print("Response:", response.text)

        except requests.exceptions.RequestException as e:
            print("An error occurred while making the request:", e)

        # Close the file handlers
        for _, file in files:
            file.close()

        # Wait for 1 second before sending the next request
        time.sleep(1)

if __name__ == '__main__':
    test_inference()

import os
import requests
import random
import time
import threading

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
IMAGES_DIR = '/home/louduser/images'

# Lock for synchronizing access to the active_requests counter
active_requests_lock = threading.Lock()
active_requests = 0
MAX_ACTIVE_REQUESTS = 5

# Function to handle a single request
def send_request(selected_images, latency_constraint):
    global active_requests

    # Prepare the files for the POST request
    files = [('images', open(os.path.join(IMAGES_DIR, image), 'rb')) for image in selected_images]

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

    finally:
        # Close the file handlers
        for _, file in files:
            file.close()

        # Decrement the active requests counter
        with active_requests_lock:
            active_requests -= 1

def start(duration_minutes=60):

    print(f"Starting test for {duration_minutes} minutes...")
    
    global active_requests

    # Collect all image files in the directory
    image_files = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]

    if not image_files:
        print("No images found in the directory.")
        return
    
    end_time = time.time() + duration_minutes * 60

    while time.time() < end_time:
        # Check if the number of active requests is less than the maximum allowed
        with active_requests_lock:
            if active_requests >= MAX_ACTIVE_REQUESTS:
                print("Maximum number of active requests reached. Waiting...")
                time.sleep(1)  # Wait briefly before checking again
                continue

            # Increment the active requests counter
            active_requests += 1

        # Select 64 random images
        selected_images = random.choices(image_files, k=64)

        # Print the selected images
        print(f"Selected images: {selected_images}")

        # Set the latency constraint
        latency = 1

        # Send request
        threading.Thread(target=send_request, args=(selected_images, latency)).start()

        # Wait for 5 seconds before attempting to send the next batch
        time.sleep(5)
    
    print(f"Test completed after {duration_minutes} minutes.")


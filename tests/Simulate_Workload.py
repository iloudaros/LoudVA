import os
import requests
import random
import time
import threading
import csv

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
IMAGES_DIR = '../images'

# Function to simulate a camera sending requests
def simulate_camera(camera_index, schedule):
    # Collect all image files in the directory
    image_files = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]

    if not image_files:
        print("No images found in the directory.")
        return

    start_time = time.time()

    for entry in schedule:
        target_time, num_frames = entry
        # Wait until the scheduled time
        time_to_wait = target_time - (time.time() - start_time)
        if time_to_wait > 0:
            time.sleep(time_to_wait)

        # Select the specified number of images
        selected_images = random.sample(image_files, num_frames)

        # Prepare the files for the POST request
        files = [('images', open(os.path.join(IMAGES_DIR, image), 'rb')) for image in selected_images]

        # Define a random latency constraint
        latency_constraint = random.randint(1, 10)

        # Print the selected images and latency constraint
        print(f"Camera {camera_index} - Selected images: {selected_images}")
        print(f"Camera {camera_index} - Latency constraint: {latency_constraint}")

        # Make the POST request to the inference endpoint
        try:
            response = requests.post(SERVER_URL, files=files, data={'latency': latency_constraint})
            print(f'Camera {camera_index} - Response: {response}')

            # Check if the request was successful
            if response.status_code == 200:
                print(f"Camera {camera_index} - Inference successful.")
                response_json = response.json()
                print(f"Camera {camera_index} - Response:", response_json)
                # Verify that the response contains results for all images
                assert len(response_json['response']) == num_frames, "❌ Mismatch in number of results"
                print(f"Camera {camera_index} - ✅ Number of results matches the number of images.")
            else:
                print(f"Camera {camera_index} - ❌ Inference failed with status code:", response.status_code)
                print(f"Camera {camera_index} - Response:", response.text)

        except requests.exceptions.RequestException as e:
            print(f"Camera {camera_index} - An error occurred while making the request:", e)

        # Close the file handlers
        for _, file in files:
            file.close()

def load_camera_schedule(csv_filename):
    camera_schedules = {}
    with open(csv_filename, mode='r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            time = float(row['Time'])
            frames = int(row['Frames After Filter'])
            camera_index = int(row['Camera Index'])

            if camera_index not in camera_schedules:
                camera_schedules[camera_index] = []

            camera_schedules[camera_index].append((time, frames))

    return camera_schedules

def main():
    # Load the camera schedule from the CSV file
    camera_schedules = load_camera_schedule('camera_schedule.csv')

    # Start a thread for each camera
    threads = []
    for camera_index, schedule in camera_schedules.items():
        thread = threading.Thread(target=simulate_camera, args=(camera_index, schedule))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()

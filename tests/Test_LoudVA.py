import os
import random
import asyncio
import aiohttp

# Check if the server is running on any of the specified URLs
SERVER_URLS = ['http://localhost:5000/', 'http://localhost:8000/']
server_is_active = False
active_url = None

async def check_server():
    global server_is_active, active_url
    async with aiohttp.ClientSession() as session:
        for server_url in SERVER_URLS:
            try:
                async with session.get(server_url) as response:
                    if response.status == 200:
                        print("Server is running on port:", server_url)
                        active_url = server_url
                        server_is_active = True
                        return
            except aiohttp.ClientError as e:
                print(f"Error connecting to {server_url}: {e}")

async def test_inference():
    if not server_is_active:
        print("No server is running. Exiting the test.")
        return

    # Define the server URL as the one that is running
    SERVER_URL = active_url + 'inference'

    # Define the path to the images directory
    IMAGES_DIR = '/home/louduser/LoudVA/data/images/'

    # Collect all image files in the directory
    image_files = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]

    if not image_files:
        print("No images found in the directory.")
        return

    async with aiohttp.ClientSession() as session:
        while True:
            # Select a random number of images to send
            num_images = random.randint(1, len(image_files))
            selected_images = random.sample(image_files, num_images)

            # Prepare the files for the POST request
            data = aiohttp.FormData()
            for image in selected_images:
                file_path = os.path.join(IMAGES_DIR, image)
                data.add_field('images', open(file_path, 'rb'), filename=image, content_type='application/octet-stream')

            # Define a random latency constraint
            latency_constraint = random.randint(1, 10)
            data.add_field('latency', str(latency_constraint))

            # Make the POST request to the inference endpoint
            try:
                async with session.post(SERVER_URL, data=data) as response:
                    print(f'Response: {response.status}')

                    # Check if the request was successful
                    if response.status == 200:
                        response_json = await response.json()
                        print("Inference successful.")
                        print("Response:", response_json)
                        # Verify that the response contains results for all images
                        assert len(response_json['response'][0]) == len(selected_images), "❌ Mismatch in number of results"
                        print("✅ Number of results matches the number of images.")
                    else:
                        print("❌ Inference failed with status code:", response.status)
                        print("Response:", await response.text())

            except aiohttp.ClientError as e:
                print("An error occurred while making the request:", e)

            finally:
                # Close the file handlers
                for field in data._fields:
                    if hasattr(field[2], 'close'):
                        field[2].close()

            # Wait before sending the next request
            await asyncio.sleep(0.8)

async def main():
    await check_server()
    await test_inference()

if __name__ == '__main__':
    asyncio.run(main())

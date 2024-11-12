import requests
import base64
import json

# Path to the image you want to test
image_path = '/home/louduser/LoudVA/data/images/brown_bear.jpg'

# URL of the LoudController API
url = 'http://localhost:8000/infer'

def load_image_as_base64(image_path):
    """Load an image and encode it as a base64 string."""
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_inference():
    # Load the image and encode it as base64
    image_base64 = load_image_as_base64(image_path)

    # Prepare the payload for the POST request
    payload = json.dumps({
        'image': image_path
    })

    # Send the POST request to the LoudController
    response = requests.post(url, data=payload, headers={'Content-Type': 'application/json'})

    # Print the response from the server
    if response.status_code == 200:
        print("Test Passed. Response from server:")
        print(response.json())
    else:
        print(f"Test Failed. Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_inference()

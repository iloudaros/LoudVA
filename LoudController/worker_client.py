import requests
from logging_config import setup_logging

# Configure logging
logger = setup_logging()

def set_gpu_frequency(ip, frequency):
    """
    Sends an HTTP request to the Flask app to set the GPU frequency.

    Args:
        ip (str): The IP address of the Flask server.
        frequency (int): The frequency to set for the GPU.

    Returns:
        dict: A dictionary containing the status code and response message.
    """

    url = f"http://{ip}:5000/set_gpu_freq/{frequency}"
    try:
        response = requests.get(url)
        logger.info(f"Set GPU frequency to {frequency} on {ip}")
        return {
            'status_code': response.status_code,
            'message': response.text
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to set GPU frequency on {ip}: {e}")
        return {
            'status_code': None,
            'message': str(e)
        }

# Example usage
if __name__ == "__main__":
    ip_address = "192.168.0.120"  
    frequency = '921600000'           
    print(f"Setting GPU frequency to {frequency} MHz on {ip_address}...")
    result = set_gpu_frequency(ip_address, frequency)
    print(f"Status Code: {result['status_code']}, Message: {result['message']}")

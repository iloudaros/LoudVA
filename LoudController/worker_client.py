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
        logger.debug(f"HTTP request sent to {url}")
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

def get_gpu_frequency(ip):
    """
    Sends an HTTP request to the Flask app to get the current GPU frequency.

    Args:
        ip (str): The IP address of the Flask server.

    Returns:
        dict: A dictionary containing the status code and response message.
    """

    url = f"http://{ip}:5000/get_gpu_freq"
    try:
        response = requests.get(url)
        logger.debug(f"HTTP request sent to {url}")
        return {
            'status_code': response.status_code,
            'message': response.text
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get GPU frequency on {ip}: {e}")
        return {
            'status_code': None,
            'message': str(e)
        }
    
def health_check(ip):
    """
    Sends an HTTP request to the Flask app to check the health of the server.

    Args:
        ip (str): The IP address of the Flask server.

    Returns:
        dict: A dictionary containing the status code and response message.
    """

    url = f"http://{ip}:5000/"
    try:
        response = requests.get(url)
        logger.debug(f"HTTP request sent to {url}")
        return {
            'status_code': response.status_code,
            'message': response.text
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check health of the server on {ip}: {e}")
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

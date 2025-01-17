from multiprocessing import Process, Queue, Manager # Queue and Manager.dict are both thread and process safe
from LoudServer import run_server
from LoudScheduler import LoudScheduler
import Settings as settings
from logging_config import setup_logging

# Alternative schedulers
from altSchedulers.RandomScheduler import RandomScheduler
from altSchedulers.RoundRobinScheduler import RoundRobinScheduler

# Configure logging
logger = setup_logging()

def start_processes():
    # Create a shared queue for messages and a manager dictionary for responses
    message_queue = Queue()
    manager = Manager()
    response_dict = manager.dict()

    # Start the server process
    server_process = Process(target=run_server, args=(message_queue, response_dict))
    server_process.start()

    # Start the printer process as a separate deamon process
    scheduler = RoundRobinScheduler(4)
    scheduler_process = Process(target=scheduler.start, args=(message_queue, response_dict))
    scheduler_process.start()

    # Join processes to keep them running
    server_process.join()
    scheduler_process.join()

if __name__ == '__main__':
    logger.info("Starting LoudController...")
    logger.info("Press CTRL+C to stop the controller.")
    logger.info(f"Debug mode: {settings.debug}") 
    start_processes()
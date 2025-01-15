from multiprocessing import Process, Queue, Manager # Queue and Manager.dict are both thread and process safe
from LoudServer import run_server
from LoudScheduler import manage_batches
import Settings as settings

def start_processes():
    # Create a shared queue for messages and a manager dictionary for responses
    message_queue = Queue()
    manager = Manager()
    response_dict = manager.dict()

    # Start the server process
    server_process = Process(target=run_server, args=(message_queue, response_dict))
    server_process.start()

    # Start the printer process as a separate deamon process
    scheduler_process = Process(target=manage_batches, args=(message_queue, response_dict))
    scheduler_process.start()

    # Join processes to keep them running
    server_process.join()
    scheduler_process.join()

if __name__ == '__main__':
    start_processes()
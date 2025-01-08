from multiprocessing import Manager, Lock

def initialize_shared_resources():
    manager = Manager()
    request_queue = manager.Queue()
    response_dict = manager.dict()
    shared_queue_lock = Lock()
    shared_response_lock = Lock()
    return request_queue, response_dict, shared_queue_lock, shared_response_lock

# Initialize shared resources
request_queue, response_dict, shared_queue_lock, shared_response_lock = initialize_shared_resources()


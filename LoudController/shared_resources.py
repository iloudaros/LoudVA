from multiprocessing import Manager, Lock

class SharedResources:
    _instance = None

    def __init__(self):
        if SharedResources._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            manager = Manager()
            self.request_queue = manager.Queue()
            self.response_dict = manager.dict()
            self.shared_queue_lock = Lock()
            self.shared_response_lock = Lock()
            SharedResources._instance = self

    @staticmethod
    def get_instance():
        if SharedResources._instance is None:
            SharedResources()
        return SharedResources._instance

# Access shared resources
shared_resources = SharedResources.get_instance()
request_queue = shared_resources.request_queue
response_dict = shared_resources.response_dict
shared_queue_lock = shared_resources.shared_queue_lock
shared_response_lock = shared_resources.shared_response_lock

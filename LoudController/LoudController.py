from multiprocessing import Process, Queue, Manager # Queue and Manager.dict are both thread and process safe
from LoudServer import run_server
import Settings as settings
from logging_config import setup_logging

# Configure logging
logger = setup_logging()


# Scheduler selection : Import only the scheduler you want to use and return an instance of it
def selected_scheduler():
    logger.info(f"Selected scheduler: {settings.scheduler}")
    if single_device:
        if settings.scheduler == 'random':
            from altSchedulers.SingleDevice.RandomScheduler import RandomScheduler
            return RandomScheduler()
        elif settings.scheduler == 'stress':
            from altSchedulers.SingleDevice.StressScheduler import StressScheduler
            return StressScheduler()
        elif settings.scheduler == 'interval':
            from altSchedulers.SingleDevice.IntervalScheduler import IntervalScheduler
            logger.info(f"Using batching interval {settings.batching_interval}")
            return IntervalScheduler(settings.batching_interval)
        elif settings.scheduler == 'transparent':
            from altSchedulers.SingleDevice.TransparentScheduler import TransparentScheduler
            return TransparentScheduler()
        elif settings.scheduler == 'fixed_batch':
            from altSchedulers.SingleDevice.FixedBatchScheduler import FixedBatchScheduler
            logger.info(f"Using fixed batch size {settings.fixed_batch_size}")
            return FixedBatchScheduler(settings.fixed_batch_size, 15)
        else:
            from LoudScheduler import LoudScheduler
            return LoudScheduler()
    else:
        if settings.scheduler == 'round_robin':
            from altSchedulers.Cluster.RoundRobinScheduler import RoundRobinScheduler
            return RoundRobinScheduler()
        elif settings.scheduler == 'kind_round_robin'
            from altSchedulers.Cluster.KindRoundRobinScheduler import KindRoundRobinScheduler
            return KindRoundRobinScheduler()
        elif settings.scheduler == 'interval':
            from altSchedulers.Cluster.IntervalScheduler import IntervalScheduler
            logger.info(f"Using batching interval {settings.batching_interval}")
            return IntervalScheduler(settings.batching_interval)
        elif settings.scheduler == 'fixed_batch':
            from altSchedulers.Cluster.FixedBatchScheduler import FixedBatchScheduler
            logger.info(f"Using fixed batch size {settings.fixed_batch_size}")
            return FixedBatchScheduler(settings.fixed_batch_size, 15)
        else:
            from LoudScheduler import LoudScheduler
            return LoudScheduler()




def start_processes():
    # Create a shared queue for messages and a manager dictionary for responses
    message_queue = Queue()
    manager = Manager()
    response_dict = manager.dict()

    # Start the server process
    server_process = Process(target=run_server, args=(message_queue, response_dict))
    server_process.start()

    # Start the printer process as a separate deamon process
    scheduler = selected_scheduler()
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
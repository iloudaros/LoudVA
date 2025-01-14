import multiprocessing
import signal
import sys
from LoudScheduler import start_scheduler
from LoudServer import app

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def signal_handler(sig, frame):
    print('Shutting down...')
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the scheduler in a separate process
    scheduler_process = multiprocessing.Process(target=start_scheduler)
    scheduler_process.start()

    # Start the Flask server in the main process
    run_flask()

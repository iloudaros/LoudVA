# This is an experiment to test the LoudScheduler against the RoundRobinScheduler and RandomScheduler. The experiment will run the LoudController with each scheduler and compare the results.
# We will use the simulated workload from LoudGenerator.py to test the schedulers.
# The outline of the experiment is as follows:
# 1. Empty the request_log.csv and LoudController.log files if they exist.
# 2. Start the LoudController with the LoudScheduler.
# 3. Start collecting data on the workers (Temperature, Power).
# 4. Start Simulate_Workload.py to generate requests.
# 5. Wait for the requests to finish processing.
# 6. Stop the LoudController.
# 7. Stop collecting data on the workers.
# 8. Repeat steps 1-8 for the RoundRobinScheduler and RandomScheduler.

import os
import time
import subprocess

schedulers = ['loud', 'round_robin', 'random']

def empty_logs():
    # Delete the logs if they exist
    if os.path.exists('request_log.csv'):
        os.remove('request_log.csv')
    if os.path.exists('LoudController.log'):
        os.remove('LoudController.log')

def set_scheduler(scheduler):
    with open('LoudController/Settings.py', 'r') as file:
        data = file.readlines()

    for i, line in enumerate(data):
        if line.startswith('scheduler'):
            data[i] = f"    scheduler = '{scheduler}' # Options: 'loud', 'random', 'round_robin'\n"

    with open('Settings.py', 'w') as file:
        file.writelines(data)

def start_controller():
    controller = subprocess.Popen(['make', 'start_LoudController'])
    return controller

def stop_controller():
    controller = subprocess.Popen(['pkill', 'screen'])
    return controller


def start_data_collection(scheduler):
    # Set tegrastats_log_name to [date]_[scheduler]_tegrastats
    tegrastats_log_name = f"{time.strftime('%Y-%m-%d_%H:%M:%S')}_{scheduler}_tegrastats"

    # Change the name of the variable in the makefile
    with open('makefile', 'r') as file:
        data = file.readlines()

        for i, line in enumerate(data):
            if line.startswith('tegrastats_log_name'):
                data[i] = f"tegrastats_log_name = {tegrastats_log_name}\n"
    
        with open('makefile', 'w') as file:
            file.writelines(data)

    # Start data collection
    data_collection = subprocess.Popen(['make', 'remote_start_tegrastats'])
    return data_collection

def stop_data_collection():
    data_collection = subprocess.Popen(['make', 'remote_stop_tegrastats'])
    return data_collection

def retrieve_data():
    data_collection = subprocess.Popen(['make', 'retrieve_tegrastats'])
    return data_collection

def simulate_workload():
    workload = subprocess.Popen(['make', 'simulate_workload'])
    return workload

def rename_logs(scheduler):
    os.rename('request_log.csv', f'{time.strftime("%Y-%m-%d_%H:%M:%S")}_{scheduler}_request_log.csv')
    os.rename('LoudController.log', f'{time.strftime("%Y-%m-%d_%H:%M:%S")}_{scheduler}_LoudController.log')


def main():
    empty_logs()

    for scheduler in schedulers:
        print(f"Running experiment with {scheduler} scheduler")
        set_scheduler(scheduler)
        controller = start_controller()

        # Wait for the controller to start
        time.sleep(10)

        data_collection = start_data_collection(scheduler)
        workload = simulate_workload()

        controller.wait()
        data_collection.wait()
        workload.wait()

        stop_data_collection()
        data_retrieval = retrieve_data()

        data_retrieval.wait()
        rename_logs(scheduler)
        
        stop_controller()
        empty_logs()
        
if __name__ == '__main__':
    main()



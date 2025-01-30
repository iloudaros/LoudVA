# This is an experiment to stress test the LoudController with the StressScheduler. The experiment will run the LoudController with the StressScheduler and compare the results.

import os
import time
import subprocess

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
            data[i] = f"scheduler = '{scheduler}' # Options: 'loud', 'random', 'round_robin', 'stress'\n"

    with open('LoudController/Settings.py', 'w') as file:
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


def rename_logs(scheduler, time):
    os.rename('request_log.csv', f'{time}_{scheduler}_request_log.csv')
    os.rename('LoudController.log', f'{time}_{scheduler}_LoudController.log')


def main():
    empty_logs()

    scheduler = 'stress'
    
    print(f"Running experiment with {scheduler} scheduler")
    set_scheduler(scheduler)


    controller = start_controller()

    # Wait for the controller to start and the board to cool down
    time.sleep(20)

    import Request_Stream as rs

     # Get the start time to rename the logs later
    start_time = time.strftime("%Y-%m-%d_%H:%M:%S")

    data_collection = start_data_collection(scheduler)

    controller.wait()
    data_collection.wait()

    rs.start(30)

    stop_data_collection()
    data_retrieval = retrieve_data()

    data_retrieval.wait()
    rename_logs(scheduler, start_time)
    
    stop_controller()
    empty_logs()
        
if __name__ == '__main__':
    main()



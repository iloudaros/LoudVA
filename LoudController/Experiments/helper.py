import os
import time
import subprocess

schedulers = ['loud', 'random', 'round_robin', 'kind_round_robin', 'stress', 'transparent', 'interval', 'fixed_batch']

# Functions to change the scheduler settings
def set_scheduler(scheduler):
    with open('LoudController/Settings.py', 'r') as file:
        data = file.readlines()

    for i, line in enumerate(data):
        if line.startswith('scheduler ='):
            print(f"Changing scheduler to {scheduler}")
            data[i] = f"scheduler = '{scheduler}' # Options: {schedulers}\n"

    with open('LoudController/Settings.py', 'w') as file:
        file.writelines(data)

def set_fixed_batch_size(batch_size):
    with open('LoudController/Settings.py', 'r') as file:
        data = file.readlines()

    for i, line in enumerate(data):
        if line.startswith('fixed_batch_size'):
            print(f"Changing fixed batch size to {batch_size}")
            data[i] = f"fixed_batch_size = {batch_size} # Used for the fixed batch size scheduler\n"

    with open('LoudController/Settings.py', 'w') as file:
        file.writelines(data)

def set_batching_interval(interval):
    with open('LoudController/Settings.py', 'r') as file:
        data = file.readlines()

    for i, line in enumerate(data):
        if line.startswith('batching_interval'):
            print(f"Changing batching interval to {interval}")
            data[i] = f"batching_interval = {interval} # Used for the fixed interval scheduler\n"

    with open('LoudController/Settings.py', 'w') as file:
        file.writelines(data)

def enable_prediction():
    with open('LoudController/Settings.py', 'r') as file:
        data = file.readlines()

    for i, line in enumerate(data):
        if line.startswith('use_prediction'):
            print(f"Enabling prediction")
            data[i] = f"use_prediction = True\n"

    with open('LoudController/Settings.py', 'w') as file:
        file.writelines(data)

def disable_prediction():
    with open('LoudController/Settings.py', 'r') as file:
        data = file.readlines()

    for i, line in enumerate(data):
        if line.startswith('use_prediction'):
            print(f"Disabling prediction")
            data[i] = f"use_prediction = False\n"

    with open('LoudController/Settings.py', 'w') as file:
        file.writelines(data)





# Functions to start and stop the controller 
def start_controller():
    controller = subprocess.Popen(['make', 'start_LoudController'])
    controller.wait()
    return controller

def stop_controller():
    controller = subprocess.Popen(['pkill', 'screen'])
    controller.wait()
    return controller





# Functions to start and stop data collection
def start_data_collection(scheduler, id):
    # Set tegrastats_log_name to [date]_[scheduler]_tegrastats
    tegrastats_log_name = f"{time.strftime('%Y-%m-%d_%H:%M:%S')}_id{id}_{scheduler}_tegrastats"

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
    data_collection.wait()
    return tegrastats_log_name

def stop_data_collection():
    data_collection = subprocess.Popen(['make', 'remote_stop_tegrastats'])
    data_collection.wait()
    return data_collection

def retrieve_data():
    data_collection = subprocess.Popen(['make', 'retrieve_tegrastats'])
    data_collection.wait()
    return data_collection


# Functions to simulate workload
def simulate_workload():
    workload = subprocess.Popen(['make', 'simulate_workload'])
    workload.wait()
    return workload





# Functions to handle logs
def rename_logs(scheduler, time):
    os.rename('request_log.csv', f'{time}_{scheduler}_request_log.csv')
    os.rename('LoudController.log', f'{time}_{scheduler}_LoudController.log')

def empty_logs():
    # Delete the logs if they exist
    if os.path.exists('request_log.csv'):
        os.remove('request_log.csv')
    if os.path.exists('LoudController.log'):
        os.remove('LoudController.log')

    delete_tegrastats = subprocess.Popen(['make', 'remote_delete_tegrastats'])
    delete_tegrastats.wait()




# Other functions
def default_power_mode():
    default = subprocess.Popen(['make', 'default_power_mode'])
    default.wait()
    return default

def generate_scenario():
    generate = subprocess.Popen(['make', 'generate_event_log'])
    generate.wait()
    return generate

def archive_scenario(name):
    # Archive /home/louduser/LoudVA/LoudController/LoudGenerator/event_log.csv to /home/louduser/LoudVA/LoudController/LoudGenerator/scenarios/[name].csv
    path = '/home/louduser/LoudVA/LoudController/LoudGenerator/scenarios'
    if not os.path.exists(path):
        os.makedirs(path)
    move = subprocess.Popen(['mv', '/home/louduser/LoudVA/LoudController/LoudGenerator/event_log.csv', f'{path}/{name}.csv'])
    move.wait()


# Main function to run the experiment
def experiment(scheduler, results_dir, id):
    if not results_dir:
        results_dir = scheduler
        
    # Create a directory for scheduler
    if not os.path.exists(f"experiment_results/{results_dir}"):
        os.makedirs(f"experiment_results/{results_dir}")

    # Clean slate
    empty_logs()
    default_power_mode()

    # Start Controller
    print(f"Running experiment with {scheduler} scheduler")
    set_scheduler(scheduler)
    start_controller()

    # Wait for the controller to start
    time.sleep(60)

    # Start data collection
    start_time = time.strftime('%Y-%m-%d_%H:%M:%S')
    tegrastats_log_name = start_data_collection(scheduler,id)
    

    # Simulate workload
    simulate_workload()
   

    # Stop data collection
    stop_data_collection()
    retrieve_data()
    

    # Move logs to the scheduler's directory
    rename_logs(results_dir, start_time)
    os.rename(f'{start_time}_{results_dir}_request_log.csv', 
                f'experiment_results/{results_dir}/{start_time}_id{id}_{results_dir}_request_log.csv')
    os.rename(f'{start_time}_{results_dir}_LoudController.log', 
                f'experiment_results/{results_dir}/{start_time}_id{id}_{results_dir}_LoudController.log')
    os.rename(f'/home/louduser/LoudVA/measurements/power/agx-xavier-00/home/iloudaros/{tegrastats_log_name}',
                f'experiment_results/{results_dir}/{tegrastats_log_name}')

    stop_controller()
    empty_logs()

    # Wait for the board to cool down
    time.sleep(60)



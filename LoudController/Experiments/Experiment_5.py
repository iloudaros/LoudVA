# This experiment evaluates the ⁠LoudCostPredictor's ability to generalize to new, unseen devices. 
# It iteratively trains the predictor by excluding one device's profiling data 
# and then gradually re-introducing it in 20% increments. 
# This process is repeated for each device type (⁠AGX, ⁠NX, ⁠Nano) 
# to analyze the prediction quality's impact on the ⁠LoudScheduler's performance.

import helper
import pandas as pd
import os
import numpy as np
import math
import time

DATA_PATH = 'LoudController/LoudPredictor/costs/agnostic/data.csv'
BACKUP_PATH = 'LoudController/LoudPredictor/costs/agnostic/data.csv.bak'

def setup_training_data(original_data, device_to_exclude, ratio):
    """
    Creates a temporary training dataset by excluding a device and then
    re-introducing a specific ratio of its data.
    """
    # Separate data for the unseen device and the rest
    unseen_df = original_data[original_data['Directory'] == device_to_exclude]
    seen_df = original_data[original_data['Directory'] != device_to_exclude]

    if ratio > 0 and not unseen_df.empty:
        sample_size = int(len(unseen_df) * ratio)
        unseen_sample = unseen_df.sample(n=sample_size, random_state=42)
        final_training_df = pd.concat([seen_df, unseen_sample])
    else:
        final_training_df = seen_df
    
    # Overwrite the data file used for training
    final_training_df.to_csv(DATA_PATH, index=False)
    print(f"Created training data excluding {device_to_exclude} with {ratio*100}% of its data.")

def main():
    """
    Main function to run Experiment 5.
    This experiment explores the LoudCostPredictor's performance when a device
    is left out of the training data and then gradually re-introduced.
    """
    devices_to_exclude = ['AGX', 'NX', 'Nano']
    ratios = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    num_scenarios = 3
    scenario_duration = 5 + 2 + 1 # 8 minutes
    
    estimated_time = math.ceil((len(devices_to_exclude) * len(ratios) * num_scenarios * scenario_duration) / 60 * 1.1)
    print(f"Estimated time: {estimated_time} hours. End time: {time.ctime(time.time() + estimated_time * 3600)}")
    if input("Proceed? (y/n)") != 'y':
        exit()

    # Backup the original data.csv file before starting
    if os.path.exists(DATA_PATH):
        os.rename(DATA_PATH, BACKUP_PATH)
    
    try:
        original_data = pd.read_csv(BACKUP_PATH)

        for device in devices_to_exclude:
            for ratio in ratios:
                print(f"--- Setting up for unseen device: {device} at {ratio*100}% inclusion ---")
                setup_training_data(original_data, device, ratio)
                
                for i in range(num_scenarios):
                    scenario_name = f"unseen_{device}_ratio{int(ratio*100)}_s{i}"
                    print(f"--- Running experiment: {scenario_name} ---")
                    
                    helper.generate_scenario()
                    helper.enable_prediction()  # Ensure LoudScheduler uses prediction
                    helper.experiment('loud', f'unseen_{device}_ratio{int(ratio*100)}', scenario_name)
                    helper.archive_scenario(scenario_name)
    finally:
        # Restore the original data file
        if os.path.exists(BACKUP_PATH):
            os.rename(BACKUP_PATH, DATA_PATH)
        print("Experiment 5 finished. Original data file restored.")

if __name__ == '__main__':
    main()

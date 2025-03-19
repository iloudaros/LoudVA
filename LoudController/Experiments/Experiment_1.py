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
# 8. Repeat steps 1-8 for the 
#                             i.TransparentScheduler (Race to idle), 
#                            ii.IntervalScheduler (0.2, 0.5, 1) and 
#                           iii.FixedBatchScheduler (8, 16, 32)
#
# 9. We will run 7 different scenarios generated by the LoudGenerator.py script.
# 10. We also have to see the difference between prediction and profiling.

import helper
import math
import time

scenarios = 7
scenario_duration = 5 + 2 + 1 #mins
scheduler_configs_to_be_tested = 1 + 3 + 3 + 2


estimated_time = math.ceil((scenarios*scenario_duration*scheduler_configs_to_be_tested)/60*1.1)
print(f"Estimated time: {estimated_time} hours. End time: {time.ctime(time.time() + estimated_time*3600)}")
print("Proceed? (y/n)")
if input() != 'y':
    exit()




def main():
    for scenario in range(scenarios):

        # Generate scenario
        print(f"Generating scenario {scenario}")
        scenario_generation = helper.generate_scenario()
        scenario_generation.wait()

        # TransparentScheduler
        print(f"Running scenario {scenario} on TransparentScheduler")
        helper.experiment('transparent', 'transparent', scenario)

        # IntervalScheduler
        for interval in [0.2, 0.5, 1]:
            print(f"Running scenario {scenario} on IntervalScheduler with interval {interval}")
            helper.set_batching_interval(interval)
            helper.experiment(f'interval', f'interval_{interval}', scenario)

        # FixedBatchScheduler
        for batch_size in [8, 16, 32]:
            print(f"Running scenario {scenario} on FixedBatchScheduler with batch size {batch_size}")
            helper.set_fixed_batch_size(batch_size)
            helper.experiment(f'fixed_batch', f'fixed_batch_{batch_size}', scenario)

        # LoudScheduler with prediction
        print(f"Running scenario {scenario} on LoudScheduler with prediction")
        helper.enable_prediction()
        helper.experiment('loud', 'loud_pred', scenario)

        # LoudScheduler with profiling
        print(f"Running scenario {scenario} on LoudScheduler with profiling")
        helper.disable_prediction()
        helper.experiment('loud', 'loud_prof', scenario)

        helper.archive_scenario(scenario)
        
if __name__ == '__main__':
    main()

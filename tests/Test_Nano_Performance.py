#!/usr/bin/python3 -u
### Performance Test ###
# 
# We use this script to test the effect of the power mode (or GPU clk speed) of the Jetson on the performance of the triton server, with the dynamic batching feature enabled.
# - We will use the `perf_analyzer` tool to measure the throughput of the server with different power modes.
# - We will use the `nvpmodel` tool to change the power mode of the Jetson.
# 
# (To be run on the Jetsons via the performance_profiling ansible playbook.)

import os
import ihelper as i
maximum_concurrency = 3

#### Power modes
# The supported power modes for the Jetson Nano
power_modes = [0,1] 

# Measure the performance of the system for each power mode using the perf_analyzer tool
for mode in power_modes:

    # Set power mode
    print(f"---Setting power mode to {mode}---")
    os.system(f"sudo nvpmodel -m {mode}")

    # For each concurrency level, run the performance test
    for conc in range(1, maximum_concurrency+1):
        print(f"---Setting concurrency to {conc}---")
        i.modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_FLOOR', '=', conc)
        i.modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_LIMIT', '=', conc)

        # Run the performance test
        print("Running performance test")
        os.system('cd /home/iloudaros/LoudVA && make measure_performance_and_power')

        # Rename the results according to the power mode
        print("Renaming the results")
        os.system(f'mv /home/iloudaros/LoudVA/measurements/performance/performance_measurements.csv /home/iloudaros/LoudVA/measurements/performance/modes/performance_measurements_mode_{mode}_conc_{conc}.csv')
        os.system(f'mv /home/iloudaros/LoudVA/measurements/power/power_measurement_stats /home/iloudaros/LoudVA/measurements/power/modes/power_measurement_stats_mode_{mode}_conc_{conc}.csv')
    
    # combine the results of the different concurrencies
    print("Combining the results")
    os.system(f'cd /home/iloudaros/LoudVA/measurements/performance/modes && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh performance_measurements_mode_{mode}')
    os.system(f'cd /home/iloudaros/LoudVA/measurements/power/modes && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh power_measurement_stats_mode_{mode}')

### 
# Return to the default power mode
print(f"---Setting power mode to 0---")
os.system(f"sudo nvpmodel -m 0")
###

#### GPU Clock Speeds
# These are the supported frequencies for the GPU on the Jetson Nano
#[76800000, 153600000, 230400000, 307200000, 384000000, 460800000, 537600000, 614400000, 691200000, 768000000, 844800000, 921600000] 
gpu_freqs = [ 153600000, 230400000, 307200000, 384000000, 460800000, 537600000, 614400000, 691200000, 768000000, 844800000, 921600000] 


# Measure the performance of the system for each frequency using the perf_analyzer tool
for freq in gpu_freqs:

    # Modify the makefile to change the gpu frequency
    print(f"---Setting GPU frequency to {freq}---")
    os.system('sudo jetson_clocks --restore /home/iloudaros/LoudVA/power_management/l4t_dfs.conf')
    os.system(f"sudo nvpmodel -m 0")
    os.system('sleep 5')
    i.modify_gpu_freq(freq)

    # For each concurrency level, run the performance test
    for conc in range(1, maximum_concurrency+1):
        print(f"---Setting concurrency to {conc}---")
        i.modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_FLOOR', '=', conc)
        i.modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_LIMIT', '=', conc)
        

       # Run the performance test
        print("Running performance test")
        os.system('cd /home/iloudaros/LoudVA && make measure_performance_and_power')

        # Rename the results according to the freq
        print("Renaming the results")
        os.system(f'mv /home/iloudaros/LoudVA/measurements/performance/performance_measurements.csv /home/iloudaros/LoudVA/measurements/performance/freqs/performance_measurements_freq_{freq}_conc_{conc}.csv')
        os.system(f'mv /home/iloudaros/LoudVA/measurements/power/power_measurement_stats /home/iloudaros/LoudVA/measurements/power/freqs/power_measurement_stats_freq_{freq}_conc_{conc}.csv')
    
    # combine the results of the different concurrencies
    print("Combining the results")
    os.system(f'cd /home/iloudaros/LoudVA/measurements/performance/freqs && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh performance_measurements_freq_{freq}')
    os.system(f'cd /home/iloudaros/LoudVA/measurements/power/freqs && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh power_measurement_stats_freq_{freq}')


# Return the Makefile GPU frequency and MEASUREMENT_INTERVAl to the default value, reenable the 3d-scaling
print(f"Returning to the default values")
i.modify_variable('/home/iloudaros/LoudVA/makefile', 'MEASUREMENT_INTERVAL', '=', 5000)
i.modify_variable('/home/iloudaros/LoudVA/makefile', 'GPU_MIN_FREQ', '=', 76800000)
i.modify_variable('/home/iloudaros/LoudVA/makefile', 'GPU_MAX_FREQ', '=', 921600000)
os.system('sudo jetson_clocks --restore /home/iloudaros/LoudVA/power_management/l4t_dfs.conf')
os.system('sudo nvpmodel -m 0')

### Performance Test ###
# 
# We use this notebook to test the effect of the power mode (or GPU clk speed) of the Jetson on the performance of the triton server, with the dynamic batching feature enabled.
# - We will use the `perf_analyzer` tool to measure the throughput of the server with different power modes.
# - We will use the `nvpmodel` tool to change the power mode of the Jetson.
# 
# (To be run on the Jetsons via the performance_profiling ansible playbook.)

import os
import ihelper as i

#### Power modes
power_modes = [0] #[0,1]

for mode in power_modes:
    # Set power mode
    print(f"---Setting power mode to {mode}---")
    os.system(f"sudo nvpmodel -m {mode}")

    # Modify the makefile to change the MEASUREMENT_INTERVAL 
    if mode == 1:
        i.modify_variable('/home/iloudaros/LoudVA/makefile', 'MEASUREMENT_INTERVAL', '=', 10000)
    else:
        i.modify_variable('/home/iloudaros/LoudVA/makefile', 'MEASUREMENT_INTERVAL', '=', 5000)

    # Run the performance test
    print("Running performance test")
    os.system('cd /home/iloudaros/LoudVA && make measure_performance_csv')

    # Rename the results according to the power mode
    print("Renaming the results")
    os.system('mv /home/iloudaros/LoudVA/measurements/performance_measurements.csv /home/iloudaros/LoudVA/measurements/performance_measurements_mode_' + str(mode) + '.csv')

### 
# Return to the default power mode
print(f"---Setting power mode to 0---")
os.system(f"sudo nvpmodel -m 0")
###

#### GPU Clock Speeds
# These are the supported frequencies for the GPU on the Jetson Nano
gpu_freqs = [307200000, 844800000, 921600000] #[76800000, 153600000, 230400000, 307200000, 384000000, 460800000, 537600000, 614400000, 691200000, 768000000, 844800000, 921600000] 


# Measure the performance of the system for each frequency using the perf_analyzer tool
for freq in gpu_freqs:

    # Modify the makefile to change the gpu frequency
    print(f"---Setting GPU frequency to {freq}---")
    os.system('sleep 5')
    i.modify_gpu_freq(freq)

    # Modify the makefile to change the MEASUREMENT_INTERVAL (not needed because we changed the mode to count_windows for more info read the makefile)
    # new_interval = (921600000//freq)*5000+1000
    # print(f"Setting MEASUREMENT_INTERVAL to {new_interval}")
    # i.modify_variable('/home/iloudaros/LoudVA/makefile', 'MEASUREMENT_INTERVAL', '=', new_interval)

    # Run the performance measurement from the makefile
    print("Running performance test")
    os.system('cd /home/iloudaros/LoudVA && make measure_performance_csv')

    # Rename the results according to the frequency
    print("Renaming the results")
    os.system('mv /home/iloudaros/LoudVA/measurements/performance_measurements.csv /home/iloudaros/LoudVA/measurements/performance_measurements_freq_' + str(freq) + '.csv')




# Return the Makefile GPU frequency and MEASUREMENT_INTERVAl to the default value, reenable the 3d-scaling
print(f"Returning to the default values")
i.modify_variable('/home/iloudaros/LoudVA/makefile', 'MEASUREMENT_INTERVAL', '=', 5000)
i.modify_variable('/home/iloudaros/LoudVA/makefile', 'GPU_MIN_FREQ', '=', 76800000)
i.modify_variable('/home/iloudaros/LoudVA/makefile', 'GPU_MAX_FREQ', '=', 921600000)
os.system('sudo jetson_clocks --restore /home/iloudaros/LoudVA/power_management/l4t_dfs.conf')
os.system('sudo nvpmodel -m 0')

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
power_modes = [0, 1]

for mode in power_modes:
    # Set power mode
    print(f"Setting power mode to {mode}")
    os.system(f"sudo nvpmodel -m {mode}")

    # Run the performance test
    print("Running performance test")
    os.system('cd ~/LoudVA && make measure_performance_csv')

    # Rename the results according to the power mode
    print("Renaming the results")
    os.system('mv ~/LoudVA/measurements/performance_measurements.csv ~/LoudVA/measurements/performance_measurements_mode_' + str(mode) + '.csv')


#### GPU Clock Speeds
# These are the supported frequencies for the GPU on the Jetson Nano
gpu_freqs = [844800000, 921600000] #[76800000, 153600000, 230400000, 307200000, 384000000, 460800000, 537600000, 614400000, 691200000, 768000000,


# Measure the performance of the system for each frequency using the perf_analyzer tool
for freq in gpu_freqs:
    # Modify the makefile to change the gpu frequency
    print(f"Setting GPU frequency to {freq}")
    i.modify_gpu_freq('/home/iloudaros/LoudVA/makefile', freq)

    # Run the performance measurement from the makefile
    print("Running performance test")
    os.system('cd ~/LoudVA && make measure_performance_csv')

    # Rename the results according to the frequency
    print("Renaming the results")
    os.system('mv ~/LoudVA/measurements/performance_measurements.csv ~/LoudVA/measurements/performance_measurements_freq_' + str(freq) + '.csv')




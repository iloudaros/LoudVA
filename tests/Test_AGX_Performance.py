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
i.return_to_defaults("agx")

minimum_concurrency = 1
maximum_concurrency = 64
check_modes = 0
check_freqs = 1

#### Power modes
if (check_modes==1):
    # The supported power modes for the Jetson AGX Xavier
    power_modes = [0, 1, 2, 3, 4, 5, 6, 7] 

    # Measure the performance of the system for each power mode using the perf_analyzer tool
    for mode in power_modes:

        # Set power mode
        print(f"---Setting power mode to {mode}---")
        os.system(f"sudo nvpmodel -m {mode}")

        # For each concurrency level, run the performance test
        for conc in range(minimum_concurrency, maximum_concurrency+1):
            counter=0

            while True:
                counter+=1
                try:
                    print(f"---Setting concurrency to {conc}---")
                    i.modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_FLOOR', '=', conc)
                    i.modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_LIMIT', '=', conc)

                    # Run the performance test
                    print("Running performance test")
                    os.system('cd /home/iloudaros/LoudVA && make measure_performance_and_power')

                    # Open the log file and check if there are any errors 
                    with open('/home/iloudaros/LoudVA/measurements/log', 'r') as file:
                        lines = file.readlines()
                        for line in lines[-5:]:
                            if "Error" in line or "Failed" in line:
                                print('Error in the log file, exception raised')
                                raise Exception("Error in the log file")

                    # Rename the results according to the power mode
                    print("Renaming the results")
                    os.system(f'mv /home/iloudaros/LoudVA/measurements/performance/performance_measurements.csv /home/iloudaros/LoudVA/measurements/performance/modes/performance_measurements_mode_{mode}_conc_{conc}.csv')
                    os.system(f'mv /home/iloudaros/LoudVA/measurements/power/power_measurement_stats /home/iloudaros/LoudVA/measurements/power/modes/power_measurement_stats_mode_{mode}_conc_{conc}.csv')

                    # Empty the log of tegra_stats
                    os.system('rm /home/iloudaros/LoudVA/measurements/power/tegra_log')
                except Exception as e:                    
                    print(f"🔄 An error occured:{e} Retrying...")
                    # stop tegrastats and empty the tegra_log
                    os.system('sudo pkill tegrastats')
                    os.system('rm /home/iloudaros/LoudVA/measurements/power/tegra_log')

                    if counter>5:
                        print("❌ Too many retries, skipping this frequency")
                        break
                else:
                    break
                finally:   
                    # close the log file 
                    file.close()

        
        # combine the results of the different concurrencies
        print("Combining the results")
        os.system(f'cd /home/iloudaros/LoudVA/measurements/performance/modes && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh performance_measurements_mode_{mode}')
        os.system(f'cd /home/iloudaros/LoudVA/measurements/power/modes && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh power_measurement_stats_mode_{mode}')

    ### 
    # Return to the default power mode
    i.return_to_defaults("agx")
    ###

#### GPU Clock Speeds
if(check_freqs==1):
    # These are the supported frequencies for the GPU on the Jetson AGX Xavier
    #[114750000, 204000000, 306000000, 408000000, 510000000, 599250000, 701250000, 752250000, 803250000, 854250000, 905250000, 956250000, 1007250000, 1058250000, 1109250000] 
    gpu_freqs = [ 114750000, 204000000, 306000000, 408000000, 510000000, 599250000, 701250000, 752250000, 803250000, 854250000, 905250000, 956250000, 1007250000, 1058250000, 1109250000] 


    # Measure the performance of the system for each frequency using the perf_analyzer tool
    for freq in gpu_freqs:

        # Modify the makefile to change the gpu frequency
        print(f"---Setting GPU frequency to {freq}---")
        i.return_to_defaults("agx")
        os.system('sleep 5')
        i.modify_gpu_freq(freq)

        # For each concurrency level, run the performance test
        for conc in range(minimum_concurrency, maximum_concurrency+1):
            counter=0
            while True:
                counter+=1
                try:
                    print(f"---Setting concurrency to {conc}---")
                    i.modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_FLOOR', '=', conc)
                    i.modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_LIMIT', '=', conc)

                    # Run the performance test
                    print("Running performance test")
                    os.system('cd /home/iloudaros/LoudVA && make measure_performance_and_power')

                    # Open the log file and check if there are any errors 
                    with open('/home/iloudaros/LoudVA/measurements/log', 'r') as file:
                        lines = file.readlines()
                        for line in lines[-5:]:
                            if "Error" in line or "Failed" in line:
                                print('Error in the log file, exception raised')
                                raise Exception("Error in the log file")

                    # Rename the results according to the freq
                    print("Renaming the results")
                    os.system(f'mv /home/iloudaros/LoudVA/measurements/performance/performance_measurements.csv /home/iloudaros/LoudVA/measurements/performance/freqs/performance_measurements_freq_{freq}_conc_{conc}.csv')
                    os.system(f'mv /home/iloudaros/LoudVA/measurements/power/power_measurement_stats /home/iloudaros/LoudVA/measurements/power/freqs/power_measurement_stats_freq_{freq}_conc_{conc}.csv')

                    # Empty the log of tegra_stats
                    os.system('rm /home/iloudaros/LoudVA/measurements/power/tegra_log')
                except Exception as e:                    
                    print(f"🔄 An error occured:{e} Retrying...")
                    # stop tegrastats and empty the tegra_log
                    os.system('sudo pkill tegrastats')
                    os.system('rm /home/iloudaros/LoudVA/measurements/power/tegra_log')

                    if counter>5:
                        print("❌ Too many retries, skipping this frequency")
                        break
                else:
                    break
                finally:   
                    # close the log file 
                    file.close()

        
        # combine the results of the different concurrencies
        print("Combining the results")
        os.system(f'cd /home/iloudaros/LoudVA/measurements/performance/freqs && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh performance_measurements_freq_{freq}')
        os.system(f'cd /home/iloudaros/LoudVA/measurements/power/freqs && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh power_measurement_stats_freq_{freq}')


# Return the Makefile GPU frequency and MEASUREMENT_INTERVAl to the default value, reenable the 3d-scaling
i.return_to_defaults("agx")

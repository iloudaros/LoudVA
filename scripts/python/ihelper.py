import os
import csv

def modify_gpu_freq(freq):
  """
  Modifies the GPU frequency to the specified value.

  Args:
    freq: The new GPU frequency in Hz.
  """

  # Get the model name 
  model = os.popen("cd /home/iloudaros/LoudVA && make model").read().strip()

  # Define the location of the GPU frequency files for each model
  if model == "NVIDIA Jetson Nano Developer Kit":
    path = '/sys/devices/57000000.gpu/devfreq/57000000.gpu'
  elif model == "NVIDIA Jetson Xavier NX Developer Kit":
    path = '/sys/devices/17000000.gv11b/devfreq/17000000.gv11b'
  elif model == "Jetson-AGX":
    path = '/sys/devices/17000000.gv11b/devfreq/17000000.gv11b'
  else:
    print('Model not supported')

  print(f"Model: {model}")

  # Read available frequencies
  with open(f'{path}/available_frequencies', 'r') as file:
    available_freqs = [int(f) for f in file.read().split()]

  # Check if freq is within valid range
  if freq not in available_freqs:
    print(f"Error: Frequency {freq}Hz not supported. Valid options: {available_freqs}")
    return

  # Attempt to write the frequency to min and max files (with sudo)
  try:
    with open(f'{path}/min_freq', 'w') as min_file:
      min_file.write(str(freq))
    with open(f'{path}/max_freq', 'w') as max_file:
      max_file.write(str(freq))
    print(f"GPU frequency set to {freq}Hz.")
  except OSError as e:
    print(f"Error setting GPU frequency: {e}")



def modify_max_batch_size(config_file, size):
  """
  Modifies the max_batch_size value in model config file.

  Args:
    config_file: The path to the config file.
    size: The new max batch size.
  """
# Open the file in read mode
  with open(config_file, "r") as file:
    lines = file.readlines()

  # Modify line with GPU_FREQ declaration
  modified_lines = []
  for line in lines:
    if line.startswith("max_batch_size: "):
      # Extract the beginning part of the line
      start_of_line = line.split(":")[0]
      # Combine with freq to set the value
      modified_line = start_of_line + ': '  + str(size) + '\n'
    else:
      modified_line = line

    modified_lines.append(modified_line)

  # Open the file again in write mode (overwrites existing content)
  with open(config_file, "w") as file:
    file.writelines(modified_lines)



def modify_variable(config_file, variable, seperator, value):
  """
  Modifies the variable value in config file.

  Args:
    config_file: The path to the config file.
    variable: The name of the variable to modify.
    seperator: The seperator between the variable and value.
    value: The new value.
  """
# Open the file in read mode
  with open(config_file, "r") as file:
    lines = file.readlines()

  # Modify line with GPU_FREQ declaration
  modified_lines = []
  for line in lines:
    if line.startswith(f"{variable} {seperator}"):
      # Extract the beginning part of the line
      start_of_line = line.split(seperator)[0]
      # Combine with freq to set the value
      modified_line = start_of_line + seperator+ ' ' + str(value) + '\n'
    else:
      modified_line = line

    modified_lines.append(modified_line)

  # Open the file again in write mode (overwrites existing content)
  with open(config_file, "w") as file:
    file.writelines(modified_lines)



def read_variable(file, variable, seperator):
  """
  Reads the value of a variable in a file.

  Args:
    file: The path to the config file.
    variable: The name of the variable to read.
  """
  # Open the file in read mode
  with open(file, "r") as file:
    lines = file.readlines()

  # Find the line with the variable
  for line in lines:
    if line.startswith(f"{variable} "):
      value = line.split(seperator)[1]
      # Remove any leading or trailing whitespace and also remove any comments
      return value.split("#")[0].strip()
    
  return None



def return_to_defaults(model):
  
  print(f"Returning to the default values")

  # For the Jetson Nano
  if model == "nano":
    os.system('sudo jetson_clocks --restore /home/iloudaros/LoudVA/power_management/Nano/l4t_dfs.conf')
    os.system('sudo nvpmodel -m 0')

  # For the Jetson Xavier NX
  elif model == "nx":
    os.system('sudo jetson_clocks --restore /home/iloudaros/LoudVA/power_management/NX/jetsonclocks_conf.txt')
    os.system('sudo nvpmodel -m 8')

  # For the Jetson Xavier AGX
  elif model == "agx":
    os.system('sudo jetson_clocks --restore /home/iloudaros/LoudVA/power_management/AGX/jetsonclocks_conf.txt')
    os.system('sudo nvpmodel -m 0')

  else:
    print(f"Model {model} not supported./n Supported models: nano, nx, agx")



def choose_threshold(counter):
  """
  Sets the stability threshold based on the number of tries.

  Args:
    counter: The number of tries.
  """
  if counter in range(1, 21):     threshold = 10 ; distrust = 0
  elif counter in range(21, 31):  threshold = 12 ; distrust = 1
  elif counter in range(31, 41):  threshold = 15 ; distrust = 2
  elif counter in range(41, 51):  threshold = 17 ; distrust = 3
  else:                           threshold = 20 ; distrust = 4

  return threshold, distrust


def calculate_energy(power_file, performance_file, energy_file):
    """
    Calculates the energy consumption based on the power and performance files.

    Args:
        power_file: The path to the power file.
        performance_file: The path to the performance file.
        energy_file: The path to the energy file.
    """
    # Print a message with the names of the files
    print(f"Calculating energy consumption based on {power_file} and {performance_file}")

    # Open the files
    with open(power_file, 'r') as power, open(performance_file, 'r') as performance, open(energy_file, 'w') as energy:
        # Read the power_file and strip the values
        power_lines = power.readlines()
        power = [x.split(':')[1].strip() for x in power_lines]
        power = [float(x)*10**-3 for x in power]

        # Read the performance_file and strip the values
        performance_lines = csv.reader(performance, delimiter=',')
        performance = list(performance_lines)  
    
        latency = [int(x[4])+int(x[5])+int(x[6])+int(x[7]) for x in performance[1:]]
        latency = [int(x)*10**-6 for x in latency]
        throughput = [float(x[1]) for x in performance[1:]]

        # Write the header
        energy.write('Concurrency, Mean Power (W), Avg Latency (s), Throughput (Inference/sec), Energy (J)\n')

        # Calculate the energy
        for i in range(0, len(power_lines)):
            energy.write(f'{i+1},{power[i]},{latency[i]},{throughput[i]},{float(power[i])*float(latency[i])}\n')
        
        print(f"Energy consumption calculated and saved to {energy_file}")



def calculate_energy_directory(devices = ['agx-xavier-00', 'LoudJetson0', 'xavier-nx-00'],
                               measurement_code = 'Representative',
                               checkModes = False,
                               checkFreqs = True,
                               ):
    """
    Calculates the energy consumption based on the power and performance files.

    """

    for device in devices:
            
        # Specify the directory
        directory = f'/home/louduser/LoudVA/measurements/archive/{measurement_code}/{device}/measurements'

        if checkFreqs:

            # Create the energy directory if it does not exist
            if not os.path.exists(f'{directory}/energy/freqs'):
                os.makedirs(f'{directory}/energy/freqs')

            # Get the list of files and directories
            contents = os.listdir(f'{directory}/performance/freqs')

            # Print each item
            for performance_file in contents:
                if performance_file.endswith('.csv'):
                    freq = performance_file.split('_')[-1].split('.')[0]
                    power_file = f'{directory}/power/freqs/power_measurement_stats_freq_{freq}.csv'
                    energy_file = f'{directory}/energy/freqs/energy_calculated_freq_{freq}.csv'
                    performance_file = f'{directory}/performance/freqs/{performance_file}'
                    calculate_energy(power_file, performance_file, energy_file)

        if checkModes:

            # Create the energy directory if it does not exist
            if not os.path.exists(f'{directory}/energy/modes'):
                os.makedirs(f'{directory}/energy/modes')
                
            # Get the list of files and directories
            contents = os.listdir(f'{directory}/performance/modes')

            # Print each item
            for performance_file in contents:
                if performance_file.endswith('.csv'):
                    mode = performance_file.split('_')[-1].split('.')[0]
                    power_file = f'{directory}/power/modes/power_measurement_stats_mode_{mode}.csv'
                    energy_file = f'{directory}/energy/modes/energy_calculated_mode_{mode}.csv'
                    performance_file = f'{directory}/performance/modes/{performance_file}'
                    calculate_energy(power_file, performance_file, energy_file)



def profiling(check_modes, check_freqs, minimum_concurrency, maximum_concurrency, timeout_enabled, retries_allowed, power_modes, gpu_freqs, board):

  # This is a dictionary where we will store frequencies and modes that needed retries and the number of retries
  retried_modes = {}
  retried_freqs = {}

  #### Power modes
  if (check_modes):
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
                  threshold, distrust = choose_threshold(counter)

                  print(f"Stability Percentage is set to {threshold}%")
                  modify_variable('/home/iloudaros/LoudVA/makefile', 'STABILITY_THRESHOLD', '=', threshold)
                     
                  # Run the performance test
                  try:
                      print(f"---Testing Mode:{mode} and Concurrency:{conc} ---")
                      modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_FLOOR', '=', conc)
                      modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_LIMIT', '=', conc)

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

                      # Add conc and mode to the retried dictionary
                      key = (mode, conc)
                      if key in retried_modes:
                          retried_modes[key][0] += 1
                          retried_modes[key][1] = distrust
                      else:
                          retried_modes[key] = [1, distrust]
                  
                      if counter>=retries_allowed and timeout_enabled:
                          print("❌ Too many retries, skipping...")
                          retried_modes[key][1] = 20
                          break
                  else: 
                      break
                  finally:   
                      # close the log file 
                      file.close()


          # combine the results of the different concurrencies
          print("Combining the results")
          os.system(f'cd /home/iloudaros/LoudVA/measurements/performance/modes && bash /home/iloudaros/LoudVA/scripts/shell/combine_measurements.sh performance_measurements_mode_{mode}')
          os.system(f'cd /home/iloudaros/LoudVA/measurements/power/modes && bash /home/iloudaros/LoudVA/scripts/shell/combine_measurements.sh power_measurement_stats_mode_{mode}')

          # calculate the energy consumption
          print("Calculating the energy consumption")
          calculate_energy(f'/home/iloudaros/LoudVA/measurements/power/modes/power_measurement_stats_mode_{mode}.csv', f'/home/iloudaros/LoudVA/measurements/performance/modes/performance_measurements_mode_{mode}.csv', f'/home/iloudaros/LoudVA/measurements/energy/modes/energy_measurement_stats_mode_{mode}.csv')



      ### 
      # Return to the default power mode
      return_to_defaults(board)
      ###



  #### GPU Clock Speeds
  if (check_freqs):
      
      # Measure the performance of the system for each frequency using the perf_analyzer tool
      for freq in gpu_freqs:

          # Modify the makefile to change the gpu frequency
          print(f"---Setting GPU frequency to {freq}---")
          return_to_defaults(board)
          os.system('sleep 5')
          modify_gpu_freq(freq)

          # For each concurrency level, run the performance test
          for conc in range(minimum_concurrency, maximum_concurrency+1):
              counter=0

              while True:
                  counter+=1
                  threshold, distrust = choose_threshold(counter)

                  print(f"Stability Percentage is set to {threshold}%")
                  modify_variable('/home/iloudaros/LoudVA/makefile', 'STABILITY_THRESHOLD', '=', threshold)

                  # Run the performance test
                  try:
                      print(f"---Testing Freq:{freq} and Concurrency:{conc} ---")
                      modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_FLOOR', '=', conc)
                      modify_variable('/home/iloudaros/LoudVA/makefile', 'CONCURRENCY_LIMIT', '=', conc)
                      
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
                      print(f"🔄 An error occured:{e.__str__} Retrying...")
                      
                      # stop tegrastats and empty the tegra_log
                      os.system('sudo pkill tegrastats')
                      os.system('rm /home/iloudaros/LoudVA/measurements/power/tegra_log')
                      
                      # Add conc and freq to the retried dictionary
                      key = (freq, conc)
                      if key in retried_freqs:
                          retried_freqs[key][0] += 1
                          retried_freqs[key][1] = distrust
                      else:
                          retried_freqs[key] = [1, distrust]
                  
                      if counter>=retries_allowed and timeout_enabled:
                          print("❌ Too many retries, skipping...")
                          retried_modes[key][1] = 20
                          break
                  else:
                      break
                  finally:   
                      # close the log file 
                      file.close()


          # combine the results of the different concurrencies
          print("Combining the results")
          os.system(f'cd /home/iloudaros/LoudVA/measurements/performance/freqs && bash /home/iloudaros/LoudVA/scripts/shell/combine_measurements.sh performance_measurements_freq_{freq}')
          os.system(f'cd /home/iloudaros/LoudVA/measurements/power/freqs && bash /home/iloudaros/LoudVA/scripts/shell/combine_measurements.sh power_measurement_stats_freq_{freq}')

          # calculate the energy consumption
          print("Calculating the energy consumption")
          calculate_energy(f'/home/iloudaros/LoudVA/measurements/power/freqs/power_measurement_stats_freq_{freq}.csv', f'/home/iloudaros/LoudVA/measurements/performance/freqs/performance_measurements_freq_{freq}.csv', f'/home/iloudaros/LoudVA/measurements/energy/freqs/energy_measurement_stats_freq_{freq}.csv')

  return_to_defaults(board)

  # Export the retried modes and frequencies to a file if they are not empty
  if retried_modes:
      with open('/home/iloudaros/LoudVA/measurements/retried_modes.txt', 'w') as file:
          for key in sorted(retried_modes.keys()):
                  file.write(str(key) + ' ' + str(retried_modes[key][0]) + ' ' + '!'*retried_modes[key][1] + '\n')

  if retried_freqs:
      with open('/home/iloudaros/LoudVA/measurements/retried_freqs.txt', 'w') as file:
          for key in sorted(retried_freqs.keys()):
                  file.write(str(key) + ' ' + str(retried_freqs[key][0]) + ' ' + '!'*retried_freqs[key][1] + '\n')
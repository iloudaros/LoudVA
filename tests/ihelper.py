import os

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


def calculate_energy(power_file, performance_file):
  pass



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
          os.system(f'cd /home/iloudaros/LoudVA/measurements/performance/modes && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh performance_measurements_mode_{mode}')
          os.system(f'cd /home/iloudaros/LoudVA/measurements/power/modes && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh power_measurement_stats_mode_{mode}')



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
          os.system(f'cd /home/iloudaros/LoudVA/measurements/performance/freqs && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh performance_measurements_freq_{freq}')
          os.system(f'cd /home/iloudaros/LoudVA/measurements/power/freqs && bash /home/iloudaros/LoudVA/scripts/combine_measurements.sh power_measurement_stats_freq_{freq}')

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
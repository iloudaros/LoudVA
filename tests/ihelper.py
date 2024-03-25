import os

# def modify_gpu_freq(filename, freq):
#   """
#   Modifies the GPU_FREQ value in a file to freq.

#   Args:
#     filename: The path to the makefile.
#     freq: The frequency to set the GPU to.
#   """
#   # Open the file in read mode
#   with open(filename, "r") as file:
#     lines = file.readlines()

#   # Modify line with GPU_FREQ declaration
#   modified_lines = []
#   for line in lines:
#     if line.startswith("GPU_MIN_FREQ = ") or line.startswith("GPU_MAX_FREQ = "):
#       # Extract the beginning part of the line
#       start_of_line = line.split("=")[0]
#       # Combine with freq to set the value
#       modified_line = start_of_line + '= '  + str(freq) + '\n'
#     else:
#       modified_line = line

#     modified_lines.append(modified_line)

#   # Open the file again in write mode (overwrites existing content)
#   with open(filename, "w") as file:
#     file.writelines(modified_lines)

#   # Change the GPU frequency using the makefile
#   os.system('cd /home/iloudaros/LoudVA && make change_gpu_freq')

def modify_gpu_freq(freq):

  # Read available frequencies
  with open('/sys/devices/57000000.gpu/devfreq/57000000.gpu/available_frequencies', 'r') as file:
    available_freqs = [int(f) for f in file.read().split()]

  # Check if freq is within valid range
  if freq not in available_freqs:
    print(f"Error: Frequency {freq}Hz not supported. Valid options: {available_freqs}")
    return

  # Attempt to write the frequency to min and max files (with sudo)
  try:
    with open('/sys/devices/57000000.gpu/devfreq/57000000.gpu/min_freq', 'w') as min_file:
      min_file.write(str(freq))
    with open('/sys/devices/57000000.gpu/devfreq/57000000.gpu/max_freq', 'w') as max_file:
      max_file.write(str(freq))
    print(f"GPU frequency set to {freq}Hz (if supported by hardware).")
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



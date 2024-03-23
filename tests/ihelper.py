import os

def modify_gpu_freq(filename, freq):
  """
  Modifies the GPU_FREQ value in a file to freq.

  Args:
    filename: The path to the makefile.
    freq: The frequency to set the GPU to.
  """
  # Open the file in read mode
  with open(filename, "r") as file:
    lines = file.readlines()

  # Modify line with GPU_FREQ declaration
  modified_lines = []
  for line in lines:
    if line.startswith("GPU_FREQ = "):
      # Extract the beginning part of the line
      start_of_line = line.split("=")[0]
      # Combine with freq to set the value
      modified_line = start_of_line + '= '  + str(freq) + '\n'
    else:
      modified_line = line

    modified_lines.append(modified_line)

  # Open the file again in write mode (overwrites existing content)
  with open(filename, "w") as file:
    file.writelines(modified_lines)

  # Change the GPU frequency using the makefile
  os.system('cd /home/iloudaros/LoudVA && make change_gpu_freq')


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



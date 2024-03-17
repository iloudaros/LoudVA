import os

def modify_gpu_freq(filename, freq):
  """
  Modifies the GPU_FREQ value in a file to freq.

  Args:
    filename: The path to the makefile.
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



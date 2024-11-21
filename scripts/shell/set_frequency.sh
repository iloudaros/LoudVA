#!/bin/bash

# Get the model of the Jetson device
model=$(tr -d '\0' < /proc/device-tree/model)

# Set the GPU frequency
set_gpu_freq() {
  local freq=$1

  if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]; then
    gpu_path="/sys/devices/57000000.gpu/devfreq/57000000.gpu"
  elif [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ] || [ "${model}" = "Jetson-AGX" ]; then
    gpu_path="/sys/devices/17000000.gv11b/devfreq/17000000.gv11b"
  else
    echo "This is not a supported Jetson device."
    return 1
  fi

  # Set the minimum and maximum GPU frequencies
  sudo sh -c "echo ${freq} > ${gpu_path}/min_freq"
  sudo sh -c "echo ${freq} > ${gpu_path}/max_freq"

  echo "GPU frequency set to ${freq} Hz"
}

# Print available frequencies
print_available_frequencies() {
  echo "Model: ${model}"

  if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]; then
    cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/available_frequencies
  elif [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ] || [ "${model}" = "Jetson-AGX" ]; then
    cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/available_frequencies
  else
    echo "This is not a supported Jetson device."
  fi
}

# Check if a frequency was provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <frequency>"
  echo "Available frequencies:"
  print_available_frequencies
  exit 1
fi

# Set the GPU frequency
set_gpu_freq $1

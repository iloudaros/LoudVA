#!/bin/bash

# Define the source and target directories
source_dir="/home/louduser/LoudVA/measurements"
target_dir="/home/louduser/LoudVA/measurements/archive"

# If there are 3 or less folders in the source directory, exit the script
if [ $(ls -1q "$source_dir" | wc -l) -le 3 ]; then
  echo "No folders to move"
  exit 0
fi

# If the target directory does not exist, create it
if [ ! -d "$target_dir" ]; then
  mkdir -p "$target_dir"
fi

# Get current date and time in YYYY-MM-DD_HH-MM-SS format
current_datetime=$(date +%Y-%m-%d_%H-%M-%S)

# Create the target directory with current date and time
mkdir -p "${target_dir}/${current_datetime}"

# Loop through all folders in the source directory
for folder in "$source_dir"/*; do
  # Check if it's a directory and not one to exclude
if [[ -d "$folder" &&  !(  "$folder" == "$source_dir/performance" || "$folder" == "$source_dir/power" ||  "$folder" == "$source_dir/archive" ) ]]; then
    # Print the folder name
    echo "Moving folder: $folder"
    # Move the folder to the target directory
    mv "$folder" "${target_dir}/${current_datetime}"
  fi
done

echo "--> Folders moved to: ${target_dir}/${current_datetime}"

#!/bin/bash

# Check if two arguments are provided
if [ $# -ne 2 ]; then
  echo "Usage: $0 <input_file> <output_file>"
  exit 1
fi

# Get the name of the model from /proc/device-tree/model
model=$(tr -d '\0' </proc/device-tree/model)


# Get the input and output files
input_file="$1"
output_file="$2"


# Check if the input file exists
if [ ! -f "$input_file" ]; then
  echo "Error: Input file '$input_file' does not exist."
  exit 1
fi

# Delete the output file if it exists
if [ -f "$output_file" ]; then
  rm "$output_file"
fi

# Open the input and output files
while IFS= read -r line; do
  # For the Jetson Nano, extract the number following "POM_5V_IN" using grep and sed.
  if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]
  then
    number=$(grep -o 'POM_5V_IN\s*\([0-9]*\)' <<< "$line" | sed 's/POM_5V_IN //')
  fi

  # For the NX, extract the number following "VDD_IN" using grep and sed.
  if [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ]
  then
    number=$(grep -o 'VDD_IN\s*\([0-9]*\)' <<< "$line" | sed 's/VDD_IN //')
  fi


  # For the AGX Xavier, extract the number following "GPU", "CPU", "SOC", "CV", "VDDRQ" and "SYS5V" and save their sum.
  if [ "${model}" = "Jetson-AGX" ]
  then
    gpu=$(grep -o 'GPU\s*\([0-9]*\)' <<< "$line" | grep -o '[0-9]*')
    cpu=$(grep -o 'CPU\s*\([0-9]*\)' <<< "$line" | grep -o '[0-9]*')
    soc=$(grep -o 'SOC\s*\([0-9]*\)' <<< "$line" | grep -o '[0-9]*')
    cv=$(grep -o 'CV\s*\([0-9]*\)' <<< "$line" | grep -o '[0-9]*')
    vddrq=$(grep -o 'VDDRQ\s*\([0-9]*\)' <<< "$line" | grep -o '[0-9]*')
    sys5v=$(grep -o 'SYS5V\s*\([0-9]*\)' <<< "$line" | sed 's/SYS5V //')
    number=$((gpu + cpu + soc + cv + vddrq + sys5v))
  fi  

  # Check if a number was found
  if [[ -n "$number" ]]; then
    # Append the number to the output file with a newline
    echo "$number" >> "$output_file"
  fi

  # empty the number variable
  number=""

done < "$input_file"

echo "Extracted numbers from '$input_file' and saved them to '$output_file'"


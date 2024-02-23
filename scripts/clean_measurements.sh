#!/bin/bash

# Check if two arguments are provided
if [ $# -ne 2 ]; then
  echo "Usage: $0 <input_file> <output_file>"
  exit 1
fi

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
  # Extract the number following "POM_5V_IN" using grep and sed
  number=$(grep -o 'POM_5V_IN\s*\([0-9]*\)' <<< "$line" | sed 's/POM_5V_IN //')

  # Check if a number was found
  if [[ -n "$number" ]]; then
    # Append the number to the output file with a newline
    echo "$number" >> "$output_file"
  fi
done < "$input_file"

echo "Extracted numbers from '$input_file' and saved them to '$output_file'"


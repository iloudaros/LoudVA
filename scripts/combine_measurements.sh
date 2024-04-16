#!/bin/bash

# Check if an argument is provided
if [ -z "$1" ]; then
  echo "Error: Please provide the base name of the CSV files as an argument."
  exit 1
fi

# Define the base name
base_name="$1"
combined_file=${2:-"${base_name}.csv"}

# Initialize the output file with the first file's content
first_file=$(ls -1 "${base_name}_"*.csv | head -n 1)
if [ -z "$first_file" ]; then
  echo "Error: No CSV files found with the base name '${base_name}'"
  exit 1
fi

# Copy the first file's content to the output file
cp "$first_file" "$combined_file"

# Delete the last line of the output file
sed -i '$ d' "$combined_file"

# Loop through remaining files (sorted numerically)
for file in $(ls -1 "${base_name}_"*.csv | sort -V); do
  # Extract the last line
  last_line=$(tail -n 1 "$file")

  # Append the last line to the output file
  echo "$last_line" >> "$combined_file"
done

echo "Combined CSV file created: ${base_name}.csv"

# Delete the original files
rm "${base_name}_"*.csv

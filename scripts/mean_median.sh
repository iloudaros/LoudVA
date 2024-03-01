#!/bin/bash

# Check if a file is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

# Store the filename in a variable
filename="$1"

# Check if the file exists
if [ ! -f "$filename" ]; then
  echo "Error: File '$filename' does not exist."
  exit 1
fi

# Use awk to calculate the sum and number of lines
sum=$(awk '{ sum += $1 } END { print sum }' "$filename")
count=$(wc -l < "$filename")

# Calculate the mean using bc for floating-point division
mean=$(echo "scale=2; $sum / $count" | bc)

# Use sort and awk to calculate the median
sorted=$(sort -n "$filename")
middle_index=$(echo "scale=0; ($count + 1) / 2" | bc)

# Check if there's an even number of elements
if [ $(echo "$count % 2" | bc) -eq 0 ]; then
  # If even, median is the average of the two middle elements
  median=$(echo "scale=2; (($(awk "NR == $middle_index" <<< "$sorted") + $(awk "NR == $((middle_index - 1))" <<< "$sorted")) / 2)" | bc)
else
  # If odd, median is the middle element
  median=$(awk "NR == $middle_index" <<< "$sorted")
fi

# Print the results
echo "Mean: $mean"
echo "Median: $median"

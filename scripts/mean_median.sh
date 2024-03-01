#!/bin/bash

# Check for file argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

# Calculate mean
sum=0
count=0
while read -r number; do
  sum=$((sum + number))
  count=$((count + 1))
done < "$1"

mean=$((sum / count))

# Calculate median
sorted=$(sort -n "$1")
middle=$((count / 2))

if [[ $((count % 2)) -eq 0 ]]; then
  median=$(( (${sorted[$middle]} + ${sorted[$((middle + 1))]}) / 2 ))
else
  median=${sorted[$middle]}
fi

# Output results
echo "Mean: $mean"
echo "Median: $median"
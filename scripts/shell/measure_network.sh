#!/bin/bash

# Initialize variables
IP_ADDRESS=""
OUTPUT_DIR=""
START=""
END=""

# Parse command line arguments
while getopts ":i:o:s:e:" opt; do
  case $opt in
    i) IP_ADDRESS="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    s) START="$OPTARG" ;;
    e) END="$OPTARG" ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
    :) echo "Option -$OPTARG requires an argument" >&2; exit 1 ;;
  esac
done

# Validate required arguments
if [[ -z "$IP_ADDRESS" || -z "$OUTPUT_DIR" || -z "$START" || -z "$END" ]]; then
  echo "Error: Missing required arguments"
  echo "Usage: $0 -i <ip:port> -o <output_dir> -s <start_batch> -e <end_batch>"
  exit 1
fi

# Validate numerical arguments
re='^[0-9]+$'
if ! [[ $START =~ $re ]] || ! [[ $END =~ $re ]]; then
  echo "Error: Start and end batch must be numbers"
  exit 1
fi

if [ $START -gt $END ]; then
  echo "Error: Start batch ($START) cannot be greater than end batch ($END)"
  exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Main command
COMMAND="/home/iloudaros/tritonserver/clients/bin/perf_analyzer -u $IP_ADDRESS -s 10 -m inception_graphdef --measurement-mode count_windows"

# Run performance tests
for ((i=START; i<=END; i++))
do
  OUTPUT_FILE="${OUTPUT_DIR}/remote_performance_measurements_${i}.csv"
  $COMMAND -f "$OUTPUT_FILE" -b $i
done

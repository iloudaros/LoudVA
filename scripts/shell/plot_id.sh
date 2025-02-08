#!/bin/bash

# Check if an id and folder path is provided
if [ $# -ne 2 ]; then
  echo "Usage: $0 <id> <folder_path>"
  exit 1
fi

ID="$1"
FOLDER_PATH="$2"

TEGRA_LOG=$(find "$FOLDER_PATH" -maxdepth 1 -type f -name "*_id${ID}_*tegrastats")

REQUEST_LOG=$(find "$FOLDER_PATH" -maxdepth 1 -type f -name "*_id${ID}_*.csv")

echo "Plotting Tegrastats for ID $ID and folder path $FOLDER_PATH"
echo "Tegra: $TEGRA_LOG"
echo "Request: $REQUEST_LOG"

python3 plots/LoudVA_activity.py --logs $TEGRA_LOG,$REQUEST_LOG --plot-latency 
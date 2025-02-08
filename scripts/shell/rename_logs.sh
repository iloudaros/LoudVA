#!/bin/bash

# Check if a folder path is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <folder_path>"
  exit 1
fi

FOLDER_PATH="$1"
COUNTER=0

# Loop through each file in the folder that matches the pattern
for FILE in "$FOLDER_PATH"/*_tegrastats; do
  if [[ -f "$FILE" ]]; then
    # Extract the parts of the filename
    BASENAME=$(basename "$FILE")
    DATE=$(echo "$BASENAME" | cut -d'_' -f1)
    TIME=$(echo "$BASENAME" | cut -d'_' -f2)
    OTHER=$(echo "$BASENAME" | cut -d'_' -f3-)

    # Construct the new filename with the counter
    NEW_FILENAME="${DATE}_${TIME}_id${COUNTER}_${OTHER}"

    # Rename the file
    mv "$FILE" "$FOLDER_PATH/$NEW_FILENAME"

    # Increment the counter
    COUNTER=$((COUNTER + 1))
  fi
done

echo "Renaming completed!"

#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

filename="$1"

grep -E 'POM_5V_IN\s+(\d+)' "$filename" | sed 's/.* \(.*\) \/\1/'

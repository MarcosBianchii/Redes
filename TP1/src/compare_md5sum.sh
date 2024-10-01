#!/bin/bash

# Check if both arguments (from_dir and to_dir) are provided
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 from_dir to_dir"
  exit 1
fi

# Assign the parameters to variables
from_dir="$1"
to_dir="$2"

# Check if both directories exist
if [[ ! -d "$from_dir" || ! -d "$to_dir" ]]; then
  echo "One or both of the directories do not exist."
  exit 1
fi

# Loop through files in the from_dir
for from_file in "$from_dir"/*; do
  # Get the filename from the full path
  filename=$(basename "$from_file")

  # Check if the same file exists in the to_dir
  to_file="$to_dir/$filename"
  if [[ -f "$to_file" ]]; then
    # Calculate md5sum for both files
    md5_from=$(md5sum "$from_file" | awk '{ print $1 }')
    md5_to=$(md5sum "$to_file" | awk '{ print $1 }')

    # Print the md5sums
    echo "File: $filename"
    echo "MD5 $from_dir:    $md5_from"
    echo "MD5 $to_dir:   $md5_to"

    # Compare the md5sums
    if [[ "$md5_from" == "$md5_to" ]]; then
      echo "File $filename: IDENTICAL"
    else
      echo "File $filename: DIFFERENT"
    fi
  else
    echo "File $filename: does not exist in $to_dir"
  fi
done

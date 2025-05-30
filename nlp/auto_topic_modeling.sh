#!/bin/bash

#Script is inted to be used to automate topic modeling processing
# Define an array to hold the file names
files=()
# Define the directory path
dir="convo-analysis/raw-text-convo/"

# Loop through each file in the specified directory
for file in "$dir"*; do
    # Check if it's a regular file (not a directory or link, etc.)
    if [ -f "$file" ]; then
        # Add the file to the array, extracting just the filename if needed
        files+=("$(basename "$file")")
    fi
done


# Loop through the array of files
for file in "${files[@]}"; do
    python3 topic_modeling.py "$file"

done



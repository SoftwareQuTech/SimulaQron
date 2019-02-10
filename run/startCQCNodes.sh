#!/usr/bin/env bash

# start the nodes ['Alice', 'Bob', 'Charlie', 'David', 'Eve']

# Get the path to the SimulaQron folder
this_file_path=$(realpath "$0")
this_folder_path=$(dirname "${this_file_path}")
simulaqron_path=${this_folder_path%/run}

cd "$simulaqron_path"/run

for name in "$@"
do
    python3 startCQC.py "$name" &
done

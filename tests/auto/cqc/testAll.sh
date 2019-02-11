#!/bin/bash

# Get the path to the SimulaQron folder
this_file_path=$0
this_folder_path=$(dirname "${this_file_path}")
simulaqron_path=$(${this_folder_path}/../../../toolbox/get_simulaqron_path.py)

echo "Starting logging server"
sh "$simulaqron_path"/run/startAllLog.sh -nd "Alice Bob"&
sleep 1s
echo "Started logging server"
echo "Testing cqc headers.."
python3 "$simulaqron_path"/tests/auto/cqc/testCQCMessages.py


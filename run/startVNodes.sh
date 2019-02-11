#!/usr/bin/env bash
# start the nodes specified by the arguments
# the arguments should be a list of the informal names of hosts

# Get the path to the SimulaQron folder
this_file_path=$0
this_folder_path=$(dirname "${this_file_path}")
simulaqron_path=$(${this_folder_path}/../toolbox/get_simulaqron_path.py)

cd "$simulaqron_path"/run

for name in "$@"
do
    python3 startNode.py "$name" &
done

#!/bin/bash

set -eu

# Get the path to the SimulaQron folder
this_file_path=$0
this_folder_path=$(dirname "${this_file_path}")
simulaqron_path=$(${this_folder_path}/../../simulaqron/toolbox/get_simulaqron_path.py)

# Clean up leftovers
$simulaqron_path/cli/SimulaQron stop
make -C $simulaqron_path clean

# Start the Virtual and CQC Nodes
echo -e "\e[1;32m[$(date +%H:%M:%S)] Start CQC Nodes\e[0m"
$simulaqron_path/cli/SimulaQron start --nrnodes 2
sleep 5

# Build the tests
echo -e "\e[1;32m[$(date +%H:%M:%S)] Build Tests\e[0m"
make all

# Start the tests
echo -e "\e[1;32m[$(date +%H:%M:%S)] Run Tests\e[0m"
./qubit localhost 8803
./send localhost 8803 localhost 8804
./recv localhost 8804
./gates localhost 8803

echo -e "\e[1;32m[$(date +%H:%M:%S)] Testing Complete\e[0m"
$simulaqron_path/cli/SimulaQron stop

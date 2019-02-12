#!/bin/bash

set -eu

# Get the path to the SimulaQron folder
this_file_path=$0
this_folder_path=$(dirname "${this_file_path}")
simulaqron_path=$(${this_folder_path}/../../../simulaqron/toolbox/get_simulaqron_path.py)

# Start the Virtual and CQC Nodes
echo -e "\e[1;32m[$(date +%H:%M:%S)] Start CQC Nodes\e[0m"
$simulaqron_path/run/startAll.sh --nrnodes 2 &
sleep 5

# start the test
echo -e "\e[1;32m[$(date +%H:%M:%S)] Run Tests\e[0m"
cargo test -- --nocapture

echo -e "\e[1;32m[$(date +%H:%M:%S)] Testing Complete\e[0m"

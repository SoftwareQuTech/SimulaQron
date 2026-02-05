#!/usr/bin/env bash

# Check if SimulaQron is already running
if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    # TODO - Modify the list of nodes to start on this machine
    # TODO - Change the filename of the network configuration if you changed that
    if ! simulaqron start --nodes=Alice,Bob --network-config-file network_config.json
    then
        echo "SimulaQron could not start correctly"
        exit 1
    fi
fi


# Run the files for Alice, Bob or whatever nodes you construct
python3 bobTest.py &
python3 aliceTest.py

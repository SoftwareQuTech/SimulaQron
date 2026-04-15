#!/usr/bin/env bash

# Check if SimulaQron is already running
if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    if ! simulaqron start --nodes=Alice,Bob --network-config-file classicalNet.json
    then
        echo "SimulaQron could not start correctly!"
        exit 1
    fi
fi

sleep 5

python3 bobTest.py &
python3 aliceTest.py






#!/usr/bin/env bash

# Check if SimulaQron is already running
if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    if ! simulaqron start --nodes=Alice,Bob,Charlie,David --network-config-file classicalNet.json --simulaqron-config-file simulaqron_settings.json
    then
        echo "SimulaQron could not start correctly"
        exit 1
    fi
fi

sleep 5

python3 bobTest.py &
sleep 1
python3 charlieTest.py &
sleep 1
python3 davidTest.py &
sleep 1
python3 aliceTest.py

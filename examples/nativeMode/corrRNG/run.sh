#!/bin/sh

# Check if SimulaQron is already running
if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    simulaqron start --nodes=Alice,Bob --network-config-file classicalNet.json
fi

python3 bobTest.py &
python3 aliceTest.py






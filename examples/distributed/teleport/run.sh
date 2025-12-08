#!/bin/sh

# Check if SimulaQron is already running
if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    simulaqron start --nodes=Alice,Bob --network-config-file ./networkConfig.json
fi

python3 teleport-bob.py &
python3 teleport-alice.py






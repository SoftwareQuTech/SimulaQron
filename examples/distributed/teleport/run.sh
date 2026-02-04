#!/bin/sh

# Check if SimulaQron is already running
if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    # If not, start simulaqron backend for both nodes
    simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json
fi

python3 teleport-bob.py &
python3 teleport-alice.py






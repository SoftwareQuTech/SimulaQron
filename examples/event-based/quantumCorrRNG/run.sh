#!/usr/bin/env bash
#
# Runs the quantum correlated RNG example.
#
# Unlike the purely classical ping-pong examples, this one uses quantum
# operations (EPR pairs) so the SimulaQron backend must be running.
#
# On two separate machines, run these commands in separate terminals:
#   Machine B (Bob):   python3 bobTest.py
#   Machine A (Alice): python3 aliceTest.py
#
# On a single machine (this script):
#   SimulaQron starts first, then Bob in the background, then Alice.

cd "$(dirname "$0")"

# Start SimulaQron backend if not already running
if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    simulaqron start --nodes=Alice,Bob \
        --network-config-file simulaqron_network.json \
        --simulaqron-config-file simulaqron_settings.json
fi

python3 -u bobTest.py &
BOB_PID=$!

sleep 1

python3 aliceTest.py

kill $BOB_PID 2>/dev/null
wait $BOB_PID 2>/dev/null

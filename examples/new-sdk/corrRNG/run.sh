#!/usr/bin/env bash

# Flag used to determine whether to start simulaqron backend or not
# This is useful when using this script to run the application in different machines.
START_SIMULAQRON=true

# Process the arguments, if any
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--no-start-simulaqron)
            START_SIMULAQRON=false
            shift
            ;;
    esac
done

if [ "$START_SIMULAQRON" = true ]; then
    # Check if SimulaQron is already running
    if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
        # If not, start simulaqron backend for both nodes
        simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    fi
fi

python3 aliceTest.py &
python3 bobTest.py

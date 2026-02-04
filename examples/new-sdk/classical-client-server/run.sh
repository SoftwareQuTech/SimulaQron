#!/bin/sh

# Running SimulaQron backend is not needed for this example.
## Check if SimulaQron is already running
#if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
#    # If not, start simulaqron backend for both nodes
#    simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json
#fi

# Run the server
python3 example_server_alice.py &
# Wait 1 second for the server to fully start
sleep 1
# Run the client
python3 example_client_bob.py &

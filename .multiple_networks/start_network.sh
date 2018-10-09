#!/bin/bash

network_name=$1

# Move all files to config folder

rm -r "${NETSIM}/config/"*
cp "${NETSIM}/.multiple_networks/configs/${network_name}/"* "${NETSIM}/config"

# Kill the current such network
sh kill_network.sh "${network_name}"

# Start the network again
while IFS='' read -r name; do
    python "${NETSIM}/run/startNode.py" "$name" "${network_name}" &
    python "${NETSIM}/run/startCQC.py" "$name" "${network_name}" &
done < "${NETSIM}/config/Nodes.cfg"


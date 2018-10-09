#!/usr/bin/env sh

sh killAll_networks.sh

while IFS='' read -r name; do
    sh start_network.sh "$name"
done < "network_names.cfg"
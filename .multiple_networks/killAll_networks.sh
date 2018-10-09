#!/usr/bin/env sh

while IFS='' read -r name; do
    sh kill_network.sh "$name"
done < "network_names.cfg"

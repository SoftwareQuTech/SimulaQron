#!/usr/bin/env bash
# start the nodes specified by the arguments
# the arguments should be a list of the informal names of hosts

cd "$NETSIM"/run

for name in "$@"
do
    python3 startNode.py "$name" &
done

#!/usr/bin/env bash


# start the node Alice, Bob

cd "$NETSIM"/run

for name in "$@"
do
    python startCQC.py "$name" &
done

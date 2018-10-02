#!/usr/bin/env bash

# start the nodes ['Alice', 'Bob', 'Charlie', 'David', 'Eve']

cd "$NETSIM"/run

for name in "$@"
do
    python startCQC.py "$name" &
done

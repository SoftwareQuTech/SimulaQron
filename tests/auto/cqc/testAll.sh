#!/bin/bash

echo "Starting logging server"
sh "$NETSIM"/run/startAll.sh -b log
echo "Started logging server"
sleep 1s
echo "Testing cqc headers.."
python testCQCMessages.py

echo "Starting SimulaQron server"
sh "$NETSIM"/run/startAll.sh -b simulaqron
echo "Started SimulaQron server"

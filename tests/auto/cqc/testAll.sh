#!/bin/bash

echo "Starting logging server"
sh "$NETSIM"/run/startAllLog.sh -nd "Alice Bob"&
sleep 1s
echo "Started logging server"
echo "Testing cqc headers.."
python "$NETSIM"/tests/auto/cqc/testCQCMessages.py


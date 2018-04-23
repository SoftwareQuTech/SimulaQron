#!/bin/bash

python "$NETSIM"/tests/auto/cqc/changebackend.py log
echo "Starting logging server"
sh "$NETSIM"/run/startAll.sh Alice Bob
echo "Started logging server"
sleep 1s
echo "Testing cqc headers.."
python testCQCMessages.py


python "$NETSIM"/tests/auto/cqc/changebackend.py simulaqron
echo "Starting SimulaQron server"
sh "$NETSIM"/run/startAll.sh Alice Bob Charlie
echo "Started SimulaQron server"

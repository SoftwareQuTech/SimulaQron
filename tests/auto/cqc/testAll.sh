#!/bin/bash

#python "$NETSIM"/tests/auto/cqc/changebackend.py log
echo "Starting logging server"
sh "$NETSIM"/run/startAllLog.sh -nd "Alice Bob" &
sleep 1s
echo "Started logging server"
echo "Testing cqc headers.."
python "$NETSIM"/tests/auto/cqc/testCQCMessages.py


#python "$NETSIM"/tests/auto/cqc/changebackend.py simulaqron
echo "Starting SimulaQron server"
sh "$NETSIM"/run/startAll.sh -nd "Alice Bob Charlie" &
sleep 1s
echo "Started SimulaQron server"

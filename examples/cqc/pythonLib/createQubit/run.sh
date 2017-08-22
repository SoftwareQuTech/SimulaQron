#!/bin/sh

cd "$NETSIM/cqc/backend"
python setupCQC.py Alice &

sleep 5s

cd "$NETSIM/examples/cqc/pythonLib/createQubit"
python aliceTest.py &

#!/bin/sh

cd "$NETSIM/examples/graphState"
python bobTest.py &
python charlieTest.py &
python davidTest.py &
python aliceTest.py

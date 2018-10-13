#!/bin/sh

cd "$NETSIM/examples/nativeMode/graphState"
python bobTest.py &
python charlieTest.py &
python davidTest.py &
python aliceTest.py

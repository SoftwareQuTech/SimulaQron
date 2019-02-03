#!/bin/sh

cd "$NETSIM/examples/nativeMode/graphState"
python3 bobTest.py &
python3 charlieTest.py &
python3 davidTest.py &
python3 aliceTest.py

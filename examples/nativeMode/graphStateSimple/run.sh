#!/bin/sh

cd "$NETSIM/examples/nativeMode/graphStateSimple"
python bobTest.py &
python charlieTest.py &
python davidTest.py &
python aliceTest.py

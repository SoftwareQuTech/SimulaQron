#!/bin/sh

python aliceTest.py &
python bobTest.py &
python charlieTest.py &
python ../../../../../run/addNode.py &
python petrosTest.py &
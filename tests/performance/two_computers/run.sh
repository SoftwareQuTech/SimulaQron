#!/bin/sh

python /home/axel/Documents/SimulaQron/run/startNode.py Alice &
python /home/axel/Documents/SimulaQron/run/startCQC.py Alice &

sleep 10s

python client.py 1 5 1

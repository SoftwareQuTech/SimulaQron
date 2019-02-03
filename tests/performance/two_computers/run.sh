#!/bin/sh

python3 /home/axel/Documents/SimulaQron/run/startNode.py Alice &
python3 /home/axel/Documents/SimulaQron/run/startCQC.py Alice &

sleep 10s

python3 client.py 1 5 1

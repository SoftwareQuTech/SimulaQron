#!/bin/sh

python /Users/adahlberg/Documents/SimulaQron/run/startNode.py Alice &
python /Users/adahlberg/Documents/SimulaQron/run/startCQC.py Alice &
python /Users/adahlberg/Documents/SimulaQron/run/startNode.py Bob &
python /Users/adahlberg/Documents/SimulaQron/run/startCQC.py Bob &

sleep 10s

python server.py 1 6 10&
python client.py 1 6 10

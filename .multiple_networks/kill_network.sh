#!/bin/bash

network_name=$1

NETWORK_PIDS=$(ps aux | grep python | grep -E "startNode|startCQC" | grep -E ${network_name} | awk {'print $2'})

if [ "$NETWORK_PIDS" != "" ]
then
    kill -9 $NETWORK_PIDS
fi

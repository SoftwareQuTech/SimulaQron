#!/bin/bash

set -eu

# Start the Virtual and CQC Nodes
echo -e "\e[1;32m[$(date +%H:%M:%S)] Start Virtual Nodes\e[0m"
nohup $NETSIM/run/startVNodes.sh > /dev/null 2>&1 && sleep 5

echo -e "\e[1;32m[$(date +%H:%M:%S)] Start CQC Nodes\e[0m"
nohup $NETSIM/run/startCQCNodes.sh > /dev/null 2>&1 && sleep 5

# start the test
echo -e "\e[1;32m[$(date +%H:%M:%S)] Run Tests\e[0m"
cargo test -- --nocapture

echo -e "\e[1;32m[$(date +%H:%M:%S)] Testing Complete\e[0m"

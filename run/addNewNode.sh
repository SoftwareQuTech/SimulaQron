#!/usr/bin/env sh
echo
echo "$1, localhost, $2" >> "../config/appNodes.cfg"
echo
echo "$1, localhost, $2" >> "../config/classicalNet.cfg"
echo
echo "$1, localhost, $2" >> "../config/cqcNodes.cfg"
echo
echo "$1, localhost, $2" >> "../config/virtualNodes.cfg"
echo
echo $1    >> "../config/Nodes.cfg"

python "$NETSIM/run/startNode.py" "$1" &
python "$NETSIM/run/startCQC.py" "$1" &
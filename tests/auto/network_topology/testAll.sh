#!/bin/bash

if [ -f "${NETSIM}/config/settings.ini" ]; then
    echo "Temporarily moving settings.ini to use default settings..."
    mv "${NETSIM}/config/settings.ini" "${NETSIM}/config/_settings.ini"
fi

echo "Setting topo settings.ini..."
cp "${NETSIM}/tests/auto/resources/settings_topo_path/settings.ini" "${NETSIM}/config/settings.ini"

echo "Starting SimulaQron sever (restricted topology)"
sh "${NETSIM}/run/startAll.sh"
sleep 1s
echo "Started SimulaQron sever (restricted topology)"
python "${NETSIM}/tests/auto/network_topology/test_restricted_topology.py"


echo "Setting topo settings.ini to full path..."
cp "${NETSIM}/tests/auto/resources/settings_full_topo/settings.ini" "${NETSIM}/config/settings.ini"


echo "Starting SimulaQron sever (default settings)"
sh "${NETSIM}/run/startAll.sh"
sleep 1s
echo "Started SimulaQron sever (default settings)"
python "${NETSIM}/tests/auto/network_topology/test_default_topology.py"

# Clean up
if [ -f "${NETSIM}/config/_settings.ini" ]; then
    echo "Moving back the old settings file"
    mv "${NETSIM}/config/_settings.ini" "${NETSIM}/config/settings.ini"
fi


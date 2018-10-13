#!/bin/bash

if [ -f "${NETSIM}/config/settings.ini" ]; then
    echo "Temporarily moving settings.ini to use default settings..."
    mv "${NETSIM}/config/settings.ini" "${NETSIM}/config/_settings.ini"
fi

echo "Starting SimulaQron sever (restricted topology)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice Bob Charlie" -tp "path" &
sleep 1s
echo "Started SimulaQron sever (restricted topology)"
python "${NETSIM}/tests/auto/network_topology/test_restricted_topology.py"

echo "Starting SimulaQron sever (default settings)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice Bob Charlie" &
sleep 1s
echo "Started SimulaQron sever (default settings)"
python "${NETSIM}/tests/auto/network_topology/test_default_topology.py"

# Clean up
if [ -f "${NETSIM}/config/_settings.ini" ]; then
    echo "Moving back the old settings file"
    mv "${NETSIM}/config/_settings.ini" "${NETSIM}/config/settings.ini"
fi

# Start servers again for future tests
echo "Starting SimulaQron sever (default settings)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice Bob Charlie David Eve" &
sleep 1s
echo "Started SimulaQron sever (default settings)"

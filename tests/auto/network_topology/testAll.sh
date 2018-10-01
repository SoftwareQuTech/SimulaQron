#!/bin/bash

if [ -f "${NETSIM}/config/settings.ini" ]; then
    echo "Temporarily moving settings.ini to use default settings..."
    mv "${NETSIM}/config/settings.ini" "${NETSIM}/config/_settings.ini"
fi

echo "Creating a new temporary settings file with restricted topology"
cp "resources/settings.ini" "${NETSIM}/config/settings.ini"
#SETTINGS_FILE="${NETSIM}/config/settings.ini"
#touch "${SETTINGS_FILE}"
#echo "[BACKEND]" >> "${SETTINGS_FILE}"
#echo "maxqubits = 20" >> "${SETTINGS_FILE}"
#echo "maxregisters = 1000" >> "${SETTINGS_FILE}"
#echo "waittime = 0.5" >> "${SETTINGS_FILE}"
#echo "loglevel = warning" >> "${SETTINGS_FILE}"
#echo "backendhandler = simulaqron" >> "${SETTINGS_FILE}"
#echo "topology_file = tests/auto/network_topology/resources/topology.json" >> "${SETTINGS_FILE}"
#echo "" >> "${SETTINGS_FILE}"
#echo "[FRONTEND]" >> "${SETTINGS_FILE}"
#echo "loglevel = warning" >> "${SETTINGS_FILE}"

echo "Starting SimulaQron sever (restricted topology)"
sh "${NETSIM}/run/startAll.sh" Alice Bob Charlie &
sleep 1s
echo "Started SimulaQron sever (restricted topology)"
python "${NETSIM}/tests/auto/network_topology/test_restricted_topology.py"

echo "Removing temporary settings file"
rm "${NETSIM}/config/settings.ini"

echo "Starting SimulaQron sever (default settings)"
sh "${NETSIM}/run/startAll.sh" Alice Bob Charlie &
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
sh "${NETSIM}/run/startAll.sh" Alice Bob Charlie David Eve &
sleep 1s
echo "Started SimulaQron sever (default settings)"

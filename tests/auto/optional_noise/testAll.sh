#!/bin/bash

if [ -f "${NETSIM}/config/settings.ini" ]; then
    echo "Temporarily moving settings.ini to use noisy settings..."
    mv "${NETSIM}/config/settings.ini" "${NETSIM}/config/_settings.ini"
fi

echo "Setting noisy settings.ini..."
cp "${NETSIM}/tests/auto/optional_noise/resources/settings.ini" "${NETSIM}/config/settings.ini"

echo "Starting SimulaQron sever (noisy setting)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice"
sleep 1s
echo "Started SimulaQron sever (noise setting)"
python "${NETSIM}/tests/auto/optional_noise/test_optional_noise.py"

# Clean up
rm "${NETSIM}/config/settings.ini"
if [ -f "${NETSIM}/config/_settings.ini" ]; then
    echo "Moving back the old settings file"
    mv "${NETSIM}/config/_settings.ini" "${NETSIM}/config/settings.ini"
fi

# Start servers again for future tests
echo "Starting SimulaQron sever (default settings)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice Bob Charlie David Eve" &
sleep 1s
echo "Started SimulaQron sever (default settings)"

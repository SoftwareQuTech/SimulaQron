#!/bin/bash

if [ -f "${NETSIM}/config/settings.ini" ]; then
    echo "Temporarily moving settings.ini to use default settings..."
    mv "${NETSIM}/config/settings.ini" "${NETSIM}/config/_settings.ini"
fi

echo "Setting log settings.ini..."
cp "${NETSIM}/tests/auto/resources/log_settings/settings.ini" "${NETSIM}/config/settings.ini"

echo "Starting logging server"
sh "$NETSIM"/run/startAllLog.sh &
sleep 1s
echo "Started logging server"
echo "Testing cqc headers.."
python "$NETSIM"/tests/auto/cqc/testCQCMessages.py

# Clean up
if [ -f "${NETSIM}/config/_settings.ini" ]; then
    echo "Moving back the old settings file"
    mv "${NETSIM}/config/_settings.ini" "${NETSIM}/config/settings.ini"
fi

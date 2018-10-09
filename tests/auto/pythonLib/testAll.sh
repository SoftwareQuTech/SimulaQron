#!/usr/bin/env sh
TEST_PIDS=$(ps aux | grep python | grep -E "test_" | awk {'print $2'})
if [ "$TEST_PIDS" != "" ]
then
        kill -9 $TEST_PIDS
fi


if [ -f "${NETSIM}/config/settings.ini" ]; then
    echo "Temporarily moving settings.ini to use default settings..."
    mv "${NETSIM}/config/settings.ini" "${NETSIM}/config/_settings.ini"
fi

echo "Setting default settings.ini..."
cp "${NETSIM}/tests/auto/resources/default_settings/settings.ini" "${NETSIM}/config/settings.ini"

echo "Starting SimulaQron sever (default)"
sh "${NETSIM}/run/startAll.sh"
sleep 1s
echo "Started SimulaQron sever (default)"

sh run.sh $@

# Clean up
if [ -f "${NETSIM}/config/_settings.ini" ]; then
    echo "Moving back the old settings file"
    mv "${NETSIM}/config/_settings.ini" "${NETSIM}/config/settings.ini"
fi


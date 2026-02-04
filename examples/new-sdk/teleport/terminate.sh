#!/usr/bin/env sh
TEST_PIDS=$(ps aux | grep python | grep -E "teleport" | awk {'print $2'})
if [ "$TEST_PIDS" != "" ]
then
        kill -9 $TEST_PIDS
fi

simulaqron stop

# Check if SimulaQron is running
if [ -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    cat $HOME/.simulaqron_pids/simulaqron_network_default.pid | xargs kill -9 
fi


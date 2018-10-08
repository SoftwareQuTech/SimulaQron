#!/usr/bin/env sh
ALL_PIDS=$(ps aux | grep python | grep -E "Test|setup|start" | awk {'print $2'})
if [ "$ALL_PIDS" != "" ]
then
        kill -9 $ALL_PIDS
fi
echo "Starting tests"
cd "$NETSIM"/tests/auto
sh testAll.sh $@


#!/usr/bin/env sh
TEST_PIDS=$(ps aux | grep python3 | grep -E "Test" | awk {'print $2'})
if [ "$TEST_PIDS" != "" ]
then
        kill -9 $TEST_PIDS
fi
sh run.sh $@

#!/usr/bin/env sh
PIDS=$(ps aux | grep python | grep -E "start|server\.py" | awk {'print $2'})
if [ "$PIDS" != "" ]
then
        kill -9 $PIDS
fi
sh run.sh

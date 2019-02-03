#!/usr/bin/env sh
PIDS=$(ps aux | grep python3 | grep -E "start|server\.py" | awk {'print $2'})
if [ "$PIDS" != "" ]
then
        kill -9 $PIDS
fi
sh run.sh

#!/usr/bin/env sh
NODE_PIDS=$(ps aux | grep python | grep -E "node\.py|node_v2\.py" | awk {'print $2'})
if [ "$NODE_PIDS" != "" ]
then
        kill -9 $NODE_PIDS
fi
sh run_v2.sh

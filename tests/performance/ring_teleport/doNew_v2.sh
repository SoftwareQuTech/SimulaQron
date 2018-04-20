ps aux | grep python | grep 'node\.py' | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep 'node_v2\.py' | awk {'print $2'} | xargs kill -9
sh run_v2.sh

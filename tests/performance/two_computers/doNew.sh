ps aux | grep python | grep start | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep 'server\.py' | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep 'server\.py' | awk {'print $2'} | xargs kill -9
sh run.sh

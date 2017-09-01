
ps aux | grep python | grep test_ | awk {'print $2'} | xargs kill -9
sh run.sh


ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9
sh run.sh

ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep setup | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep start | awk {'print $2'} | xargs kill -9

sh "$NETSIM/run/startVNodes.sh"

sh "$NETSIM/run/startCQCNodes.sh"

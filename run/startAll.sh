ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep setup | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep start | awk {'print $2'} | xargs kill -9

if [ "$1" = "-v" ] || [ "$3" = "-v" ] ;
then
	sh "$NETSIM/run/startVNodes.sh" -v # ugly
else
	sh "$NETSIM/run/startVNodes.sh" # ugly
fi

sh "$NETSIM/run/startCQCNodes.sh" $1 $2 $3 # ugly

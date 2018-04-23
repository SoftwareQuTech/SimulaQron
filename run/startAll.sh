#!/usr/bin/env bash
ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep setup | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep start | awk {'print $2'} | xargs kill -9

if [ "$#" -eq 0 ] ;
then
    #
    python "$NETSIM/configFiles.py" Alice Bob Charlie David Eve

    sh "$NETSIM/run/startVNodes.sh" Alice Bob Charlie David Eve

    sh "$NETSIM/run/startCQCNodes.sh" Alice Bob Charlie David Eve

else
    python "$NETSIM/configFiles.py" $@

    sh "$NETSIM/run/startVNodes.sh" $@

    sh "$NETSIM/run/startCQCNodes.sh" $@
fi

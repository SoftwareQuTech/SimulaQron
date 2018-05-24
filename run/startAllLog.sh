#!/usr/bin/env sh
ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep setup | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep start | awk {'print $2'} | xargs kill -9

# if no list of names is given we take the list of current Nodes
if [ "$#" -eq 0 ] ;
then
    # check if the file with current nodes exist. Otherwise use Alice - Eve
    if [ -f "$NETSIM/config/Nodes.cfg" ]
    then
        python "$NETSIM/run/log/startCQCLog.py"
    else
        python "$NETSIM/configFiles.py" Alice Bob Charlie David Eve

        python "$NETSIM/run/log/startCQCLog.py" Alice Bob Charlie David Eve
    fi

else  # if arguments were given, create the new nodes and start them
    python "$NETSIM/configFiles.py" $@

    python "$NETSIM/run/log/startCQCLog.py" $@
fi

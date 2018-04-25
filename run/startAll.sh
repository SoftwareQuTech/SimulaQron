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
        while IFS='' read -r name; do
            python "$NETSIM/run/startNode.py" "$name" &
            python "$NETSIM/run/startCQC.py" "$name" &
        done < "$NETSIM/config/Nodes.cfg"
    else
        python "$NETSIM/configFiles.py" Alice Bob Charlie David Eve

        sh "$NETSIM/run/startVNodes.sh" Alice Bob Charlie David Eve

        sh "$NETSIM/run/startCQCNodes.sh" Alice Bob Charlie David Eve
    fi

else  # if arguments were given, create the new nodes and start them
    python "$NETSIM/configFiles.py" $@

    sh "$NETSIM/run/startVNodes.sh" $@

    sh "$NETSIM/run/startCQCNodes.sh" $@
fi

#!/usr/bin/env sh
ALL_PIDS=$(ps aux | grep python | grep -E "Test|setup|start" | awk {'print $2'})
if [ "$ALL_PIDS" != "" ]
then
        kill -9 $ALL_PIDS
fi

# Read in some settings
nodes_file=$NETSIM/$(sed -nr "/^\[CONFIG\]/ { :l /^nodes_file[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $NETSIM/config/settings.ini)
if [ -z "$nodes_file" ]
then
nodes_file="$NETSIM/config/Nodes.cfg"
fi
# if no arguments were given we take the list of current Nodes
if [ "$#" -eq 0 ] ;
then
    # check if the file with current nodes exist. Otherwise use Alice - Eve
    if [ -f ${nodes_file} ]
    then
        python "$NETSIM/run/log/startCQCLog.py"
    else
        python "$NETSIM/configFiles.py" --nodes "Alice Bob Charlie David Eve"

        python "$NETSIM/run/log/startCQCLog.py"
    fi
else  # if arguments were given, create the new nodes and start them
    while [ "$#" -gt 0 ]; do
        key="$1"
        case $key in
            -nn|--nrnodes)
            NRNODES="$2"
            shift
            shift
            ;;
            -tp|--topology)
            TOPOLOGY="$2"
            shift
            shift
            ;;
            -nd|--nodes)
            NODES="$2"
            shift
            shift
            ;;
            *)
            echo "Unknown argument ${key}"
            exit 1
        esac
    done

    python "$NETSIM/configFiles.py" --nrnodes "${NRNODES}" --topology "${TOPOLOGY}" --nodes "${NODES}"

    # We call this script again, without arguments, to use the newly created config-files
    sh "$NETSIM/run/startAllLog.sh"
fi

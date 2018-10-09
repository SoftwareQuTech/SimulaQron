#!/usr/bin/env sh
ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep setup | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep start | awk {'print $2'} | xargs kill -9

# Read in some settings
if [ -f $NETSIM/config/settings.ini ]
then
    nodes_file=$NETSIM/$(sed -nr "/^\[CONFIG\]/ { :l /^nodes_file[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $NETSIM/config/settings.ini)
    if [ -z "$nodes_file" ]
    then
        nodes_file="$NETSIM/config/Nodes.cfg"
    fi
else
    echo "Settings file not found in config folder, aborting"
    exit 1
fi
# if no arguments were given we take the list of current Nodes
if [ "$#" -eq 0 ] ;
then
    # check if the file with current nodes exist. Otherwise use Alice - Eve
    if [ -f ${nodes_file} ]
    then
        while IFS='' read -r name; do
            python "$NETSIM/run/startNode.py" "$name" &
            python "$NETSIM/run/startCQC.py" "$name" &
        done < ${nodes_file}
    else
        python "$NETSIM/configFiles.py" --nodes "Alice Bob Charlie David Eve"

        # We call this script again, without arguments, to use the newly created config-files
        sh "$NETSIM/run/startAll.sh"
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
    sh "$NETSIM/run/startAll.sh"
fi

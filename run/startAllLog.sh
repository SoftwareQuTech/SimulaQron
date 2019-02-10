#!/usr/bin/env sh
ALL_PIDS=$(ps aux | grep python3 | grep -E "Test|setup|start" | awk {'print $2'})
if [ "$ALL_PIDS" != "" ]
then
        kill -9 $ALL_PIDS
fi

# Get the path to the SimulaQron folder
this_file_path=$(realpath "$0")
this_folder_path=$(dirname "${this_file_path}")
simulaqron_path=${this_folder_path%/run}

# if no arguments were given we take the list of current Nodes
if [ "$#" -eq 0 ] ;
then
    # check if the file with current nodes exist. Otherwise use Alice - Eve
    if [ -f "$simulaqron_path/config/Nodes.cfg" ]
    then
        names=""
        while IFS='' read -r name; do
            names="$names $name"
        done < "$simulaqron_path/config/Nodes.cfg"
        python3 "$simulaqron_path/run/log/startCQCLog.py" $names &
    else
        python3 "$simulaqron_path/configFiles.py" --nd "Alice Bob Charlie David Eve"

        # We call this script again, without arguments, to use the newly created config-files
        sh "$simulaqron_path/run/startAllLog.sh"
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

    python3 "$simulaqron_path/configFiles.py" --nrnodes "${NRNODES}" --topology "${TOPOLOGY}" --nodes "${NODES}"

    # We call this script again, without arguments, to use the newly created config-files
    sh "$simulaqron_path/run/startAllLog.sh"
fi

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
        while IFS='' read -r name; do
            python3 "$simulaqron_path/run/startNode.py" "$name" &
            python3 "$simulaqron_path/run/startCQC.py" "$name" &
        done < "$simulaqron_path/config/Nodes.cfg"
    else
        python3 "$simulaqron_path/configFiles.py" --nd "Alice Bob Charlie David Eve"

        # We call this script again, without arguments, to use the newly created config-files
        sh "$simulaqron_path/run/startAll.sh"
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
            --maxqubits_per_node)
            MAXQUBITSPERNODE="$2"
            shift
            shift
            ;;
            --maxregisters_per_node)
            MAXREGISTERSPERNODE="$2"
            shift
            shift
            ;;
            --waittime)
            WAITTIME="$2"
            shift
            shift
            ;;
            --backend_loglevel)
            BACKENDLOGLEVEL="$2"
            shift
            shift
            ;;
            --backendhandler)
            BACKENDHANDLER="$2"
            shift
            shift
            ;;
            --backend)
            BACKEND="$2"
            shift
            shift
            ;;
            --topology_file)
            TOPOLOGYFILE="$2"
            shift
            shift
            ;;
            --noisy_qubits)
            NOISYQUBITS="$2"
            shift
            shift
            ;;
            --t1)
            T1="$2"
            shift
            shift
            ;;
            --frontend_loglevel)
            FRONTENDLOGLEVEL="$2"
            shift
            shift
            ;;
            *)
            echo "Unknown argument ${key}"
            exit 1
        esac
    done

    python3 "$simulaqron_path/configFiles.py" --nrnodes "${NRNODES}" --topology "${TOPOLOGY}" --nodes "${NODES}" \
                                    --maxqubits_per_node "${MAXQUBITSPERNODE}" --maxregisters_per_node "${MAXREGISTERSPERNODE}" \
                                    --waittime "${WAITTIME}" --backend_loglevel "${BACKENDLOGLEVEL}" \
                                    --backendhandler "${BACKENDHANDLER}" --backend "${BACKEND}" \
                                    --topology_file "${TOPOLOGYFILE}" --noisy_qubits "${NOISYQUBITS}" \
                                    --t1 "${T1}" --frontend_loglevel "${FRONTENDLOGLEVEL}"

    # We call this script again, without arguments, to use the newly created config-files
    sh "$simulaqron_path/run/startAll.sh"
fi

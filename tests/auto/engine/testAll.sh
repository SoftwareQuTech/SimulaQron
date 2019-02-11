#!/bin/bash

# Get the path to the SimulaQron folder
this_file_path=$0
this_folder_path=$(dirname "${this_file_path}")
simulaqron_path=$(${this_folder_path}/../../../toolbox/get_simulaqron_path.py)

while [ "$#" -gt 0 ]; do
    key="$1"
    case $key in
        --quick)
        QUICK="y"
        shift
        ;;
        --full)
        FULL="y"
        shift
        ;;
        --qutip)
        BACKEND="qutip"
        shift
        ;;
        --projectq)
        BACKEND="projectq"
        shift
        ;;
        --stabilizer)
        BACKEND="stabilizer"
        shift
        ;;
        *)
        echo "Unknown argument ${key}"
        exit 1
    esac
done

BACKEND=${BACKEND:-"projectq"} #If not set, use projectq backend

echo "Starting tests (using $BACKEND as backend)"
sh "$simulaqron_path"/run/startAll.sh -nd "Alice Bob Charlie" --backend "$BACKEND" &
sleep 1s
echo "Started SimulaQron server"

if [ "$BACKEND" = "projectq" ]; then
    python3 test_projectQEngine.py
elif [ "$BACKEND" = "qutip" ]; then
    python3 test_qutipEngine.py
elif [ "$BACKEND" = "stabilizer" ]; then
    python3 test_stabilizerEngine.py
fi

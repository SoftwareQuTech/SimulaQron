#!/bin/bash

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
        *)
        echo "Unknown argument ${key}"
        exit 1
    esac
done

BACKEND=${BACKEND:-"projectq"} #If not set, use projectq backend

echo "Starting SimulaQron server"
sh "$NETSIM"/run/startAll.sh -nd "Alice Bob Charlie" --backend "$BACKEND" &
sleep 1s
echo "Started SimulaQron server"

if [ "$BACKEND" = "projectq" ]; then
    python test_projectQEngine.py
elif [ "$BACKEND" = "qutip" ]; then
    python test_qutipEngine.py
fi

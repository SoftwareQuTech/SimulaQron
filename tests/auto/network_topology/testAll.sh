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

echo "Starting SimulaQron sever (restricted topology)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice Bob Charlie" -tp "path" --backend "$BACKEND" &
sleep 1s
echo "Started SimulaQron sever (restricted topology)"
python "${NETSIM}/tests/auto/network_topology/test_restricted_topology.py"

echo "Starting SimulaQron sever (default settings)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice Bob Charlie David Eve" --backend "$BACKEND" &
sleep 1s
echo "Started SimulaQron sever (default settings)"
python "${NETSIM}/tests/auto/network_topology/test_default_topology.py"

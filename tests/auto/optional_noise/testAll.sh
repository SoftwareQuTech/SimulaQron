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

if [ "$QUICK" = y ]; then
    if [ "$FULL" = y ]; then
        echo "Cannot specify both --quick and --full"
        exit 1
    else
        echo "Since --quick is specified we skip tests of optional noise."
        exit 1
    fi
fi

echo "Starting SimulaQron sever (noisy setting)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice" --noisy_qubits "True" --t1 "0.0001"
sleep 1s
echo "Started SimulaQron sever (noise setting)"
python "${NETSIM}/tests/auto/optional_noise/test_optional_noise.py"

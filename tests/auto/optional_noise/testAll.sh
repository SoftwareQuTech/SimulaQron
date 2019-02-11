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

if [ "$QUICK" = y ]; then
    if [ "$FULL" = y ]; then
        echo "Cannot specify both --quick and --full"
        exit 1
    else
        echo "Since --quick is specified we skip tests of optional noise."
        exit 1
    fi
fi

echo "Starting SimulaQron server (noisy setting and using $BACKEND as backend))"
sh "$simulaqron_path/run/startAll.sh" -nd "Alice" --noisy_qubits "True" --t1 "0.0001" --backend "$BACKEND"
sleep 1s
echo "Started SimulaQron server (noise setting)"
python3 "$simulaqron_path/tests/auto/optional_noise/test_optional_noise.py"

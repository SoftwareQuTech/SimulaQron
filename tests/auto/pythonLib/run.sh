#!/bin/sh

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
        *)
        echo "Unknown argument ${key}"
        exit 1
    esac
done

if [ "$QUICK" = y ]; then
    if [ "$FULL" = y ]; then
        echo "Cannot specify both --quick and --full"
        exit 1
    else
        echo "Since --quick is specified we skip tests doing tomography (tests of gates)."
        python3 test_context.py
        python3 test_other.py
        python3 test_sequence.py
        python3 test_maxQubits.py
    fi
else
    python3 test_context.py
    python3 test_single_qubit.py
    python3 test_two_qubit.py
    python3 test_other.py
    python3 test_factory_gates.py
    python3 test_factory_other.py
    python3 test_sequence.py
    python3 test_maxQubits.py
fi

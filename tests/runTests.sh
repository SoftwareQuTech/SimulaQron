#!/usr/bin/env sh
ALL_PIDS=$(ps aux | grep python | grep -E "Test|setup|start" | awk {'print $2'})
if [ "$ALL_PIDS" != "" ]
then
        kill -9 $ALL_PIDS
fi

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

echo "Starting tests (using $BACKEND as backend)"
cd "$NETSIM"/tests/auto

if [ "$FULL" = "y" ]; then
    if [ "$BACKEND" = "qutip" ]; then
        sh testAll.sh --full --qutip
    else
        sh testAll.sh --full --projectq
    fi
else
    if [ "$BACKEND" = "qutip" ]; then
        sh testAll.sh --quick --qutip
    else
        sh testAll.sh --quick --projectq
    fi
fi

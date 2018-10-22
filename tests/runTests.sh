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
cd "$NETSIM"/tests/auto

if [ "$FULL" = "y" ]; then
    if [ "$BACKEND" = "qutip" ]; then
        sh testAll.sh --full --qutip
    elif [ "$BACKEND" = "projectq" ]; then
        sh testAll.sh --full --projectq
    elif [ "$BACKEND" = "stabilizer" ]; then
        sh testAll.sh --full --stabilizer
    else
        echo "Unknown backend $BACKEND"
    fi
else
    if [ "$BACKEND" = "qutip" ]; then
        sh testAll.sh --quick --qutip
    elif [ "$BACKEND" = "projectq" ]; then
        sh testAll.sh --quick --projectq
    elif [ "$BACKEND" = "stabilizer" ]; then
        sh testAll.sh --quick --stabilizer
    else
        echo "Unknown backend $BACKEND"
    fi
fi

echo "Done with testing, killing the SimulaQron server"
ALL_PIDS=$(ps aux | grep python | grep -E "Test|setup|start" | awk {'print $2'})
if [ "$ALL_PIDS" != "" ]
then
        kill -9 $ALL_PIDS
fi

# Reset to default settins
rm "${NETSIM}/config/settings.ini"
python "${NETSIM}/settings.py"


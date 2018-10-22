#!/usr/bin/env sh
TEST_PIDS=$(ps aux | grep python | grep -E "test_" | awk {'print $2'})
if [ "$TEST_PIDS" != "" ]
then
        kill -9 $TEST_PIDS
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

rm "${NETSIM}/config/settings.ini"

echo "Starting SimulaQron sever"
sh "${NETSIM}/run/startAll.sh" -nd "Alice Bob Charlie David Eve" --backend "$BACKEND" &
sleep 1s
echo "Started SimulaQron sever"

if [ "$QUICK" = "y" ]; then
    sh run.sh --quick
elif [ "$FULL" = "y" ]; then
    sh run.sh --full
fi

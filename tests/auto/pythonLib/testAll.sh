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

rm "${NETSIM}/config/settings.ini"

echo "Starting SimulaQron server (using $BACKEND as backend)"
sh "${NETSIM}/run/startAll.sh" -nd "Alice Bob Charlie David Eve" --backend "$BACKEND" --backend_loglevel critical --frontend_loglevel critical &
sleep 1s
echo "Started SimulaQron server"

if [ "$FULL" = "y" ]; then
    sh run.sh --full
else
    sh run.sh --quick
fi


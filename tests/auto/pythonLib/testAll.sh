#!/usr/bin/env sh
TEST_PIDS=$(ps aux | grep python | grep -E "test_" | awk {'print $2'})
if [ "$TEST_PIDS" != "" ]
then
        kill -9 $TEST_PIDS
fi

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

rm "${simulaqron_path}/config/settings.ini"

echo "Starting SimulaQron server (using $BACKEND as backend)"
sh "${simulaqron_path}/run/startAll.sh" -nd "Alice Bob Charlie David Eve" --backend "$BACKEND" --backend_loglevel critical --frontend_loglevel critical &
sleep 1s
echo "Started SimulaQron server"

if [ "$FULL" = "y" ]; then
    sh run.sh --full
else
    sh run.sh --quick
fi

#!/usr/bin/env bash
ALL_PIDS=$(ps aux | grep python | grep -E "Test|setup|start" | awk {'print $2'})
if [ "$ALL_PIDS" != "" ]
then
        kill -9 $ALL_PIDS
fi

# Get the path to the SimulaQron folder
this_file_path=$0
this_folder_path=$(dirname "${this_file_path}")
simulaqron_path=$(${this_folder_path}/../simulaqron/toolbox/get_simulaqron_path.py)

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
 cd "$simulaqron_path"/tests/auto

 if [ "$FULL" = "y" ]; then
     if [ "$BACKEND" = "qutip" ]; then
         has_qutip=$(${simulaqron_path}/simulqron/toolbox/has_module.py qutip)
         if [ "$has_qutip" = "Y" ]; then
             sh testAll.sh --full --qutip
         else
             echo "Cannot run tests for qutip backend if qutip is not installed as a module"
         fi
     elif [ "$BACKEND" = "projectq" ]; then
         has_projectq=$(${simulaqron_path}/simulqron/toolbox/has_module.py projectq)
         if [ "$has_projectq" = "Y" ]; then
             sh testAll.sh --full --projectq
         else
             echo "Cannot run tests for projectq backend if projectq is not installed as a module"
         fi
     elif [ "$BACKEND" = "stabilizer" ]; then
         sh testAll.sh --full --stabilizer
     else
         echo "Unknown backend $BACKEND"
     fi
 else
     if [ "$BACKEND" = "qutip" ]; then
         has_qutip=$(${simulaqron_path}/simulaqron/toolbox/has_module.py qutip)
         if [ "$has_qutip" = "Y" ]; then
             sh testAll.sh --quick --qutip
         else
             echo "Cannot run tests for qutip backend if qutip is not installed as a module"
         fi
     elif [ "$BACKEND" = "projectq" ]; then
         has_projectq=$(${simulaqron_path}/simulaqron/toolbox/has_module.py projectq)
         if [ "$has_projectq" = "Y" ]; then
             sh testAll.sh --quick --projectq
         else
             echo "Cannot run tests for projectq backend if projectq is not installed as a module"
         fi
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
rm "${simulaqron_path}/config/settings.ini"
python3 "${simulaqron_path}/simulaqron/settings.py"

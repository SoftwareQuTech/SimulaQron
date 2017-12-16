

# start the node Alice, Bob

cd "$NETSIM"/run

python startCQC.py Alice &
python startCQC.py Bob &
python startCQC.py Charlie &
python startCQC.py David &
python startCQC.py Eve &


# start the nodes ['Alice', 'Bob', 'Charlie', 'David', 'Eve']

cd "$NETSIM"/run

python startNode.py Alice &
python startNode.py Bob &
python startNode.py Charlie &
python startNode.py David &
python startNode.py Eve &

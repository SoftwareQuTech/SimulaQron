# start the node Alice, Bob and Charlie 

cd "$NETSIM"/run

python startNode.py Alice $1 &
python startNode.py Bob $1 &
python startNode.py Charlie $1 &
python startNode.py David $1 &
python startNode.py Eve $1 &

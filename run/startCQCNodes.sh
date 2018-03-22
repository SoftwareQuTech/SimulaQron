

# start the node Alice, Bob

cd "$NETSIM"/run


python startCQC.py Alice $1 $2 $3&
python startCQC.py Bob $1 $2 $3&
python startCQC.py Charlie $1 $2 $3&
python startCQC.py David $1 $2 $3&
python startCQC.py Eve $1 $2 $3&


cd tests/auto
python testEngine.py
cd ../manual
python serverTest.py
cd merges/remoteAtoB
sh doNew.sh
cd ../remoteBtoA
sh doNew.sh
cd ../bothRemote
sh doNew.sh
cd ../../../../examples/teleport
sh doNew.sh
cd ../extendGHZ
sh doNew.sh
cd ../sendEPRDR
sh doNew.sh





Distributed version of the teleport example, using simple NetQASM code both for Alice and Bob.

How to run this example:

1. First of all, make sure you are not already running existing simulaqron programs. You can run

simulaqron stop
sh terminate.sh

which should get rid of all things running for the teleport example itself. If you want to be a bit
more radical and confident you are not running other things to preserve you can run:

simulaqron stop
pkill -9 python

This will kill ALL python processes run by you so beware.

If you have a debugging enabled, you may also wish to wipe old log files by running

rm /tmp/simulaqron*


Now you should have a clear slate!

2. Now you can run this example:

First, we want to start the simulaqron virtual node backend and the NetQASM frontend your apps will their NetQASM subroutines to. 


** Single Machine
If you are running everything on the same machine, first we start the simulaqron backend by typing

simulaqron start --node Alice,Bob

This needs to be done only once. Now type

sh run.sh

There is no need to restart the simulaqron backend again if you want to re-run your example. 

** Multiple machines

If you are starting on two different machines run:

simulaqron start --node Alice
simulaqron start --node Bob

on the machines you will use as Alice and Bob respectively. Again this needs to be run only once.

Now you can run:
on Bob:
python teleport-bob.py

on Alice:
python teleport-alice.py

The code assumes you start Bob before starting Alice. Using your knowledge of network programming
from our ping pong example - do you have an idea to make this more robust?





Getting started 
===============

---------------
Installation
---------------

SimulaQron requires `Python 3 <https://python.org/>`_ , `Twisted <http://twistedmatrix.com/trac/>`_ and `QuTip <http://qutip.org/>`_ 
Assuming you have python 3 etc already installed already, do::

	pip install twisted 
	pip install service_identity
	pip install qutip

For detailed instructions on how to install QuTip and Twisted, please refer to their respective installations instructions. You will then 
need to set the following environment variables in order to execute the code. I am assuming here
you use bash (e.g., standard on OSX or the GIT Bash install on Windows 10), otherwise set the same variables using your favorite shell.::

	export NETSIM=yourPath/SimulaQron
	export PYTHONPATH=yourPath:$PYTHONPATH

where yourPath is the directory containing SimulaQron.

.. You may verify the successful installation of the back engine itself, by executing::

.. 	python tests/auto/testEngine.py 


------------------------
Testing a simple example
------------------------

Before delving into how to write any program yourself, let's first simply run one of the existing examples when programming SimulaQron through the Python library (see :doc:`ExamplespythonLib`).
Remember from the Overview that SimulaQron has two parts: the first are the virtual node servers that act simulate the hardware at each node as well as the quantum communication between them in a transparent manner.
The second are the applications themselves which can be written in two ways, the direct way is to use the native mode using the Python Twisted framework connecting to the virtual node servers, see :doc:`ExamplesDirect`.
Another way is the use the provided Python library that calls the virtual nodes by making use of the classical/quantum combiner interface.
We will here illustrate how to use SimulaQron with the Python library.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Starting the virtual node servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A test configuration of virtual node servers will start 3 nodes, Alice, Bob and Charlie on your local computers. You may do so by executing::

	sh run/startVNodes.sh

Let us now see in detail what happens when you execute this example script. 
The configuration for the test network is read from config/virtualNodes.cfg. This file defines which virtualNodes to start up and what their names are. The example runs them all locally, but you can as well run them on remote hosts by using one such file on each host.

For the example, this file is::

	# Network configuration file
	# 
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]
	#

	Alice, localhost, 8801
	Bob, localhost, 8802
	Charlie, localhost, 8803

Provided a configuration in the file above, you can run::
	python run/startNode.py Alice & 

To start the virtual node for Alice. The script startVNodes.sh then simply starts any number of desired virtual nodes::

	# startVNodes.sh - start the node Alice, Bob and Charlie 

	cd "$NETSIM"/run
	python startNode.py Alice &
	python startNode.py Bob &
	python startNode.py Charlie &

Provided the virtual nodes started successfully you now have a network of 3 simulated quantum nodes that accept connections on the ports indicated above to allow an application program to access qubits on the virtual node servers. The 3 virtual nodes have also established connections to each other in order to exchange simulated quantum traffic. 

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Starting the CQC servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similarly to the virtual nodes we also need to start the CQC servers, which provide the possibility to talk to SimulaQron using the CQC interface.
A test configuration of CQC servers will start 3 nodes, Alice, Bob and Charlie on your local computers. You may do so by executing::

	sh run/startCQCNodes.sh

The configuration for the CQC network is read from config/CQCNodes.cfg. This file defines which virtualNodes to start up and what their names are.
**Note that the names for the virtual nodes and the CQC servers have to be the same at the moment.**

For the example, this file is::

	# Network configuration file
	# 
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]
	#

	Alice, localhost, 8801
	Bob, localhost, 8802
	Charlie, localhost, 8803

The script startCQCNodes.sh starts any number of desired CQC servers::

	# startCQCNodes.sh - start the node Alice, Bob and Charlie 

	cd "$NETSIM"/run
	python startCQC.py Alice &
	python startCQC.py Bob &
	python startCQC.py Charlie &

Provided the CQC servers started successfully you now have a network of 3 simulated quantum nodes that accept connections on the ports indicated above and takes messages specified by the CQC header.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Running automated test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before turning to an actual protocol it is a good idea to run some tests to see that everything is working.
It is a good idea to open a new terminal at this point, since the outputs will otherwise be hidden by the debugging information from the virtual nodes and CQC servers.
Do not forget to set the environment variables.
To run the test in the new terminal just type::

    sh tests/runAll.sh

Recall that some of these tests use quantum tomography and are inherently probabilistic. If one of the tests therefore fails, try to run it again and see if the error persists.

^^^^^^^^^^^^^^^^^^^
Running a protocol
^^^^^^^^^^^^^^^^^^^

Having started the virtual quantum nodes, let us now run a simple test application, which already illustrates some of the aspects in realizing protocols.
Our objective will be to realize the following protocol which will generate 1 shared random bit between Alice and Bob. Evidently, there would be classical means to achieve this trivial task chosen for illustration. 

* Alice generates 1 EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`

* She sends qubit :math:`B` to Bob.

* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`. 

Before seeing how this example works, let us again simply run the code::

	cd examples/cqc/pythonLib/corrRNG
	sh doNew.sh

Next to a considerable about of debugging information, you should be seeing the following two lines::

	App Alice: Measurement outcome is: 0/1
	App Bob: Measurement outcome is: 0/1

Note that the order of these two lines may differ, as it does not matter who measures first. So what is actually going on here ? Let us first look at how we will realize the example by making an additional step (3) explicit:

* Alice generates 1 EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`

* She sends qubit :math:`B` to Bob.

* Bob is informed of the identifier of the qubit and is informed it has arrived. 

* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`. 

While the task we want to realize here is completely trivial, the addition of step 3 does however already highlight a range of choices on how to realize step 3 and the need to find good abstractions to allow easy application development. 
One way to realize step 3 would be to hardwire Bobs measurement: if the hardware can identify the correct qubit from Alice, then we could instruct it to measure it immediately without asking for a notification from Alice. It is clear that in a network that is a bit larger than our tiny three node setup, identifying the right setup requires a link between the underlying qubits and classical control information: this is the objective of the classical/quantum combiner.

The first thing that happens if we execute the script doNew.sh is that after some setting up it will call run.sh, executing::

	#!/bin/sh

	python aliceTest.py
	python bobTest.py &

Let us now look at the programs for Alice and Bob.
We first initialize an object of the class ``CQCConnection`` which will do all the communication to the virtual through the CQC interface.
Qubits can then be created by initializing a qubit-object, which takes a ``CQCConnection`` as an input.
On these qubits operations can be applied and they can also be sent to other nodes in the network by use of the ``CQCConnection``.
The full code in aliceTest.py is::

	# Initialize the connection
	Alice=CQCConnection("Alice")

	# Create qubits
	q1=qubit(Alice)
	q2=qubit(Alice)

	# Create Bell-pair
	q1.H()
	q1.cnot(q2)

	#Send second qubit to Bob
	Alice.sendQubit(q2,"Bob")

	# Measure qubit
	m=q1.measure()
	to_print="App {}: Measurement outcome is: {}".format(Alice.name,m)
	print("|"+"-"*(len(to_print)+2)+"|")
	print("| "+to_print+" |")
	print("|"+"-"*(len(to_print)+2)+"|")

	# Stop the connections
	Alice.close()

Similarly the code in bobTest.py read::

	# Initialize the connection
	Bob=CQCConnection("Bob")

	# Receive qubit
	q=Bob.recvQubit()

	# Measure qubit
	m=q.measure()
	to_print="App {}: Measurement outcome is: {}".format(Bob.name,m)
	print("|"+"-"*(len(to_print)+2)+"|")
	print("| "+to_print+" |")
	print("|"+"-"*(len(to_print)+2)+"|")

	# Stop the connection
	Bob.close()

For further examples, see the examples/ folder.

^^^^^^^^^^^^^^^^^^^^^^^^
Logging and debug output
^^^^^^^^^^^^^^^^^^^^^^^^

In this Pre Beta, the default is for all code - the SimulaQron Backend, the CQC Backend, and any examples - to produce very detailed logging information. You may set the detail of this output using the Python logging module, by setting logging.DEBUG, logging.ERROR, etc depending on your desired level of detail. The default everywhere is full debug output, ile ::

	logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)


Distribute a GHZ-state
======================

Here we consider an example with three parties, Alice, Bob and Charlie.
Alice and Bob will make an EPR-pair which Bob will extend to Charlie, such that they share a three-partite GHZ-state.

------------
The protocol
------------

Alice, Bob and Charlie will perform the following operations

#. Alice and Bob creates a shared EPR pair on qubits :math:`q_A` and :math:`q_B`.

#. Bob creates a fresh qubit :math:`q_C`.

#. Bob performs a CNOT with :math:`q_B` as control and :math:`q_C` as target.

#. Bob sends his qubit to Charlie.

They will all measure their corresponing qubits in the standard basis and print their results.

-----------
Setting up
-----------

We will run everything locally (localhost) using the standard virtualNodes.cfg file found in config that define the virtual quantum nodes run in the background to simulate the quantum hardware::

	# Network configuration file
	#
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]

	Alice, localhost, 8801
	Bob, localhost, 8802
	Charlie, localhost, 8803
	David, localhost, 8804

Similarly we use the cqcNodes.cfg file that define the network of CQC nodes that provides an way to talk to SimulaQron through the CQC interface::

	# Network configuration file
	# 
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]
	#

	Alice, localhost, 8821
	Bob, localhost, 8822
	Charlie, localhost, 8823
	David, localhost, 8824

-----------------
Programming Alice
-----------------

Here we program what Alice should do using the python library::

	from SimulaQron.general.hostConfig import *
	from SimulaQron.cqc.backend.cqcHeader import *
	from SimulaQron.cqc.pythonLib.cqc import *


	#####################################################################################################
	#
	# main
	#
	def main():

		# Initialize the connection
		Alice=CQCConnection("Alice")

		# Make an EPR pair with Bob
		qA=Alice.createEPR("Bob")

		# Measure qubit
		m=qA.measure()
		to_print="App {}: Measurement outcome is: {}".format(Alice.name,m)
		print("|"+"-"*(len(to_print)+2)+"|")
		print("| "+to_print+" |")
		print("|"+"-"*(len(to_print)+2)+"|")

		# Stop the connections
		Alice.close()


	##################################################################################################
	main()

-----------------
Programming Bob
-----------------

Here we program what Bob should do using the python library::

	from SimulaQron.general.hostConfig import *
	from SimulaQron.cqc.backend.cqcHeader import *
	from SimulaQron.cqc.pythonLib.cqc import *


	#####################################################################################################
	#
	# main
	#
	def main():

		# Initialize the connection
		Bob=CQCConnection("Bob")

		# Make an EPR pair with Alice
		qB=Bob.createEPR("Alice")

		# Create a fresh qubit
		qC=qubit(Bob)

		# Entangle the new qubit
		qB.cnot(qC)

		# Send qubit to Charlie
		Bob.sendQubit(qC,"Charlie")

		# Measure qubit
		m=qB.measure()
		to_print="App {}: Measurement outcome is: {}".format(Bob.name,m)
		print("|"+"-"*(len(to_print)+2)+"|")
		print("| "+to_print+" |")
		print("|"+"-"*(len(to_print)+2)+"|")

		# Stop the connection
		Bob.close()


	##################################################################################################
	main()

--------------------
Programming Charlie
--------------------

Here we program what Charlie should do using the python library::

	from SimulaQron.general.hostConfig import *
	from SimulaQron.cqc.backend.cqcHeader import *
	from SimulaQron.cqc.pythonLib.cqc import *


	#####################################################################################################
	#
	# main
	#
	def main():

		# Initialize the connection
		Charlie=CQCConnection("Charlie")

		# Receive qubit
		qC=Charlie.recvQubit()

		# Measure qubit
		m=qC.measure()
		to_print="App {}: Measurement outcome is: {}".format(Charlie.name,m)
		print("|"+"-"*(len(to_print)+2)+"|")
		print("| "+to_print+" |")
		print("|"+"-"*(len(to_print)+2)+"|")

		# Stop the connection
		Charlie.close()


	##################################################################################################
	main()

--------
Starting
--------

We first start the virtual quantum node backend, by executing::

	cd "$NETSIM"/run
	python startNode.py Alice &
	python startNode.py Bob &
	python startNode.py David &
	python startNode.py Charlie &

where $NETSIM is the environment variable defining the SimulaQron directory as outlined in :doc:`GettingStarted`.

We also start up the CQC servers::

	cd "$NETSIM"/cqc/backend
	python setupCQC.py Alice &
	python setupCQC.py Bob &
	python setupCQC.py Charlie &

We then start up the programs for the parties themselves. These files contain the code above for the corresponding host::

	python aliceTest.py &
	python bobTest.py &
	python charlieTest.py &

Teleporting a Qubit
===================

Let's now consider a very simple protocol, in which Alice first generates an EPR pair with Bob, and then teleports a qubit to Bob. To program it in SimulaQron's native mode, we will use the template described in :doc:`NativeModeTemplate`.  

------------
The protocol
------------

For completness, let's briefly recap the protocol:

* For generating an EPR pair with Bob, Alice proceeds as follows:

	#. Alice prepares two qubits in the state :math:`|0\rangle_A |0\rangle_B`

	#. Alice applies a Hadamard transform to qubit A, giving :math:`|+\rangle_A |0\rangle_B`

	#. Alice applies a CNOT on qubits A and B, where qubit A is the control and B is the target, giving the state :math:`\frac{1}{\sqrt{2}}(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B)`

	#. Alice sends qubit B to Bob

* Alice then teleports qubit q1 to Bob using the EPR pair:

	#. Alice applies a CNOT between q1 and qubit A, where q1 is the control and A is the target.

	#. Alice applies a Hadamard to qubit q1.

	#. Alice measures qubits q1 and A to obtain outcomes a and b.

	#. She sends a and b to Bob, who applies the correction unitary :math:`Z^a X^b`

-----------
Setting up
-----------

We will run everything locally (localhost) using the standard virtualNodes.cfg file found in conig that define the virtual quantum nodes run in the background to simulate the quantum hardware::

	# Network configuration file
	#
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]

	Alice, localhost, 8801
	Bob, localhost, 8802

As we can see from the proocol above, only Alice communicates to Bob for which we will run a client at Alice' and a server at Bob's. Since we run everything locally, we may thus use for the configuration file classicalNet.cfg::

	# Network configuration file
	# 
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]
	#

	Bob, localhost, 8812

Let us now provide the actual program code for both Alice and Bob.

-----------------
Programming Alice
-----------------

Since Alice acts as a client, we will only need to fill in runClientNode. This gives::

	#####################################################################################################
	#
	# runClientNode
	#
	# This will be run on the local node if all communication links are set up (to the virtual node
	# quantum backend, as well as the nodes in the classical communication network), and the local classical
	# communication server is running (if applicable).
	#
	@inlineCallbacks
	def runClientNode(qReg, virtRoot, myName, classicalNet):
		"""
		Code to execute for the local client node. Called if all connections are established.
	
		Arguments
		qReg		quantum register (twisted object supporting remote method calls)
		virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
		myName		name of this node (string)
		classicalNet	servers in the classical communication network (dictionary of hosts)
		"""

		logging.debug("LOCAL %s: Runing client side program.",myName)

		# Create 3 qubits
		q1 = yield virtRoot.callRemote("new_qubit_inreg",qReg)
		qA = yield virtRoot.callRemote("new_qubit_inreg",qReg)
		qB = yield virtRoot.callRemote("new_qubit_inreg",qReg)

		# Prepare the first one in the |-> state
		yield q1.callRemote("apply_H")

		# For information purposes, let's print the state of that qubit
		(R,I) = yield q1.callRemote("get_qubit")
		print("Qubit to be teleported is: ", assemble_qubit(R,I))

		# Put qubits A and B in an EPR state
		yield qA.callRemote("apply_H")
		yield qA.callRemote("cnot_onto",qB)

		# Send qubit B to Bob
		# Instruct the virtual node to transfer the qubit
		remoteNum = yield virtRoot.callRemote("send_qubit",qB, "Bob")
		logging.debug("LOCAL %s: Remote qubit is %d.",myName, remoteNum)

		# Apply the local teleportation operations
		yield q1.callRemote("cnot_onto",qA)	
		yield q1.callRemote("apply_H")

		a = yield q1.callRemote("measure")
		b = yield qA.callRemote("measure")
		logging.debug("LOCAL %s: Correction info is a=%d, b=%d.",myName, a, b)

		# Tell Bob the number of the virtual qubit so the can use it locally
		bob = classicalNet.hostDict["Bob"]
		yield bob.root.callRemote("recover_teleport", a, b, remoteNum)

		reactor.stop()

---------------
Programming Bob
---------------

Let us now program the code for Bob. Since he only acts as a server on the classical network, it is enough to edit the localNode portion of the template. Alice calls recover_teleport to convey the classical measurement outcomes, as well as the identifier of the virtual qubit. Bob first asks his local virtual quantum node for a reference
for the qubit with that identfier and then processes the relevant quantum instructions to recover the qubit. We print the density matrix of the qubit at the end for illustration.::


	#####################################################################################################
	#
	# localNode
	#
	# This will be run if the local node acts as a server on the classical communication network,
	# accepting remote method calls from the other nodes. 

	class localNode(pb.Root):
	
		def __init__(self, node, classicalNet):
	
			self.node = node
			self.classicalNet = classicalNet

			self.virtRoot = None
			self.qReg = None

		def set_virtual_node(self, virtRoot):
			self.virtRoot = virtRoot

		def set_virtual_reg(self, qReg):
			self.qReg = qReg

		def remote_test(self):
			return "Tested!"

		# This can be called by Alice to tell Bob where to get the qubit and what corrections to apply
		@inlineCallbacks
		def remote_recover_teleport(self, a, b, virtualNum):
			"""
			Recover the qubit from teleportation.
		
			Arguments
			a,b		received measurement outcomes from Alice
			virtualNum	number of the virtual qubit corresponding to the EPR pair received
			"""

			logging.debug("LOCAL %s: Getting reference to qubit number %d.",self.node.name, virtualNum)

			# Get the reference to Alice's qubit from the local virtual node
			eprB = yield self.virtRoot.callRemote("get_virtual_ref",virtualNum)

			# Apply the desired correction info
			logging.debug("LOCAL %s: Correction info is a=%d, b=%d.", self.node.name, a, b)
			if b == 1:
				yield eprB.callRemote("apply_X")
			if a == 1:	
				yield eprB.callRemote("apply_Z")

			# Just print the qubit we received
			(realRho, imagRho) = yield eprB.callRemote("get_qubit")
			rho = self.assemble_qubit(realRho, imagRho)

			print("Qubit is:", rho)

		def assemble_qubit(self, realM, imagM):
			"""
			Reconstitute the qubit as a qutip object from its real and imaginary components given as a list.
			We need this since Twisted PB does not support sending complex valued object natively.
			"""
			M = realM
			for s in range(len(M)):
				for t in range(len(M)):
					M[s][t] = realM[s][t] + 1j * imagM[s][t]
		
			return Qobj(M)

--------
Starting
--------

We first start the virtual quantum node backend, by executing::

	python3 simulaqron/run/startNode.py Alice &
	python3 simulaqron/run/startNode.py Bob &

We then start up the programs for Alice and Bob themselves. These will connect to the virtual quantum nodes, and execute the quantum commands and classical communication outlined above, in the same directory as we placed classicalNet.cfg::

	python3 bobTest.py &
	python3 aliceTest.py


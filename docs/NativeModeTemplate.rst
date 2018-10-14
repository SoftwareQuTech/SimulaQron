Template for programming in native mode
=======================================

In examples/nativeMode/template you will find a template that allows you to program relatively easily by filling in the relevant parts of the template. Let us now discuss this template in detail. 

#. The first step in programming your application protocol is to determine how many nodes are involved. For simplicity, let us here assume you only have two, called Alice and Bob. This will typically be obvious from the high level description of the quantum protocol that you are given. 

#. The next, and possibly less obvious step, is to determine how classical information is exchanged in the quantum protocol. That is, who sends classical messages to whom, at what time, and what actions are taken when those messages are received. Based on this, you need to decide which nodes run a server on the classical network, and which nodes may simply be a client program that connects to the servers to deliver messages. Let us here simply assume, Alice only sends information to Bob, who then acts upon the message received. In this case, we would make Alice a client and Bob a server. Note that one node can obviously fullfill both roles.

#. The template will look for a file called classicalNet.cfg in the local directory to determine who acts as a server and what that nodes address details are. An example, if only Bob acts as a server would be::

	# Network configuration file
	# 
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]
	#

	Bob, localhost, 8812

#. The next step is to check that on each network computer that you will run on, the global configuration file starting the virtual quantum nodes is set up correctly. See :doc:`GettingStarted` on how to perform such a configuration and start the local quantum virtual node backends.

#. Now copy nodeTest.py to a separate file for each node. In our example above where we just have Alice (client only) and Bob (server only), you would copy nodeTest to aliceTest.py and bobTest.py.

---------------------
Programming a client
---------------------

Let us now see how we would program a protocol in which a node acts as a client. In our example above this would be Alice, requiring you to edit aliceTest.py. The template code already includes everything necessary to connect to the local virtual quantum node backend, so all you have to do is to write that classical client program communicating with Bob (and possibly directing the local quantum hardware simulated by the virtual node to perform certain tasks). Specifically, you would add your code at the indicated place below::


	#####################################################################################################
	#
	# runClientNode
	#
	# This will be run on the local node if all communication links are set up (to the virtual node
	# quantum backend, as well as the nodes in the classical communication network), and the local classical
	# communication server is running (if applicable).
	#
	#@inlineCallbacks
	def runClientNode(qReg, virtRoot, myName, classicalNet):
        	"""
        	Code to execute for the local client node. Called if all connections are established.
        
        	Arguments
        	qReg            quantum register (twisted object supporting remote method calls)
        	virtRoot        virtual quantum ndoe (twisted object supporting remote method calls)
        	myName          name of this node (string)
        	classicalNet    servers in the classical communication network (dictionary of hosts)
        	"""

        	logging.debug("LOCAL %s: Runing client side program.",myName)

        	# Here the code to execute for Alice acting as a client
        	# Uncomment @inlineCallbacks above if you use yield statements

        	# Stop the server and client - you want to delete this if the nodes acts as a server
        	reactor.stop()

That's all. As a simple example, this code would correspond to the protocol where Alice creates a qubit in the :math:`|+\rangle` state and send it to Bob.::


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
        	qReg            quantum register (twisted object supporting remote method calls)
        	virtRoot        virtual quantum ndoe (twisted object supporting remote method calls)
        	myName          name of this node (string)
        	classicalNet    servers in the classical communication network (dictionary of hosts)
        	"""

        	logging.debug("LOCAL %s: Runing client side program.",myName)

		# Prepare a new qubit
		qA = yield virtRoot.callRemote("new_qubit_inreg",qReg)

		# Apply the Hadamard transform
        	yield qA.callRemote("apply_H")

        	# Instruct the virtual node to transfer the qubit to Bob
        	remoteNum = yield virtRoot.callRemote("send_qubit",qB, "Bob")

      		# Tell Bob to process the qubit
        	bob = classicalNet.hostDict["Bob"]
        	yield bob.root.callRemote("tell_bob", remoteNum)

        	# Stop the server and client - you want to delete this if the nodes acts as a server
        	reactor.stop()



--------------------
Programming a server
--------------------

Let us now have a look on how to program a node that acts as a server on the classical network. In our example above this would be Bob, requiring you to edit bobTest.py. The template code already includes everything necessary to connect to the local virtual quantum node backend, so all you have to do is to write that classical server program communicating with Alice (and possibly directing the local quantum hardware simulated by the virtual node to perform certain tasks). Specifically, you would add your code at the indicated place below::


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

        	# This can be called by Alice (or other clients on the classical network) to inform Bob 
        	# of an event. Your code goes here.
        	# @inlineCallbacks
        	def remote_tell_bob(self, someInfo):

                # Uncomment inlineCallbacks if you use yield here
                # Also remove the pass statement when executing actual code
                pass

Evidently, it depends on the program what actions Bob would perform precisely. Here, let us just assume Bob receives the qubit and applies Pauli X::

        # This can be called by Alice to tell Bob where to get the qubit and what corrections to apply
        @inlineCallbacks
        def remote_tell_bob (self, virtualNum):
                """
		Apply X  

                Arguments
                virtualNum      number of the virtual qubit corresponding to the qubit received
                """

                logging.debug("LOCAL %s: Getting reference to qubit number %d.",self.node.name, virtualNum)

		# Get a reference to the qubit from the local virtual quantum node.
                qB = yield self.virtRoot.callRemote("get_virtual_ref",virtualNum)

		# Apply Pauli X
                yield qB.callRemote("apply_X")



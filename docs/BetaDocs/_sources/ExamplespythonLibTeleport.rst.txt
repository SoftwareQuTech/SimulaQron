Teleport
========

Here we consider an example with two parties, Alice and Bob.
Alice will teleport a state (in this case the :math:`|+\rangle`-state) to Bob.

------------
The protocol
------------

Alice, Bob and Charlie will perform the following operations

#. Alice and Bob creates a shared EPR pair on qubits :math:`q_A` and :math:`q_B`.

#. Alice creates a qubit :math:`q` and puts it in some state (in this case :math:`|+\rangle`).

#. Alice performs the local teleportation operations, i.e. performs a CNOT with :math:`q` as control and :math:`q_A` as target and a Hadamard on :math:`q`.

#. Alice measures her two qubits and sends the measurement outcomes to Bob.

#. Bob receives the measurement outcomes from Alice and performs a Pauli operation depending on what they are.

In the end Bob measures the qubit :math:`q_B` which is now in the state of the teleported qubit and prints the outcome.

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

Since in this case Alice and Bob needs to communicate we also need to define an application network and we will use the standard appNodes.cfg file in config that defines this::


        # Network configuration file
        # 
        # For each host its informal name, as well as its location in the network must
        # be listed.
        #
        # [name], [hostname], [port number]
        #

        Alice, localhost, 8831
        Bob, localhost, 8832
        Charlie, localhost, 8833
        David, localhost, 8834

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

        # Create a qubit to teleport
        q=qubit(Alice)

        # Prepare the qubit to teleport in |+>
        q.H()

        # Apply the local teleportation operations
        q.cnot(qA)
        q.H()

        # Measure the qubits
        a=q.measure()
        b=qA.measure()
        to_print="App {}: Measurement outcomes are: a={}, b={}".format(Alice.name,a,b)
        print("|"+"-"*(len(to_print)+2)+"|")
        print("| "+to_print+" |")
        print("|"+"-"*(len(to_print)+2)+"|")

        # Send corrections to Bob
        Alice.sendClassical("Bob",[a,b])

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

                # Receive info about corrections
                Bob.startClassicalServer()
                data=Bob.recvClassical()
                message=list(data)
                a=message[0]
                b=message[1]

                # Apply corrections
                if b==1:
                        qB.X()
                if a==1:
                        qB.Z()

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

--------
Starting
--------

Start the virtual nodes and CQC servers as explained in :doc:`GettingStarted`.
We then start up the programs for the parties themselves. These files contain the code above for the corresponding host::

	python aliceTest.py &
	python bobTest.py &

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

We will run everything locally (localhost) using two nodes, Alice, Bob and Charlie. Start up the backend of the simulation by running::

    sh run/startAll.sh --nodes "Alice Bob Charlie"

The below example can then be executed when in the folder `examples/cqc/pythonLib/extendGHZ` typing::

    sh doNew.sh

which will execute the Python scripts `aliceTest.py`, `bobTest.py` and `charlieTest.py` containing the code below.

-----------------
Programming Alice
-----------------

Here we program what Alice should do using the python library::

	from SimulaQron.cqc.pythonLib.cqc import CQCConnection

	#####################################################################################################
	#
	# main
	#
	def main():

		# Initialize the connection
		with CQCConnection("Alice") as Alice:

            # Make an EPR pair with Bob
            qA=Alice.createEPR("Bob")

            # Measure qubit
            m=qA.measure()
            to_print="App {}: Measurement outcome is: {}".format(Alice.name,m)
            print("|"+"-"*(len(to_print)+2)+"|")
            print("| "+to_print+" |")
            print("|"+"-"*(len(to_print)+2)+"|")

	##################################################################################################
	main()

-----------------
Programming Bob
-----------------

Here we program what Bob should do using the python library::

	from SimulaQron.cqc.pythonLib.cqc import CQCConnection

	#####################################################################################################
	#
	# main
	#
	def main():

		# Initialize the connection
		with CQCConnection("Bob") as Bob:

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

	##################################################################################################
	main()

--------------------
Programming Charlie
--------------------

Here we program what Charlie should do using the python library::

	from SimulaQron.cqc.pythonLib.cqc import CQCConnection

	#####################################################################################################
	#
	# main
	#
	def main():

		# Initialize the connection
		with CQCConnection("Charlie") as Charlie:

            # Receive qubit
            qC=Charlie.recvQubit()

            # Measure qubit
            m=qC.measure()
            to_print="App {}: Measurement outcome is: {}".format(Charlie.name,m)
            print("|"+"-"*(len(to_print)+2)+"|")
            print("| "+to_print+" |")
            print("|"+"-"*(len(to_print)+2)+"|")

	##################################################################################################
	main()


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

We will run everything locally (localhost) using two nodes, Alice and Bob. Start up the backend of the simulation by running::

    sh run/startAll.sh --nodes "Alice Bob"

The below example can then be executed when in the folder `examples/cqc/pythonLib/teleport` typing::

    sh doNew.sh

which will execute the Python scripts `aliceTest.py` and `bobTest.py` containing the code below.

-----------------
Programming Alice
-----------------

Here we program what Alice should do using the python library::

        from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit

        #####################################################################################################
        #
        # main
        #
        def main():

            # Initialize the connection
            with CQCConnection("Alice") as Alice:

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

        ##################################################################################################
        main()

-----------------
Programming Bob
-----------------

Here we program what Bob should do using the python library::

        from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit

        #####################################################################################################
        #
        # main
        #
        def main():

                # Initialize the connection
                with CQCConnection("Bob") as Bob:

                    # Make an EPR pair with Alice
                    qB=Bob.recvEPR()

                    # Receive info about corrections
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

        ##################################################################################################
        main()


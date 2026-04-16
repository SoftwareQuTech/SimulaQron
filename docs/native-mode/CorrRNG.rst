Generate correlated randomness
==============================

.. note:: Native mode is the low-level Twisted interface. For new projects, the NetQASM SDK is recommended.
   See :doc:`New SDK Overview <../new-sdk/Overview>` and the :doc:`new SDK version of this example <../new-sdk/CorrRNG>`.

Having started the virtual quantum nodes, let us now run a simple test application, which already illustrates some of
the aspects in realizing protocols. Our objective will be to realize the following protocol which will generate 1
shared random bit between Alice and Bob. Evidently, there would be classical means to achieve this trivial task chosen
for illustration.

* Alice generates 1 EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form
  :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`
* She sends qubit :math:`B` to Bob.
* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`. 

Before seeing how this example works, let us again simply run the code::

    cd examples/native-mode/corrRNG
    bash doNew.sh

Next to a considerable about of debugging information, you should be seeing the following two lines::

    ALICE: My Random Number is  0/1
    BOB: My Random Number is  0/1

Note that the order of these two lines may differ, as it does not matter who measures first. So what is actually
going on here ? Let us first look at how we will realize the example by making an additional step (3) explicit:

* Alice generates 1 EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form
  :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`
* She sends qubit :math:`B` to Bob.
* Bob is informed of the identifier if the qubit and is informed it has arrived.
* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`. 

While the task we want to realize here is completely trivial, the addition of step 3 does however already highlight a
range of choices on how to realize step 3 and the need to find good abstractions to allow easy application development.
One way to realize step 3 would be to hardwire Bobs measurement: if the hardware can identify the correct qubit from
Alice, then we could instruct it to measure it immediately without asking for a notification from Alice.

This version simply allows a completely barebones access to the virtual nodes without implementing such convenient
abstractions in order to allow you to explore such possibilities. To this end, we will here actually implement the
following protocol for mere illustration purposes. We emphasize that this would be inefficient on a real quantum
network since it requires Bob to store his qubit until Alice's control message arrives, which can be a significant
delay causing the qubit to decohere in the meantime.

* Alice generates 1 EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form
  :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`
* She sends qubit :math:`B` to Bob.
* Alice sends Bob the correct identifier of the qubit, and tells him to measure it.
* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`. 

To realize this, we thus need not only the connection to the virtual quantum node servers, but Alice and Bob
themselves need to run a client/server to exchange classical control information. Before looking at the code, we
know that the setup of these servers is again determined by a configuration file, namely ``classicalNet.json``.
You want to copy this to whatever example you are running. It takes the JSON format, where in our example we
have Alice and Bob::

    {
        "default": {
            "nodes": {
                "Alice": {
                    "app_socket": ["localhost", 8821],
                    "qnodeos_socket": ["localhost", 8822],
                    "vnode_socket": ["localhost", 8823]
                },
                "Bob": {
                    "app_socket": ["localhost", 8831],
                    "qnodeos_socket": ["localhost", 8832],
                    "vnode_socket": ["localhost", 8833]
                }
            },
            "topology": null
        }
    }

The first thing that happens if we execute the script ``doNew.sh`` is that after some setting up it will call ``run.sh``,
executing::

    #!/usr/bin/env bash

    python3 bobTest.py &
    python3 aliceTest.py

Let us now look at the programs for Alice and Bob. Alice will merely run a client on the classical communication
network that connects to Bob to be found in aliceTest.py. Using the template (see general Examples section) which
establishes the connections to the local virtual nodes, we thus need to provide client code for Alice to implement
the protocol above. The function runClientNode will automatically be executed once Alice connected to her local
virtual quantum node simulating the underlying hardware, and to Bob's server::

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

            # Create 2 qubits
            qA = yield virtRoot.callRemote("new_qubit_inreg",qReg)
            qB = yield virtRoot.callRemote("new_qubit_inreg",qReg)

            # Put qubits A and B in a maximally entangled state
            yield qA.callRemote("apply_H")
            yield qA.callRemote("cnot_onto",qB)

            # Send qubit B to Bob
            # Instruct the virtual node to transfer the qubit
            remoteNum = yield virtRoot.callRemote("send_qubit",qB, "Bob")

            # Tell Bob the ID of the qubit, and ask him to measure
            bob = classicalNet.hostDict["Bob"]
            yield bob.root.callRemote("process_qubit", remoteNum)

            # Measure qubit A to obtain a random number
            x = yield qA.callRemote("measure")
            print("ALICE: My Random Number is ",x,"\n")

            reactor.stop()


Let us now look at Bob's server program to be found in bobTest.py. Observe that Alice will call process_qubit above.
Not included in the code below are several standard methods that require no change to be used in examples.::

    #####################################################################################################
    #
    # localNode
    #
    # This will be run if the local node acts as a server on the classical communication network,
    # accepting remote method calls from the other nodes.

    class localNode(pb.Root):

            # This can be called by Alice to tell Bob to process the qubit
            @inlineCallbacks
            def remote_process_qubit(self, virtualNum):
                    """
                    Recover the qubit and measure it to get a random number.
                
                    Arguments
                    virtualNum      number of the virtual qubit corresponding to the EPR pair received
                    """

                    qB = yield self.virtRoot.callRemote("get_virtual_ref",virtualNum)

                    # Measure
                    x = yield qB.callRemote("measure")

                    print("BOB: My Random Number is ", x, "\n")

--------
Starting
--------

We first start the virtual quantum node backend, by executing::

    simulaqron start --nodes=Alice,Bob --network-config-file classicalNet.json

We then start up the programs for Alice and Bob themselves. These will connect to the virtual quantum nodes, and
execute the quantum commands and classical communication outlined above, in the same directory as we placed
``classicalNet.json``::

    python3 bobTest.py &
    python3 aliceTest.py

You can easily start everything by using the a single helper script::

    bash doNew.sh

-------
Stoping
-------

You can stop all the running processes by using the helper script::

    bash terminate.sh

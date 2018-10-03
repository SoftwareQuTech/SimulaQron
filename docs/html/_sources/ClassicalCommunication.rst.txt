Classical Communication
========================

In the figure below there is a schematic overview of how the communication is realized between the nodes in a network simulated by SimulaQron.
In this setup there are three nodes: Alice, Bob and Eve.
Firstly, the applications in each node communicate with a CQC (classical-quantum-combiner) server that in turn talk to a SimulaQron server.
CQC is an interface between the classical control information in the network and the hardware, here simulated by SimulaQron.
The communication between the nodes needed to simulate the quantum hardware is handled by the SimulaQron servers, denoted SimulaQron internal communication in the figure.
Note that such communication is needed since entanglement cannot be simulated locally.
SimulaQron comes with a Python library that handles all the communication between the application and the CQC server.
In this library, the object ``CQCConnection`` takes care of this communication.
Any operation applied to the qubits in this Python library is translated to a message sent to the CQC server, by the ``CQCConnection``.

On top of the quantum network there will be classical communication between the applications, denoted Application communication in the figure.
This communication include for example the case where Alice can sends Bob an encoded classical message or a measurement outcome.
Such communication would also be present in a real implementation of a quantum network.
There is a built-in feature in the Python library that realize this functionality, which have been developed for ease of use for someone not familiar with a client/server setup.
This communication is also handled by the object ``CQCConnection``.
Let assume that Alice wants to send a classical message to Bob and that ``Alice`` and ``Bob`` are instances of ``CQCConnection`` at the respective nodes.
For Alice to be able to send a message to Bob, Bob needs to first start a server by running ``Bob.startClassicalServer()``.
Alice would then apply the method ``Alice.sendClassical("Bob",msg)``, where ``msg`` is the message she wish to send to Bob.
The method checks if a socket connection is already opened to Bob and if not opens one and sends the message.
Note that if this method is never called, a socket connection is never opened.
Both the socket connection on Alice's side and the server on Bob's side can be closed by the methods ``closeClassicalChannel`` and ``closeClassicalServer``, respectively.
Alternatetively all connections set up by the ``CQCConnection``, including the connection to the CQC server, can be closed by the method ``close``
Note that if this method is never called a socket connections never opened.
Both the socket connection on Alice's side and the server on Bob's side can be closed by the methods ``closeClassicalChannel`` and ``closeClassicalServer``, respectively.
Alternatetively all connections set up by the ``CQCConnection``, including the connection to the CQC server, can be closed by the method ``close``.

We emphasise that to have classical communication between the applications, one is not forced to use the built-in functionality realized by the ``CQCConnection``.
You can just as well setup your own client/server communication using the method of your preference.
More information and a template for setting up a client/server interaction can be found in :doc:`NativeModeTemplate`:.

.. image:: figs/servers.pdf
    :width: 600px
    :align: center
    :alt: Programming SimulaQrons Interfaces

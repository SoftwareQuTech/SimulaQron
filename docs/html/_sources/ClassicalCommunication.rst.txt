Classical Communication
========================

In the figure below there is a schematic overview of how the communication is realized between the nodes in a network simulated by SimulaQron.
In this setup there are three nodes: Alice, Bob and Eve.
Firstly, the applications in each node communicate with a CQC (classical-quantum-combiner) server that in turn talk to a SimulaQron server.
CQC is an interface between the classical control information in the network and the hardware, here simulated by SimulaQron.
The communication between the nodes needed to simulate the quantum hardware is handled by the SimulaQron servers, denoted SimulaQron internal communication in the figure.
Note that such communication is needed since entanglement cannot be simulated locally.
SimulaQron comes with a Python library that handles all the communication between the application and the CQC server.
In this library, the object :code:`CQCConnection` takes care of this communication.
Any operation applied to the qubits in this Python library is translated to a message sent to the CQC server, by the :code:`CQCConnection`.

On top of the quantum network there will be classical communication between the applications, denoted Application communication in the figure.
This communication include for example the case where Alice can sends Bob an encoded classical message or a measurement outcome.
Such communication would also be present in a real implementation of a quantum network.
There is a built-in feature in the Python library that realize this functionality, which have been developed for ease of use for someone not familiar with a client/server setup.

.. note:: To have classical communication between the applications, one is not forced to use the built-in functionality realized by the ``CQCConnection``. You can just as well setup your own client/server communication using the method of your preference. More information and a template for setting up a client/server interaction can be found in :doc:`NativeModeTemplate`:.

The built-in classical communication of the Python library is handled by the object :code:`CQCConnection`.
Let assume that Alice wants to send a classical message to Bob and that Alice and Bob are instances of :code:`CQCConnection` at the respective nodes.
This can be done by simply executing :code:`Alice.sendClassical("Bob", msg)`, where :code:`msg` is the message to be sent from Alice to Bob.
The method :code:`sendClassical` tries to open a socket connection to Bob and to sent the message.
Note that if this method is never called, a socket connection is never opened.
The socket connection between Alice and Bob are closed after the message is sent.
This classical communication is thus not built for efficiency but for easy of use for someone not familiar with client/server setup.

.. note:: CQC and the python library does not require SimulaQron to function. However if you want to use the built-in classical communication you need SimulaQron installed.

.. image:: figs/servers.png
    :width: 600px
    :align: center
    :alt: Programming SimulaQrons Interfaces

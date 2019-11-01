The CQC interface
=================

SimulaQron can be access from any programming language supporting network connections. Instructions to the quantum hardware simulation can be sent via the CQC interface described `here <https://softwarequtech.github.io/CQC-Python/interface.html>`_.

A `C <https://softwarequtech.github.io/CQC-C/index.html>`_, `Python <https://softwarequtech.github.io/CQC-Python/index.html>`_, and `Rust <https://docs.rs/cqc>`_ Library for programming SimulaQron using the CQC Interface are provided. If you are new to SimulaQron, programming via the Python CQC is the easiest way to get started.

^^^^^^^^^^^^
Installation
^^^^^^^^^^^^

If you have installed SimulaQron using pip, the cqc interface for python should already be installed.
If needed you can also only install the CQC interface in Python using pip by typing::

    pip3 install cqc

^^^^^
Usage
^^^^^

The python library provides a way to program a protocol on a network where the nodes listen to instructions through the classical-quantum combiner (CQC) interface. In the following examples the network is simulated by SimulaQron. But the same examples could be executed on a network with real quantum hardware which allows for instructions through the CQC interface, which is the aim for the 2020 quantum internet demonstrator.

To use the Python library you first need instantiate an object from the class :code:`cqc.pythonLib.CQCConnection`. This should be done in a `context <https://docs.python.org/3/library/contextlib.html>`_, that is using a :code:`with`-statement as follows::

    with CQCConnection("Alice") as alice:
        # your program

This is to make sure the CQCConnection is correctly closed by the end of the program and that the qubits in the backend are released, even if an error occurs in your program.

.. note:: It is still possible to initialize a :code:`CQCConnection` in the old way, i.e. without :code:`with`, however you will receive a warning message everytime you create a qubit.

Let's look at an extremely trivial example were we have the node `Alice` allocate a qubit, perform a Hadamard gate and measure the qubit::

    with CQCConnection("Alice") as alice:
        q = qubit(Alice)
        q.H()
        m = q.measure()
        print(m)

.. note:: If you do not specify the argument ``socket_address`` specifying the hostname and port of the cqc server receiving incoming CQC messages, you need to have simulaqron installed. The python library then tries to use the socket address of this nodes specified in simulaqron.

A object from the :class:`qubit`-class is created with the :class:`CQCConnection` as argument, such that whenever an operation is applied to the qubit a CQC message will be sent to the simulation backend to actually perform this operation on the simulated qubit.
For more examples using the Python library see :doc:`GettingStarted` and https://softwarequtech.github.io/CQC-Python/examples.html

.. _remoteNetwork:

----------------------------------------
Connecting to a remote simulated network
----------------------------------------

If a simulated network (consisting of virtual nodes and CQC servers) are setup on a remote computer (or on your own computer), CQC messages can be sent to the correct address and port numbers to control the nodes of the network. In this section we describe how to do this.

Given the ip and port number of the CQC server of a node, you can send CQC messages over TCP using in any way you prefer. To know how these messages should look like to perform certain instructions, refer to https://softwarequtech.github.io/CQC-Python/interface.html

An easier way to send CQC messages to a CQC server of a node is to use the provided Python library.
Assuming that you know the hostname and port number of the CQC server, you can then easily instantiate an object of the class :class:`~cqc.pythonLib.CQCConnection` which will communicate with the CQC server for you, using the CQC interface.
You can directly specify the ip and port number as follows::

    cqc = CQCConnection("Alice", socket_address=("1.1.1.1", 8801))

More information on how to then actually allocating qubits, manipulating these and creating simulated entanglement see https://softwarequtech.github.io/CQC-Python/useful_commands.html

We give some more detailed information below on how the classical communication between nodes in the application layer can be realized and also provide some useful commands to program a protocol using the Python library.

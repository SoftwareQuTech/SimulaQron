Using the Python library
========================

The python library provides a way to program a protocol on a network where the nodes listen to instructions through the classical-quantum combiner (CQC) interface. In the following examples the network is simulated by SimulaQron. But the same examples could be executed on a network with real quantum hardware which allows for instructions through the CQC interface, which is the aim for the 2020 quantum internet demonstrator.

To use the Python library you first need instantiate an object from the class :code:`SimulaQron.cqc.pythonLib.cqc.CQCConnection`. This should be done in a `context <https://docs.python.org/3/library/contextlib.html>`_, that is using a :code:`with`-statement as follows::

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

A object from the :code:`qubit`-class is created with the :code:`CQCConnection` as argument, such that whenever an operation is applied to the qubit a CQC message will be sent to the simulation backend to actually perform this operation on the simulated qubit.
For more examples using the Python library see :doc:`GettingStarted` and :doc:`ExamplespythonLib`.

We give some more detailed information below on how the classical communication between nodes in the application layer can be realized and also provide some useful commands to program a protocol using the Python library.

.. toctree::
	:maxdepth: 2

	ClassicalCommunication
	UsefulCommands

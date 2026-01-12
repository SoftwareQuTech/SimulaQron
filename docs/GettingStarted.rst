Getting started 
===============

-----
Setup
-----

SimulaQron requires `Python 3.12 <https://python.org/>`_  along with the packages *cqc*, *twisted*, *numpy*, *scipy*, *networkx*, *flake8*, *click* and *daemons*.

^^^^^^^^^^^^^^^^^^^^^^
Installation using pip
^^^^^^^^^^^^^^^^^^^^^^

The easiest way to install SimulaQron is using pip (requires MacOS or Linux). Start by creating and activating a python virtual environment::

    python3.12 -m venv simulaqron-venv
    source simulaqron-venv/bin/activate

Now, we can install SimulaQron by simply typing::

    pip3 install simulaqron

You can then make use of SimulaQron using the command :code:`simulaqron` in the terminal. For more information on how to use this command see below or type::

    simulaqron -h

To make sure you have the version compatible with this documentation type::

    simulaqron version

If you want to make sure that everything has been installed properly you can start run the unittests. Open a interactive python console by typing `python3` and the::

    import simulaqron
    simulaqron.tests()

------------------------
Testing a simple example
------------------------

Before delving into how to write any program yourself, let's first simply run one of the existing examples when programming SimulaQron through the Python library (see https://softwarequtech.github.io/CQC-Python/examples.html).
Remember from the Overview that SimulaQron has two parts: the first are the virtual node servers that act simulate the hardware at each node as well as the quantum communication between them in a transparent manner.
The second are the applications themselves which can be written in two ways, the direct way is to use the native mode using the Python Twisted framework connecting to the virtual node servers, see :doc:`Examples`.
The recommended way however is the use the NetQASM library that calls the virtual nodes by making use of the classical/quantum combiner interface.
We will here illustrate how to use SimulaQron with the NetQASM library.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Starting the SimulaQron backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
By default SimulaQron uses the five nodes Alice, Bob, Charlie, David and Eve on your local computers. In this example there will be three processes for each node listening to incoming messages on a certain port number. These make up the simulation backend, the NetQASM server and the classical communication server. To start the processes and thus the backend of SimulaQron simply type::

    simulaqron start

.. warning:: Running :code:`simulaqron start` will be default start up servers on localhost (i.e., your own computer), using port numbers between 8000 and 9000, to form the simulated quantum internet hardware. SimulaQron does not provide any access control to its simulated hardware, so you are responsible to securing access should this be relevant for you. You can also run the different simulated nodes on different computers. We do not take any responsibility for problems caused by SimulaQron.

For more information on what :code:`./cli/SimulaQron start` does, how to change the nodes and the ports of the network, the topology etc, see :doc:`ConfNodes`.

To stop the backend, simply type::

    simulaqron stop

If something went wrong (for example the process was killed before you stopped it) there might be leftover files which makes SimulaQron think that the network is still running. To reset this you can type::

    simulaqron reset

Note that this also kills any currently running network and resets any settings or configurations.

^^^^^^^^^^^^^^^^^^^
Running a protocol
^^^^^^^^^^^^^^^^^^^

Having started the virtual quantum nodes as above, let us now run a simple test application, which already illustrates some of the aspects in realizing protocols.
Our objective will be to realize the following protocol which will generate 1 shared random bit between Alice and Bob. Evidently, there would be classical means to achieve this trivial task chosen for illustration.

* Alice and Bob generates one EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`

* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`.

TODO - Update the link references and the names of the examples (NetQASM vs pythonLib)
The examples can be found in the repo `pythonLib <https://github.com/SoftwareQuTech/CQC-Python>`_.
Before seeing how this example works, let us simply run the code::

    cd examples/nativeMode/corrRNG
    sh run.sh

You should be seeing the following two lines::

    App Alice: Measurement outcome is: 0/1
    App Bob: Measurement outcome is: 0/1

Note that the order of these two lines may differ, as it does not matter who measures first. So what is actually going on here? Let us first look at how we will realize the example by making an additional step (3) explicit:

* Alice and Bob generate one EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`

* Alice and Bob are informed of the identifiers of the qubits and are informed that entanglement was generated.

* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`.

While the task we want to realize here is completely trivial, the addition of step 3 does however already highlight a range of choices on how to realize step 3 and the need to find good abstractions to allow easy application development.
One way to realize step 3 would be to hardwire Alice's and Bob's measurements: if the hardware can identify the correct qubits from the entanglement generation, then we could instruct it to measure it immediately without asking for a notification from the entanglement generation process. It is clear that in a network that is a bit larger than our tiny three node setup, identifying the right setup requires a link between the underlying qubits and classical control information: this is the objective of the classical/quantum combiner.

The script run.sh executes the following two python scripts::

    #!/bin/sh

    python3 aliceTest.py
    python3 bobTest.py &

Let us now look at the programs for Alice and Bob.
We first initialize an object of the class ``NetQASMConnection`` which will do all the communication to the virtual through the NetQASM interface.
Qubits can then be created by initializing a qubit-object, which takes a ``NetQASMConnection`` as an input.
On these qubits operations can be applied and they can also be sent to other nodes in the network by use of the ``NetQASMConnection``.
The full code in aliceTest.py is::

    # Create an EPR Socket between "Alice" and "Bob"
    epr_socket = EPRSocket("Alice", "Bob")
    # Initialize the connection
    with NetQASMConnection("Alice", epr_sockets=[epr_socket]) as Alice:
        # Create an EPR pair
        q = epr_socker.create_keep("Bob", number=1)[0]

        # Measure qubit
        m=q.measure()
        to_print="App {}: Measurement outcome is: {}".format(Alice.name,m)
        print("|"+"-"*(len(to_print)+2)+"|")
        print("| "+to_print+" |")
        print("|"+"-"*(len(to_print)+2)+"|")

Similarly the code in bobTest.py read::

    # Create an EPR Socket between "Bob" and "Alice"
    epr_socket = EPRSocket("Bob", "Alice")
    # Initialize the connection
    with NetQASMConnection("Bob", epr_sockets=[epr_socket]) as Bob:

        # Receive qubit
        q=epr_socker.receive_keep("Alice")[0]

        # Measure qubit
        m=q.measure()
        to_print="App {}: Measurement outcome is: {}".format(Bob.name,m)
        print("|"+"-"*(len(to_print)+2)+"|")
        print("| "+to_print+" |")
        print("|"+"-"*(len(to_print)+2)+"|")

TODO - Update the link references and the names of the examples (NetQASM vs pythonLib)
For further examples, see the examples/ folder and for the docs of the Python library see https://softwarequtech.github.io/CQC-Python/index.html.

--------
Settings
--------

Settings are easily accessed through the command line interface (CLI). To see what settings can be set, type::

    simulaqron set -h

To set a setting, for example to use the projectQ backend, type::

    simulaqron set backend projectq

Alternatively, you can add a file ``.simulaqron.json`` in your home folder (i.e. ``~``).
For example this file could look like::

     {
        "backend": "projectq",
        "log_level": 10
     }

which would set the backend to be use ProjectQ and the log-level to be debug (10). Any setting in this file will override the settings set in the CLI.

.. note:: Settings needs to be set before starting the SimulaQron backend. If the backend is already running, stop it, set the settings and start it again.

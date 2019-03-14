Getting started 
===============

-----
Setup
-----

SimulaQron requires `Python 3 <https://python.org/>`_  and `Twisted <http://twistedmatrix.com/trac/>`_  along with the packages *scipy*, *Cython*, *service_identity*, *qutip*, *matplotlib*, *networkx*, *projectq* and *bitstring*.

^^^^^^^^^^^^
Installation
^^^^^^^^^^^^

To install SimulaQron itself, you can clone the git repository. Do::

	git clone https://github.com/SoftwareQuTech/SimulaQron.git

You will then
need to set the following environment variables in order to execute the code. Assuming that
you use bash (e.g., standard on OSX or the GIT Bash install on Windows 10), otherwise set the same variables using your favorite shell.::

	export NETSIM=yourPath/SimulaQron
	export PYTHONPATH=yourPath:$PYTHONPATH

where yourPath is the directory containing SimulaQron. You can add this to your ~/.bashrc or ~/.bash_profile file.

^^^^^^^^^^^^^^^^^^^^^^^^^^^
Verifying the installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run SimulaQron you need to following Python packages:

* scipy
* Cython
* service_identity
* twisted
* qutip
* matplotlib
* networkx$
* projectq
* bitstring

To verify that that SimulaQron is working on your computer, type::

    make verify

in a terminal at the root of the repository. This command will clear any .pyc files in this directory, check that the needed python packages are installed (and if not install these using pip) and run the automated tests. By default a shorter version of the tests are run. If you wish to run the full tests type :code:`make full_tests`. Not however that the full tests can take quite some time since they perform quantum tomography to tests operations on the qubits.
By default the *projectq* engine will be used. If you wish to run the tests with the *qutip* backend instead, type :code:`make tests_qutip` or :code:`make full_tests_qutip`. If you want to run all tests with all three backends, type :code:`make full_tests_allBackends`. Note that running the full tests with all backends takes a lot of time.

If :code:`make` does not work for you, you can also run the test by typing :code:`sh tests/runTests.sh --quick` (not including tomography tests) or :code:`sh tests/runTests.sh --full` (full tests).

------------------------
Testing a simple example
------------------------

Before delving into how to write any program yourself, let's first simply run one of the existing examples when programming SimulaQron through the Python library (see :doc:`ExamplespythonLib`).
Remember from the Overview that SimulaQron has two parts: the first are the virtual node servers that act simulate the hardware at each node as well as the quantum communication between them in a transparent manner.
The second are the applications themselves which can be written in two ways, the direct way is to use the native mode using the Python Twisted framework connecting to the virtual node servers, see :doc:`ExamplesDirect`.
Another way is the use the provided Python library that calls the virtual nodes by making use of the classical/quantum combiner interface.
We will here illustrate how to use SimulaQron with the Python library.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Starting the SimulaQron backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
By default SimulaQron uses the five nodes Alice, Bob, Charlie, David and Eve on your local computers. In this example there will be two processes for each node listening to incoming messages on a certain port number. These make up the simulation backend and the CQC server. To start the processes and thus the backend of SimulaQron simply type::

    ./cli/main.py network start-all

.. warning:: Running :code:`./cli/main.py network start-all` will be default start up servers on localhost (i.e., your own computer), using port numbers 8801-8811, to form the simulated quantum internet hardware. SimulaQron does not provide any access control to its simulated hardware, so you are responsible to securing access should this be relevant for you. You can also run the different simulated nodes on different computers. We do not take any responsibility for problems caused by SimulaQron.

For more information on what :code:`./cli/main.py network start-all` does, how to change the nodes and the ports of the network, the topology etc, see :doc:`ConfNodes`.

^^^^^^^^^^^^^^^^^^^
Running a protocol
^^^^^^^^^^^^^^^^^^^

Having started the virtual quantum nodes as above, let us now run a simple test application, which already illustrates some of the aspects in realizing protocols.
Our objective will be to realize the following protocol which will generate 1 shared random bit between Alice and Bob. Evidently, there would be classical means to achieve this trivial task chosen for illustration.

* Alice and Bob generates one EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`

* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`.

Before seeing how this example works, let us again simply run the code::

	cd examples/cqc/pythonLib/corrRNG
	sh doNew.sh

You should be seeing the following two lines::

	App Alice: Measurement outcome is: 0/1
	App Bob: Measurement outcome is: 0/1

Note that the order of these two lines may differ, as it does not matter who measures first. So what is actually going on here? Let us first look at how we will realize the example by making an additional step (3) explicit:

* Alice and Bob generate one EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`

* Alice and Bob are informed of the identifiers of the qubits and are informed that entanglement was generated.

* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`.

While the task we want to realize here is completely trivial, the addition of step 3 does however already highlight a range of choices on how to realize step 3 and the need to find good abstractions to allow easy application development.
One way to realize step 3 would be to hardwire Alices and Bobs measurements: if the hardware can identify the correct qubits from the entanglement generation, then we could instruct it to measure it immediately without asking for a notification from the entanglement generation process. It is clear that in a network that is a bit larger than our tiny three node setup, identifying the right setup requires a link between the underlying qubits and classical control information: this is the objective of the classical/quantum combiner.

The first thing that happens if we execute the script doNew.sh is that after some setting up it will call run.sh, executing::

	#!/bin/sh

	python aliceTest.py
	python bobTest.py &

Let us now look at the programs for Alice and Bob.
We first initialize an object of the class ``CQCConnection`` which will do all the communication to the virtual through the CQC interface.
Qubits can then be created by initializing a qubit-object, which takes a ``CQCConnection`` as an input.
On these qubits operations can be applied and they can also be sent to other nodes in the network by use of the ``CQCConnection``.
The full code in aliceTest.py is::

    # Initialize the connection
    with CQCConnection("Alice") as Alice:

        # Create an EPR pair
        q = Alice.createEPR("Bob")

        # Measure qubit
        m=q.measure()
        to_print="App {}: Measurement outcome is: {}".format(Alice.name,m)
        print("|"+"-"*(len(to_print)+2)+"|")
        print("| "+to_print+" |")
        print("|"+"-"*(len(to_print)+2)+"|")

Similarly the code in bobTest.py read::

    # Initialize the connection
    with CQCConnection("Bob") as Bob:

        # Receive qubit
        q=Bob.recvEPR()

        # Measure qubit
        m=q.measure()
        to_print="App {}: Measurement outcome is: {}".format(Bob.name,m)
        print("|"+"-"*(len(to_print)+2)+"|")
        print("| "+to_print+" |")
        print("|"+"-"*(len(to_print)+2)+"|")

For further examples, see the examples/ folder.

--------
Settings
--------

In the file config/settings.ini you can set the following parameters for SimulaQron:

* :code:`[BACKEND]`
    * :code:`maxqubits_per_node` (default 20): This is the maximum virtual qubits a node can store. Note that a node can still have more simulated qubits.
    * :code:`maxregisters_per_node` (default 1000): This is the maximum of qubit registers a virtual node can store.
    * :code:`waittime` (default 0.5): This is the amount of time that the virtual nodes will wait to try to set up connection between them (when running :code:`./cli/main.py network start-all`). If you're setting up SimulaQron between multiple computers, you may wish to increase this.
    * :code:`loglevel` (default `warning`): Determines which logging messages should be printed from the backend. Options are `critical`, `error`, `warning`, `info` and `debug`, with increasing amount of logging. Setting the log-level to `debug` will print a lot of messages.
    * :code:`backendhandler` (default `simulaqron`): This is to set different types of backends for parsing the CQC messages. Current options are `simulaqron` and `log` (simply log the CQC messages). Unless you know what you're doing don't change this!
    * :code:`backend` (default `projectq`): Current choices are: `qutip` (mixed states), `projectq` (pure states) and `stabilizer` (stabilizer states and only Clifford operations).
    * :code:`topology_file` (default `<empty_string>`): Set this to the relative path (seen from root of the repo) of a .json file describing the topology of the network to be used. For more details on how to configure a network with a specific topology, see :doc:`ConfNodes`.
    * :code:`noisy_qubits` (default `False`): Setting this to `True` will add probabilistic Pauli noise to the simulated qubits, with a rate specified with the :code:`T1` parameter below.
    * :code:`T1` (default 1): If :code:`noisy_qubits` above is `True` then for each qubit one of the Pauli operators :math:`X=\begin{pmatrix}0 & 1 \\ 1 & 0\end{pmatrix}`, :math:`Y=\begin{pmatrix}0 & -i \\ i & 0\end{pmatrix}` or :math:`Z=\begin{pmatrix}1 & 0 \\ 0 & -1\end{pmatrix}` will be applied with probability :math:`1-exp(-t/T1)`, where :math:`t` is the time the qubit spent at a node. NOTE, this is not an accurate model of noise in a quantum network but simply an option to be able run and explore protocols in a noisy setting. A major drawback with this noise model is that the amount of noise during a protocol depends on how fast your computer is, since the only time in SimulaQron is the runtime of your computer.
* :code:`[FRONTEND]`
    * :code:`loglevel` (default `warning`): Determines which logging messages should be printed from the Python library. Options are `critical`, `error`, `warning`, `info` and `debug`, with increasing amount of logging. Setting the log-level to `debug` will print a lot of messages.

There are also additional settings for CQC backend which can be set in the file cqc/backend/cqcConfig.py:

* :code:`CQC_CONF_RECV_TIMEOUT` (default 10 s): The time a node will wait for receiving a qubit before sending back an error message using CQC.
* :code:`CQC_CONF_RECV_EPR_TIMEOUT` (default 10 s): The time a node will wait for receiving a qubit part of an EPR pair before sending back an error message using CQC.
* :code:`CQC_CONF_WAIT_TIME_RECV` (default 0.1 s): The time between every check if a qubit has been received.
* :code:`CQC_CONF_LINK_WAIT_TIME` (default 0.5 s): The time between every try to connect to the CQC server.
* :code:`CQC_CONF_COM_WAIT_TIME` (default 0.1 s): The time between every try to connect applications at other nodes for classical communication.

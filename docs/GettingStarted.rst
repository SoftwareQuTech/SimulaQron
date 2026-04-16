Getting started 
===============

-----
Setup
-----

SimulaQron requires `Python 3.12 <https://python.org/>`_ along with the packages *netqasm*, *twisted*, *numpy*, *scipy*,
*networkx*, *click* and *daemons*. By following the installation instructions in the following sections, you will install
SimulaQron with all the required packages.

^^^^^^^^^^^^^^^^^^^^^^
Installation using pip
^^^^^^^^^^^^^^^^^^^^^^

The easiest way to install SimulaQron is using pip. SimulaQron has been tested working in Linux, and WSL (under windows).
For installation on macOS, please use a Linux virtual machine to install SimulaQron.

Before proceeding with the installation, you need to install Python 3.12. For Debian-based distributions (like Ubuntu)
you can install the *deadsnakes* repository to gain access to some specific python versions::

    sudo add-apt-repository -y "ppa:deadsnakes/ppa"

After adding the repository, you can install the *full* version of python, including the development package::

    sudo apt-get install python3.12-full python3.12-dev

Additionally, you will need the `build-essential` package, to install tools used when building some SimulaQron dependencies::

    sudo apt-get install build-essential cmake vim linux-headers-generic

To install SimulaQron, start by creating and activating a python virtual environment::

    python3.12 -m venv simulaqron-venv
    source simulaqron-venv/bin/activate

Now, we can install SimulaQron by simply typing::

    pip3 install simulaqron

It is also recommended that you also install optional dependencies to enable full support of qubit engines::

    pip3 install simulaqron\[opt\]

You can then make use of SimulaQron using the command ``simulaqron`` in the terminal. For more information on how
to use this command see below or type::

    simulaqron -h

To make sure you have the version compatible with this documentation type::

    simulaqron version

------------------------
Testing a simple example
------------------------

Before delving into how to write any program yourself, let's first simply run one of the existing examples.
Remember from the :doc:`Overview<Overview>` that SimulaQron has two parts: the first are the virtual node servers
that simulate the hardware at each node as well as the quantum communication between them in a transparent manner.
The second are the applications themselves which can be written in two ways: the direct way is to use the native
mode using the Python Twisted framework connecting to the virtual node servers (see :ref:`Native mode examples <native-mode-examples>`),
and the recommended way is to use the NetQASM library that calls the virtual nodes via the NetQASM interface.
We will here illustrate how to use SimulaQron with the NetQASM library.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Starting the SimulaQron backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default SimulaQron uses the five nodes Alice, Bob, Charlie, David and Eve on your local computers. In this example
there will be three processes for each node listening to incoming messages on a certain port number. These make up
the simulation backend, the NetQASM server and the classical communication server. To start the processes and thus
the backend of SimulaQron simply type::

    simulaqron start

.. warning:: Running ``simulaqron start`` will by default start up servers on localhost (i.e., your own computer),
    using port numbers between 8000 and 9000, to form the simulated quantum internet hardware. SimulaQron does not
    provide any access control to its simulated hardware, so you are responsible to securing access should this be
    relevant for you. You can also run the different simulated nodes on different computers. We do not take any
    responsibility for problems caused by SimulaQron.

For more information on what ``simulaqron start`` does, how to change the nodes and the ports of the network,
the topology etc, see :doc:`Configuring the Network <ConfNodes>`.

To stop the backend, simply type::

    simulaqron stop

If something went wrong (for example the process was killed before you stopped it) there might be leftover files which
makes SimulaQron think that the network is still running. To reset this you can type::

    simulaqron reset

Note that this also kills any currently running network and resets any local settings or configurations.

^^^^^^^^^^^^^^^^^^^
Running a protocol
^^^^^^^^^^^^^^^^^^^

Having started the virtual quantum nodes as above, let us now run a simple test application, which already illustrates
some of the aspects in realizing protocols. Before proceeding, please download the SimulaQron examples as shown in the
:ref:`How to get the examples<get-examples>` section.
Our objective will be to realize the following protocol which will generate 1 shared random bit between Alice and Bob.
Evidently, there would be classical means to achieve this trivial task chosen for illustration.

* Alice and Bob generates one EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form
  :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`

* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`.

We will follow the example located in ``examples/new-sdk/corrRNG`` (see :ref:`New SDK Examples <new-sdk-examples>` for
the full list). Before seeing how this works, let us simply run the code (assuming you're already in the ``SimulaQron``
folder cloned from GitHub)::

    cd examples/new-sdk/corrRNG
    bash run.sh

You should be seeing the following two lines::

    Alice: My Random Number is '0/1'
    Bob: My Random Number is '0/1'

Note that the order of these two lines may differ, as it does not matter who measures first. So what is actually
going on here? Let us first look at how we will realize the example by making an additional step (3) explicit:

* Alice and Bob generate one EPR pair, that is, two maximally entangled qubits :math:`A` and :math:`B` of the form
  :math:`|\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)`

* Both Alice and Bob measure their respective qubits to obtain a classical random number :math:`x \in \{0,1\}`.

While the task we want to realize here is completely trivial, the addition of step 2 does however already highlight a
range of choices on how to realize step 2 and the need to find good abstractions to allow easy application development.
One way to realize step 2 would be to hardwire Alice's and Bob's measurements: if the hardware can identify the
correct qubits from the entanglement generation, then we could instruct it to measure it immediately without asking
for a notification from the entanglement generation process. It is clear that in a network that is a bit larger than
our tiny two node setup, identifying the right setup requires a link between the underlying qubits and classical
control information: this is the objective of the classical/quantum combiner.

The script ``run.sh`` executes the following two python scripts::

    #!/usr/bin/env bash

    # Some code to start SimulaQron backend

    python3 aliceTest.py &
    python3 bobTest.py

Let us now look at the programs for Alice and Bob.

We first create a ``NetQASMConnection`` which handles all communication with the local quantum backend.
An ``EPRSocket`` is used to create or receive entangled qubit pairs with a remote node.
The key pattern is: queue operations, call ``flush()`` to execute them, then read results with ``int(m)``.

The core of ``aliceTest.py`` is::

    epr_socket = EPRSocket("Bob")

    # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
    sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

    # Create an entangled qubit
    epr = epr_socket.create_keep()[0]

    # Measure it
    m1 = epr.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  Before flush(), m1 is just a future/promise.
    sim_conn.flush()

    # int(m) extracts the measurement outcome — only valid after flush().
    m1_val = int(m1)
    sim_conn.close()

Similarly the core of ``bobTest.py`` is::

    epr_socket = EPRSocket("Alice")

    # sim_conn is our connection to the quantum backend (SimulaQron), not to Alice.
    sim_conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])

    # Receive an entangled qubit
    epr = epr_socket.recv_keep()[0]

    # Measure it
    m1 = epr.measure()

    sim_conn.flush()
    m1_val = int(m1)
    sim_conn.close()

For further examples, see :doc:`Examples <Examples>` and :doc:`The NetQASM Interface <NetQASM>` for the full SDK reference.

.. _settings:

--------
Settings
--------

Settings are easily accessed through the command line interface (CLI). To see what settings can be set, type::

    simulaqron set -h

To set a setting, for example to use the projectQ backend, type::

    simulaqron set backend projectq

This will create a file named ``simulaqron_settings.json`` in the current folder. This new file contains a full set of
simulaqron configuration, including the setting that was just configured (using the `projectq` backend, in the example).

It is also possible to manually create this ``simulaqron_settings.json`` file with any text editor::

     {
        "sim_backend": "projectq",
        "log_level": 10
     }

which would set the backend to use ProjectQ and the log-level to be debug (10).

It is also possible to create a configuration file that contains all the default configurations::

    simulaqron set default

This command will create a file with the following configuration::

    {
        "max_qubits": 20,
        "max_registers": 1000,
        "conn_retry_time": 0.5,
        "conn_max_retries": 10,
        "recv_timeout": 100,
        "recv_retry_time": 0.1,
        "recv_max_retries": 10,
        "log_level": 30,
        "sim_backend": "qutip",
        "noisy_qubits": false,
        "max_app_waiting_time": -1.0,
        "t1": 1.0
    }

The section `Settings Fields`_ below provides a description about each one of the configuration options in the file.

Alternatively, you can place the ``simulaqron_settings.json`` file in the folder ``~/.simulaqron`` (i.e. a folder
named ``.simulaqron`` in your home folder). Doing so will make your settings persist across different projects you
implement using simulaqron.

.. note:: Settings need to be set before starting the SimulaQron backend. If the backend is already running, stop
    it, set the settings and start it again.

It is also possible to create the default SimulaQron network configuration in the current folder. Check the
:doc:`Configuring the Network <ConfNodes>` document to check how to achieve this.

^^^^^^^^^^^^^^^^^^^
Settings precedence
^^^^^^^^^^^^^^^^^^^

Since the simulaqron configuration file can be placed in several places, SimulaQron will follow a priority for
reading the settings:

* Settings file placed in the current working folder.
* Settings file placed in the ``~/.simulaqron`` folder.
* If none of the above is found, SimulaQron will create a settings file in the ``~/.simulaqron`` folder, then it
  will try to load it in that place.

.. _settings_fields:

^^^^^^^^^^^^^^^
Settings Fields
^^^^^^^^^^^^^^^

The SimulaQron settings file contains a set of fields to control the configurations of the SimulaQron simulation:

* ``max_qubits``: Maximum number of qubits to simulate on the Virtual Node.
* ``max_registers``: Maximum number of registers to use in the Virtual Node.
* ``conn_retry_time``: Number of seconds to wait between connection retries.
* ``conn_max_retries``: Maximum number of times to retry a connection before failing the whole execution.
* ``recv_timeout``: Maximum number of milliseconds to wait for the messages when trying to create EPR pairs.
* ``recv_retry_time``: Maximum number of milliseconds to wait between attempts to create EPR pairs.
* ``recv_max_retries``: Maximum number of tries to attempt when creating EPR pairs.
* ``log_level``: The log level to use for SimulaQron. The integer value in this field must match the values exposed
  by the python ``logging`` package. For more information about the specific values for each logging level, please
  check the `official python documentation for the logging package <https://docs.python.org/3/library/logging.html#logging-levels>`_.
* ``sim_backend``: The backend qubit simulation that SimulaQron will use to emulate qubits. Currently, three backends
  are supported: "projectq", "qutip" and "stabilizer".
* ``noisy_qubits``: Whether to enable noisy qubits simulation or not. Setting this to ``true`` will randomly apply a
  Pauli gate after every operation, emulating noise on the qubit backend.
* ``max_app_waiting_time``: Maximum time (in seconds) to wait before considering the running application as stalled.
  A value of ``-1.0`` will disable the stalling waiting time, allowing SimulaQron to wait indefinitely.
* ``t1``: T1 parameter to use when applying noise on the emulated qubits. This value is only used when the
  ``noisy_qubits`` option is set to ``true``.

The default value of all these fields can be seen in the Settings_ section above.

.. note:: An application can become "stalled" in certain configurations, leaving the application to look "hung". This
    leads to a deadlock of the application. SimulaQron will wait for the configured time before considering the
    application as "stalled" and kill all the processes.

.. warning:: Please correctly configure the ``max_app_waiting_time`` to allow your application to wait for any
    potential "slow" peers. A low value on this field might lead SimulaQron to killing your application prematurely.

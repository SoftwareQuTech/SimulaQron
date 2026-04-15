SimulaQron Documentation
========================

Welcome to the Quantum Internet simulator SimulaQron!

SimulaQron is a distributed simulation of the end nodes in a future quantum internet with the specific goal to explore
application development. Each node in the simulated network provides the illusion of having a local quantum processor
to potential applications, while the nodes connect classically to allow the exchange of simulated qubits and the
creation of simulated entanglement.

Key features
------------

* **Distributed quantum internet simulation** — install a local simulation program on each computer, or run all nodes
  on a single machine
* **Three simulation backends** — stabilizer formalism (efficient), `QuTip <http://qutip.org/>`_ (default, mixed
  state), and `ProjectQ <https://projectq.ch/>`_ (pure state)
* **Two programming interfaces** — the NetQASM SDK (recommended) and a native Twisted mode for low-level access
* **Configurable network topologies** — complete, ring, path, random tree, or custom topologies
* **Classical communication** — built-in client/server framework for exchanging classical messages between nodes

Quick start
-----------

#. **Install dependencies**::

    sudo add-apt-repository -y "ppa:deadsnakes/ppa"
    sudo apt-get install python3.12-full python3.12-dev
    sudo apt-get install build-essential cmake linux-headers-generic

#. **Create a python virtual environment**::

    python3.12 -m venv simulaqron-venv

#. **Activate the virtual environment**::

    source simulaqron-venv/bin/activate

#. **Install SimulaQron**::

    pip install simulaqron

#. **Configure SimulaQron** — use the ``simulaqron`` command line tool to create a default ``simulaqron_settings.json`` file::

    simulaqron set default

#. **Configure your network** — use the ``simulaqron`` command line tool to create a default ``simulaqron_network.json`` file, which contains 5 nodes::

    simulaqron nodes default

#. **Start the simulaqron backend**::

    simulaqron start

#. **Write your first program** using the NetQASM SDK. Save this code as ``program.py``::

    from netqasm.runtime.settings import set_simulator
    set_simulator("simulaqron")
    from netqasm.sdk.external import NetQASMConnection
    from netqasm.sdk import Qubit

    conn = NetQASMConnection("Alice")
    q = Qubit(conn)
    q.H()
    m = q.measure()
    conn.flush()                             # execute queued operations
    print(f"Qubit measurement: {int(m)}")    # read measurement result
    conn.close()

#. **Execute your program**::

    python program.py

#. **Check the output**. Output should be ``Qubit measurement: 0/1``. Measurement should randomly be ``0`` or ``1``.

#. **Stop simulaqron backend**. Before running another application, stop the current running backend::

    pip install simulaqron

#. **Run other more complex examples** — see :doc:`Examples <Examples>` for complete working programs.

Where to go next
----------------

* **New to SimulaQron?** Start with :doc:`Getting Started <GettingStarted>` for installation and your first example
* **Want to write programs?** See :doc:`The NetQASM Interface <NetQASM>` for the NetQASM SDK reference
* **Looking for examples?** See :doc:`Examples <Examples>` — new SDK, event-based, and native-mode examples
* **Configuring networks and settings?** See :ref:`Configuring the Network <networkConfig>` and :ref:`Settings <settings>`.
* **Architecture and internals?** See :doc:`Overview <Overview>`

We also have a `paper <http://iopscience.iop.org/article/10.1088/2058-9565/aad56e>`_ describing the design of
SimulaQron, freely available on `arxiv <https://arxiv.org/abs/1712.08032>`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   GettingStarted
   NetQASM
   Examples
   ConfNodes
   Overview
   simulaqron


Indices and tables
==================

* Index
* Module Index
* Search

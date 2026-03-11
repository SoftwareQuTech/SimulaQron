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
* **Three simulation backends** — stabilizer formalism (default, efficient), `QuTip <http://qutip.org/>`_ (mixed
  state), and `ProjectQ <https://projectq.ch/>`_ (pure state)
* **Two programming interfaces** — the NetQASM SDK (recommended) and a native Twisted mode for low-level access
* **Configurable network topologies** — complete, ring, path, random tree, or custom topologies
* **Classical communication** — built-in client/server framework for exchanging classical messages between nodes

Quick start
-----------

1. **Install**::

      pip3 install simulaqron

2. **Configure your network** — create a ``simulaqron_network.json`` defining nodes and ports
   (see `Configuring the Network <ConfNodes.rst>`_)

3. **Write your program** using the NetQASM SDK::

      from netqasm.sdk.external import NetQASMConnection
      from netqasm.sdk import Qubit

      conn = NetQASMConnection("Alice")
      q = Qubit(conn)
      q.H()
      m = q.measure()
      conn.flush()          # execute queued operations
      print(int(m))         # read measurement result
      conn.close()

4. **Run examples** — see `Examples <Examples.rst>`_ for complete working programs

Where to go next
----------------

* **New to SimulaQron?** Start with `Getting Started <GettingStarted.rst>`_ for installation and your first example
* **Want to write programs?** See `The NetQASM Interface <NetQASM.rst>`_ for the NetQASM SDK reference
* **Looking for examples?** See `Examples <Examples.rst>`_ — new SDK, event-based, and native-mode examples
* **Configuring networks and settings?** See `Configuring the Network <ConfNodes.rst>`_
* **Architecture and internals?** See `Overview <Overview.rst>`_

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

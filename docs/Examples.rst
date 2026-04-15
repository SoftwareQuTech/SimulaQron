SimulaQron Programming Examples
===============================

SimulaQron offers three ways to write quantum network programs, from highest-level to lowest-level:

1. **New SDK** (``examples/new-sdk/``) — The recommended approach *for simple quantum apps using
   the NetQASM SDK*. Programs use ``NetQASMConnection`` and ``EPRSocket`` for quantum operations,
   and ``SimulaQronClassicalClient``/``SimulaQronClassicalServer`` for classical messaging.
   Start here if you are new to SimulaQron.

2. **Event-based** (``examples/event-based/``) — Builds on the new SDK by adding a state-machine
   pattern for classical messaging.  Each node defines states, message handlers, and a dispatch
   table.  This is the recommended pattern *for protocols that interleave classical negotiation
   with quantum operations*.

3. **Native mode** (``examples/native-mode/``) — The low-level Twisted interface that talks
   directly to SimulaQron's virtual quantum nodes.  This is Python-specific and more verbose,
   but gives full control over the simulation backend.

.. _get-examples:

-----------------------
How to get the examples
-----------------------

The code of the examples can be found in `SimulaQron GitHub repository <https://github.com/SoftwareQuTech/SimulaQron>`_.
Clone this repository using ``git``::

    git clone https://github.com/SoftwareQuTech/SimulaQron.git

All the examples can be found in the ``examples`` folder.

When running one of the examples mentioned below, we assume that you have already made your way through
:doc:`Getting Started <GettingStarted>` and you have the virtual node servers up and running.

.. _new-sdk-examples:

-----------------
New SDK examples
-----------------

* :doc:`Overview <new-sdk/Overview>` — Key concepts: ``NetQASMConnection``, ``EPRSocket``, ``flush()``, file structure
* :doc:`Template <new-sdk/Template>` — Getting started: single-node and client-server templates
* :doc:`CorrRNG <new-sdk/CorrRNG>` — EPR pairs between two nodes, correlated measurement
* :doc:`Teleport <new-sdk/Teleport>` — Quantum teleportation with classical correction messages
* :doc:`ExtendGHZ <new-sdk/ExtendGHZ>` — Three-party entanglement, multiple EPR sockets
* :doc:`MidCircuitLogic <new-sdk/MidCircuitLogic>` — Multiple ``flush()`` calls for mid-circuit classical decisions

.. _event-based-examples:

---------------------
Event-based examples
---------------------

* :doc:`Overview <event-based/Overview>` — Event-based programming model and state machines
* :doc:`PingPong <event-based/PingPong>` — Classical ping-pong between two nodes
* :doc:`PolitePingPong <event-based/PolitePingPong>` — State-machine message dispatch pattern
* :doc:`QuantumCorrRNG <event-based/QuantumCorrRNG>` — Quantum correlated RNG with state machine
* :doc:`QuantumCorrRNGVerified <event-based/QuantumCorrRNGVerified>` — Correlated RNG with verification protocol

.. _native-mode-examples:

---------------------
Native mode examples
---------------------

* :doc:`Template <native-mode/Template>` — Template for programming in native (Twisted) mode
* :doc:`CorrRNG <native-mode/CorrRNG>` — Correlated randomness using native mode
* :doc:`Teleport <native-mode/Teleport>` — Teleportation using native mode
* :doc:`GraphState <native-mode/GraphState>` — Distributing a graph state across four nodes

.. toctree::
    :hidden:

    new-sdk/Overview
    new-sdk/Template
    new-sdk/CorrRNG
    new-sdk/Teleport
    new-sdk/ExtendGHZ
    new-sdk/MidCircuitLogic
    event-based/Overview
    event-based/PingPong
    event-based/PolitePingPong
    event-based/QuantumCorrRNG
    event-based/QuantumCorrRNGVerified
    native-mode/CorrRNG
    native-mode/Template
    native-mode/Teleport
    native-mode/GraphState

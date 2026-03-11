SimulaQron Programming Examples
================================

SimulaQron offers three ways to write quantum network programs, from highest-level to lowest-level:

1. **New SDK** (``examples/new-sdk/``) — The recommended approach using the NetQASM SDK.
   Programs use ``NetQASMConnection`` and ``EPRSocket`` for quantum operations, and
   ``SimulaQronClassicalClient``/``SimulaQronClassicalServer`` for classical messaging.
   Start here if you are new to SimulaQron.

2. **Event-based** (``examples/eventBased/``) — Builds on the new SDK by adding a state-machine
   pattern for classical messaging.  Each node defines states, message handlers, and a dispatch
   table.  This is the recommended pattern for protocols that interleave classical negotiation
   with quantum operations.

3. **Native mode** (``examples/nativeMode/``) — The low-level Twisted interface that talks
   directly to SimulaQron's virtual quantum nodes.  This is Python-specific and more verbose,
   but gives full control over the simulation backend.

The examples below assume that you have already made your way through :doc:`GettingStarted`:
you have the virtual node servers up and running.

-----------------
New SDK examples
-----------------

* :doc:`new-sdk/Overview` — Key concepts: ``NetQASMConnection``, ``EPRSocket``, ``flush()``, file structure
* :doc:`new-sdk/Template` — Getting started: single-node and client-server templates
* :doc:`new-sdk/CorrRNG` — EPR pairs between two nodes, correlated measurement
* :doc:`new-sdk/Teleport` — Quantum teleportation with classical correction messages
* :doc:`new-sdk/ExtendGHZ` — Three-party entanglement, multiple EPR sockets
* :doc:`new-sdk/MidCircuitLogic` — Multiple ``flush()`` calls for mid-circuit classical decisions

---------------------
Event-based examples
---------------------

* :doc:`event-based/Overview` — Event-based programming model and state machines
* :doc:`event-based/PingPong` — Classical ping-pong between two nodes
* :doc:`event-based/PolitePingPong` — State-machine message dispatch pattern
* :doc:`event-based/QuantumCorrRNG` — Quantum correlated RNG with state machine
* :doc:`event-based/QuantumCorrRNGVerified` — Correlated RNG with verification protocol

---------------------
Native mode examples
---------------------

* :doc:`native-mode/Template` — Template for programming in native (Twisted) mode
* :doc:`native-mode/CorrRng` — Correlated randomness using native mode
* :doc:`native-mode/Teleport` — Teleportation using native mode
* :doc:`native-mode/GraphState` — Distributing a graph state across four nodes

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
    native-mode/CorrRng
    native-mode/Template
    native-mode/Teleport
    native-mode/GraphState

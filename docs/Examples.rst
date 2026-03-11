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

The examples below assume that you have already made your way through `Getting Started <GettingStarted.rst>`_:
you have the virtual node servers up and running.

-----------------
New SDK examples
-----------------

* `Overview <new-sdk/Overview.rst>`_ — Key concepts: ``NetQASMConnection``, ``EPRSocket``, ``flush()``, file structure
* `Template <new-sdk/Template.rst>`_ — Getting started: single-node and client-server templates
* `CorrRNG <new-sdk/CorrRNG.rst>`_ — EPR pairs between two nodes, correlated measurement
* `Teleport <new-sdk/Teleport.rst>`_ — Quantum teleportation with classical correction messages
* `ExtendGHZ <new-sdk/ExtendGHZ.rst>`_ — Three-party entanglement, multiple EPR sockets
* `MidCircuitLogic <new-sdk/MidCircuitLogic.rst>`_ — Multiple ``flush()`` calls for mid-circuit classical decisions

---------------------
Event-based examples
---------------------

* `Overview <event-based/Overview.rst>`_ — Event-based programming model and state machines
* `PingPong <event-based/PingPong.rst>`_ — Classical ping-pong between two nodes
* `PolitePingPong <event-based/PolitePingPong.rst>`_ — State-machine message dispatch pattern
* `QuantumCorrRNG <event-based/QuantumCorrRNG.rst>`_ — Quantum correlated RNG with state machine
* `QuantumCorrRNGVerified <event-based/QuantumCorrRNGVerified.rst>`_ — Correlated RNG with verification protocol

---------------------
Native mode examples
---------------------

* `Template <native-mode/Template.rst>`_ — Template for programming in native (Twisted) mode
* `CorrRng <native-mode/CorrRng.rst>`_ — Correlated randomness using native mode
* `Teleport <native-mode/Teleport.rst>`_ — Teleportation using native mode
* `GraphState <native-mode/GraphState.rst>`_ — Distributing a graph state across four nodes

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

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

.. toctree::
    :maxdepth: 2
    :caption: New SDK examples:

    new-sdk/Overview
    new-sdk/Template
    new-sdk/CorrRNG
    new-sdk/Teleport
    new-sdk/ExtendGHZ
    new-sdk/MidCircuitLogic

.. toctree::
    :maxdepth: 2
    :caption: Event-based examples:

    event-based/Overview
    event-based/PingPong
    event-based/PolitePingPong
    event-based/QuantumCorrRNG
    event-based/QuantumCorrRNGVerified

.. toctree::
    :maxdepth: 2
    :caption: Native mode examples:

    native-mode/CorrRng
    native-mode/Template
    native-mode/Teleport
    native-mode/GraphState

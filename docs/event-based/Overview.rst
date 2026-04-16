Event-Based Programming Overview
================================

The event-based examples show how to structure quantum network protocols using
a **state machine** pattern.  This is the recommended approach for protocols that
interleave classical negotiation with quantum operations.

Prerequisites: you should understand the :doc:`New SDK Overview <../new-sdk/Overview>` first.

The state machine pattern
-------------------------

Each node's behaviour is defined by:

1. **States** — string constants naming each phase of the protocol
2. **Handlers** — async functions that execute when a specific message arrives in
   a specific state.  Each handler performs an action and returns the next state.
3. **Dispatch table** — a dictionary mapping ``(current_state, message)`` to handler.
   This *is* the state machine.
4. **Event loop** — reads messages, looks up the transition, calls the handler.

Example structure::

    # States
    STATE_WAITING_ACCEPT = "WAITING_ACCEPT"
    STATE_DONE           = "DONE"

    # Handler
    async def handle_yes(writer: StreamWriter) -> str:
        # ... do something ...
        return STATE_DONE

    # Dispatch table
    DISPATCH = {
        (STATE_WAITING_ACCEPT, "yes"): handle_yes,
    }

    # Event loop
    async def run_alice(reader, writer):
        state = STATE_WAITING_ACCEPT
        while state != STATE_DONE:
            data = await reader.read(255)
            msg = data.decode("utf-8")
            handler = DISPATCH.get((state, msg))
            if handler is None:
                continue  # ignore unknown messages
            state = await handler(writer)

Why this pattern?
-----------------

- **Clear protocol structure**: the dispatch table maps directly to a state
  transition diagram, making the protocol easy to read and verify.
- **Extensible**: adding a new state or message is just adding a handler and
  a dispatch entry — no changes to the event loop.
- **Quantum integration**: handlers can create ``NetQASMConnection``, perform
  quantum operations, and ``flush()`` — keeping quantum code isolated in
  focused handler functions.

Examples
--------

The examples progress from purely classical to quantum:

.. list-table::
    :header-rows: 1
    :widths: 30 70

    * - Example
      - What it teaches
    * - :doc:`PingPong <PingPong>`
      - Basic event loop with simple if/else message handling
    * - :doc:`PolitePingPong <PolitePingPong>`
      - Full state machine pattern with dispatch table
    * - :doc:`QuantumCorrRNG <QuantumCorrRNG>`
      - Adding quantum operations (EPR + measure) to event handlers
    * - :doc:`QuantumCorrRNGVerified <QuantumCorrRNGVerified>`
      - Multi-state protocol: negotiate, quantum, then classical verification

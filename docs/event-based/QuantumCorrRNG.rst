Quantum Correlated RNG: Adding Quantum to Event Handlers
=========================================================

This example combines the state machine pattern with quantum operations.
Alice proposes generating shared randomness; if Bob agrees, both create an EPR
pair and measure their half.  Found in ``examples/event-based/quantumCorrRNG/``.

This is the first example that runs quantum operations inside an event handler.

The protocol
------------

1. Alice sends "generate randomness?" to Bob.
2. Bob replies "yes".
3. Both create an EPR pair and measure their half.
4. Both get the same correlated random bit.

Alice's state diagram
---------------------

::

    (connect)
       │ send "generate randomness?"
       ▼
    WAITING_ACCEPT
       │ recv "yes" → EPR create + measure
       ▼
      DONE

Quantum inside a handler
-------------------------

The key insight: quantum operations happen inside a handler function, using the
same ``sim_conn`` + ``flush()`` pattern from the new-sdk examples::

    async def handle_yes(writer: StreamWriter) -> str:
        epr_socket = EPRSocket("Bob")

        # Open a connection to the quantum backend (not to Bob — that's the
        # classical reader/writer).
        sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

        # Create an EPR pair with Bob and keep our half
        epr = epr_socket.create_keep()[0]
        m = epr.measure()

        # flush() sends all queued quantum operations to the backend and waits
        # for them to complete.  After this, int(m) gives the real value.
        sim_conn.flush()

        result = int(m)
        sim_conn.close()

        print(f"Alice: my random bit is {result}")
        return STATE_DONE

Bob's handler is symmetric, using ``recv_keep()`` instead of ``create_keep()``.

Bob's handler
-------------

::

    async def handle_generate(writer: StreamWriter) -> str:
        # Classical: agree
        writer.write("yes".encode("utf-8"))
        await writer.drain()

        # Quantum: receive our half of the EPR pair
        epr_socket = EPRSocket("Alice")
        sim_conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])

        epr = epr_socket.recv_keep()[0]
        m = epr.measure()
        sim_conn.flush()

        result = int(m)
        sim_conn.close()

        print(f"Bob: my random bit is {result}")
        return STATE_DONE

Key concepts
------------

- **Quantum in handlers**: The handler creates a ``NetQASMConnection``, performs
  quantum operations, calls ``flush()``, reads results, and closes — all within
  one state transition.
- **Classical before quantum**: Bob first sends "yes" (classical), *then* does the
  quantum operation.  The state machine cleanly separates negotiation from execution.
- **sim_conn vs reader/writer**: ``sim_conn`` talks to the local quantum backend.
  ``reader``/``writer`` talk to the other node classically.  These are independent.

Running
-------

::

    cd examples/event-based/quantumCorrRNG
    bash run.sh

.. note:: Unlike the purely classical examples, this one requires the SimulaQron
    backend to be running.  The ``run.sh`` script starts it automatically.

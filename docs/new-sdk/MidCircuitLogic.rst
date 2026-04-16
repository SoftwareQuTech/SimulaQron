Mid-Circuit Classical Logic
===========================

This single-node example demonstrates how to use ``flush()`` to read measurement
results *during* a quantum program, make classical decisions, and continue with
more quantum operations — all within a single connection.
Found in ``examples/new-sdk/midCircuitLogic/``.

Why mid-circuit logic?
----------------------

Without ``flush()``, measurement results are futures that only resolve when
the connection closes.  With ``flush()``, you can read them at any point and
branch your program accordingly.

This is essential for protocols like quantum error correction, adaptive
measurements, and feed-forward circuits.

The protocol
------------

A simple 3-round protocol on a single node:

#. **Round 1**: Prepare :math:`|+\rangle` and measure.
#. **Round 2**: Based on round 1's outcome, prepare the *opposite* state:
    #. If round 1 gave ``0``, prepare :math:`|1\rangle`
    #. If round 1 gave ``1``, prepare :math:`|0\rangle`
#. **Round 3**: Based on the XOR of rounds 1 and 2, decide what to prepare.

The code
--------

From ``nodeTest.py``::

    def run_node(node_name: str):
        results = []

        # sim_conn is our connection to the quantum backend (SimulaQron).
        # All qubit operations are queued through this connection.
        sim_conn = NetQASMConnection(node_name)

        # --- Round 1: prepare |+> and measure ---
        q1 = Qubit(sim_conn)
        q1.H()
        m1 = q1.measure()
        # flush() after each round so we can use the result to decide
        # what to do next (mid-circuit classical logic).
        sim_conn.flush()
        # int(m) extracts the measurement outcome — only valid after flush().
        r1 = int(m1)
        results.append(r1)

        # --- Round 2: classical decision ---
        # If round 1 gave 0, prepare |1>.  If 1, prepare |0>.
        q2 = Qubit(sim_conn)
        if r1 == 0:
            q2.X()
        m2 = q2.measure()
        sim_conn.flush()
        r2 = int(m2)
        results.append(r2)

        # --- Round 3: compound classical logic ---
        xor = r1 ^ r2
        q3 = Qubit(sim_conn)
        if xor:
            q3.X()
        m3 = q3.measure()
        sim_conn.flush()
        r3 = int(m3)
        results.append(r3)

        sim_conn.close()

Key concepts
------------

- **Multiple flush() calls**: Each ``flush()`` is a sync point.  Between flushes,
  you can use Python control flow (``if``/``else``, loops) based on previous
  measurement results.
- **Single connection**: You do not need to create a new ``NetQASMConnection`` for
  each round — create it once, flush multiple times, close at the end.
- **New qubits after flush**: You can allocate new ``Qubit`` objects on the same
  connection after a flush — earlier qubits that were measured are gone, but the
  connection stays open.

Expected output
---------------

::

    Round 1: measured |+> -> 0 (or 1)
    Round 2: measured -> 1 (always opposite of round 1)
    Round 3: measured -> 1 (always equals r1 XOR r2, which is always 1)

Running
-------

::

    cd examples/new-sdk/midCircuitLogic
    bash run.sh

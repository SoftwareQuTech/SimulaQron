Correlated Random Number Generation
====================================

This example demonstrates how two nodes can generate a shared random bit using
quantum entanglement.  Found in ``examples/new-sdk/corrRNG/``.

The protocol
------------

1. Alice creates an EPR pair (two maximally entangled qubits) with Bob.
2. Both Alice and Bob measure their respective qubits.
3. Because the qubits are entangled, both measurements yield the same random bit.

The state before measurement is:

.. math:: |\Psi\rangle_{AB} = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)

Alice's code
------------

From ``aliceTest.py``::

    def run_alice(this_node_name: str, remote_node_name: str) -> int:
        epr_socket = EPRSocket(remote_node_name)

        # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
        # Bob is reached via EPRSocket for quantum and reader/writer for classical.
        sim_conn = NetQASMConnection(this_node_name, epr_sockets=[epr_socket])

        # Create an entangled qubit
        epr = epr_socket.create_keep()[0]

        # And simply measure it
        m1 = epr.measure()

        # flush() executes all queued quantum operations and makes measurement
        # results available.  Before flush(), m1 is just a future/promise.
        sim_conn.flush()

        # int(m) extracts the measurement outcome — only valid after flush().
        m1_val = int(m1)
        sim_conn.close()
        return m1_val

Bob's code
----------

From ``bobTest.py`` — the only difference is ``recv_keep()`` instead of ``create_keep()``::

    def run_bob(this_node_name: str, remote_node_name: str) -> int:
        epr_socket = EPRSocket(remote_node_name)
        sim_conn = NetQASMConnection(this_node_name, epr_sockets=[epr_socket])

        # Receive an entangled qubit (Alice created the pair)
        epr = epr_socket.recv_keep()[0]

        m1 = epr.measure()
        sim_conn.flush()

        m1_val = int(m1)
        sim_conn.close()
        return m1_val

Key concepts
------------

- **EPRSocket** handles entanglement between nodes.  One side calls ``create_keep()``,
  the other calls ``recv_keep()``.
- **sim_conn** is the connection to the quantum backend, not to the other node.
- Both nodes get the same random bit because measuring one half of an EPR pair
  determines the outcome of the other.

Running
-------

::

    cd examples/new-sdk/corrRNG
    sh run.sh

Expected output (the bit value is random)::

    Alice: My Random Number is '0'
    Bob: My Random Number is '0'

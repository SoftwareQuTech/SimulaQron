Extending a GHZ State
=====================

This example creates a three-party GHZ (Greenberger-Horne-Zeilinger) state
across Alice, Bob, and Charlie.  Found in ``examples/new-sdk/extendGHZ/``.

A GHZ state is a maximally entangled state shared between three (or more) parties:

.. math:: |GHZ\rangle = \frac{1}{\sqrt{2}} \left(|000\rangle + |111\rangle\right)

The protocol
------------

1. Alice creates an EPR pair with Bob and tells Bob to proceed.
2. Bob receives his half of an EPR pair that Alice created with him, creates a *new* EPR pair with Charlie,
   and applies a CNOT to extend the entanglement into a GHZ state.
3. Charlie receives his half of an EPR pair that Bob created with him.
4. All three measure — their outcomes are correlated.

The communication flow is::

    Alice ──EPR──► Bob ──EPR──► Charlie
    Alice ──msg──► Bob ──msg──► Charlie
    Alice ◄──msg── Bob ◄──msg── Charlie

Alice's code
------------

From ``aliceTest.py``::

    async def run_alice(reader: StreamReader, writer: StreamWriter) -> int:
        epr_socket = EPRSocket("Bob")

        # sim_conn is our connection to the quantum backend, not to Bob.
        sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

        # Create an entangled qubit with Bob
        epr = epr_socket.create_keep()[0]

        # Tell Bob to proceed
        writer.write("receive_qubit".encode("utf-8"))
        answer = await reader.read(100)
        assert answer.decode("utf-8") == "continue"

        m1 = epr.measure()
        sim_conn.flush()
        m1_val = int(m1)
        sim_conn.close()
        return m1_val

Bob's code
----------

Bob is the key node — he has EPR sockets to *both* Alice and Charlie::

    sim_conn = NetQASMConnection("Bob",
        epr_sockets=[epr_socket_alice, epr_socket_charlie])

    # Receive entangled qubit from Alice
    epr_alice = epr_socket_alice.recv_keep()[0]

    # Create new entangled pair with Charlie
    epr_charlie = epr_socket_charlie.create_keep()[0]

    # Extend into GHZ: CNOT from Alice's qubit onto Charlie's
    epr_alice.cnot(epr_charlie)

Key concepts
------------

- **Multiple EPR sockets**: A single ``NetQASMConnection`` can hold EPR sockets
  to multiple remote nodes.
- **Three-party coordination**: Bob acts as both a server (for Alice) and a client
  (to Charlie), using both ``SimulaQronClassicalServer`` and
  ``SimulaQronClassicalClient``.
- **CNOT extends entanglement**: Applying CNOT between two entangled qubits from
  different pairs creates a GHZ state.

Running
-------

::

    cd examples/new-sdk/extendGHZ
    bash run.sh

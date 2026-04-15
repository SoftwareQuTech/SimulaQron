Quantum Teleportation
=====================

This example implements the standard quantum teleportation protocol, where Alice
teleports a qubit to Bob using a pre-shared EPR pair and two classical bits.
Found in ``examples/new-sdk/teleport/``.

The protocol
------------

1. Alice and Bob share an EPR pair (entangled qubits ``A`` and ``B``).
2. Alice has a qubit ``q`` she wants to teleport to Bob.
3. Alice applies ``CNOT(q, A)`` and then ``H(q)``.
4. Alice measures both ``q`` and ``A``, obtaining bits ``a`` and ``b``.
5. Alice sends ``a`` and ``b`` to Bob via a classical message.
6. Bob applies correction gates: X if ``b = 1``, Z if ``a = 1``.
7. Bob's qubit B is now in the same state as Alice's original qubit ``q``.

Alice's code
------------

From ``aliceTest.py`` — Alice creates the EPR pair, performs the teleportation
circuit, and sends the correction bits to Bob::

    async def run_alice(reader: StreamReader, writer: StreamWriter):
        epr_socket = EPRSocket("Bob")

        # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
        sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

        # Create a qubit to teleport
        q = Qubit(sim_conn)
        q.H()
        # Create entanglement
        epr = epr_socket.create_keep()[0]
        # Teleport circuit: CNOT + H + measure both
        q.cnot(epr)
        q.H()
        m1 = q.measure()
        m2 = epr.measure()

        # flush() executes all queued quantum operations
        sim_conn.flush()

        # int(m) extracts the measurement outcome — only valid after flush().
        m1_val = int(m1)
        m2_val = int(m2)
        sim_conn.close()

        # Send correction bits to Bob via classical channel
        message = f"{m1_val}:{m2_val}"
        writer.write(message.encode("utf-8"))

Bob's code
----------

From ``bobTest.py`` — Bob waits for Alice's correction bits, then applies them::

    async def run_bob(reader: StreamReader, writer: StreamWriter):
        # Wait for the classical correction message first
        corrections_bytes = await reader.read(255)
        corrections = corrections_bytes.decode("utf-8").split(":")

        epr_socket = EPRSocket("Alice")
        sim_conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])

        entangled_qubit = epr_socket.recv_keep()[0]

        # Apply teleportation corrections based on Alice's classical message
        if int(corrections[1]) == 1:
            entangled_qubit.X()
        if int(corrections[0]) == 1:
            entangled_qubit.Z()
        meas = entangled_qubit.measure()

        sim_conn.flush()

        meas_val = int(meas)
        sim_conn.close()
        print(f"Bob measurement: {meas_val}")

Key concepts
------------

- **Classical + quantum coordination**: Alice must send classical bits to Bob so he
  can apply corrections.  This requires the client-server pattern
  (``SimulaQronClassicalClient``/``SimulaQronClassicalServer``).
- **Order matters**: Bob may receive his half of the EPR pair earlier, but he cannot
  complete the teleportation recovery step until he has Alice’s two classical bits.
- The teleported state is reconstructed perfectly regardless of the random
  measurement outcomes — the corrections compensate.

Running
-------

::

    cd examples/new-sdk/teleport
    bash run.sh

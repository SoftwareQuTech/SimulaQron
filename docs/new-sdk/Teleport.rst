Quantum Teleportation
=====================

This example implements the standard quantum teleportation protocol, where Alice
teleports a qubit to Bob using a pre-shared EPR pair and two classical bits.
Found in ``examples/new-sdk/teleport/``.

The protocol
------------

#. Alice and Bob share an EPR pair (entangled qubits ``A`` and ``B``).

.. math:: |\Phi^{+}\rangle = = \frac{1}{\sqrt{2}} \left(|0\rangle_A |0\rangle_B + |1\rangle_A |1\rangle_B\right)

#. Alice has a qubit ``Q`` she wants to teleport to Bob.
#. Alice applies ``CNOT(q, A)`` and then ``H(Q)``.
#. Alice measures both ``Q`` and ``A``, obtaining bits ``q`` and ``a``.
#. Alice sends ``q`` and ``a`` to Bob via a classical message.
#. Bob applies correction gates: X if ``a = 1``, Z if ``q = 1``.
#. Bob's qubit B is now in the same state as Alice's original qubit ``Q``.

Alice's code
------------

From ``aliceTest.py`` — Alice creates the EPR pair, performs the teleportation
circuit, and sends the correction bits to Bob::

    async def run_alice(reader: StreamReader, writer: StreamWriter):
        epr_socket = EPRSocket("Bob")

        # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
        # Bob is reached via EPRSocket for quantum and reader/writer for classical.
        sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

        # Create a qubit to teleport
        Q = Qubit(sim_conn)
        Q.H()
        # Create entanglement
        A = epr_socket.create_keep()[0]
        # Teleport circuit: CNOT + H + measure both
        Q.cnot(A)
        Q.H()
        q = Q.measure()
        a = A.measure()

        # flush() executes all queued quantum operations and makes measurement
        # results available.  Before flush(), q and a are just futures/promises.
        sim_conn.flush()

        # int(m) extracts the measurement outcome — only valid after flush().
        q_val = int(q)
        a_val = int(a)
        sim_conn.close()
        message = f"{q_val}:{a_val}"  # noqa: E231
        writer.write(message.encode("utf-8"))
        return q_val, a_val

Bob's code
----------

From ``bobTest.py`` — Bob waits for Alice's correction bits, then applies them::

    async def run_bob(reader: StreamReader, writer: StreamWriter):
        # We wait for the classical message first
        corrections_bytes = await reader.read(255)
        corrections = corrections_bytes.decode("utf-8").split(":")
        (q_val, a_val) = corrections
        epr_socket = EPRSocket("Alice")

        # sim_conn is our connection to the quantum backend (SimulaQron), not to Alice.
        # Alice is reached via EPRSocket for quantum and reader/writer for classical.
        sim_conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])

        B = epr_socket.recv_keep()[0]

        # Apply teleportation corrections based on Alice's classical message
        if int(a_val) == 1:
            B.X()
        if int(q_val) == 1:
            B.Z()
        meas = B.measure()

        # flush() executes all queued quantum operations and makes measurement
        # results available.  Before flush(), meas is just a future/promise.
        sim_conn.flush()

        # int(m) extracts the measurement outcome — only valid after flush().
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

Extending a GHZ State
=====================

This example creates a three-party GHZ (Greenberger-Horne-Zeilinger) state
across Alice, Bob, and Charlie.  Found in ``examples/new-sdk/extendGHZ/``.

A GHZ state is a maximally entangled state shared between three (or more) parties:

.. math:: |GHZ\rangle = \frac{1}{\sqrt{2}} \left(|000\rangle + |111\rangle\right)

The protocol
------------

#. Alice creates an EPR pair in the state :math:`|\Phi^{+}\rangle_{AB_1}` with Bob and tells Bob to proceed.
#. Bob receives his half of an EPR pair that Alice created with him, creates a *new* EPR pair :math:`|\Phi^{+}\rangle_{B_2C}`
   with Charlie, and applies a CNOT with :math:`B_1` as control and :math:`B_2` as target.
#. Bob measures :math:`B_2` in the standard basis and sends the outcome :math:`b_2` to Charlie.
#. Charlie receives his half of an EPR pair that Bob created with him and the measurement outcome :math:`b_2`.
#. Charlie performs an X correction depending on :math:`b_2`, :math:`A`, :math:`B_1` and :math:`C` now share a GHZ state.
#. All three measure their remaining qubits — their outcomes :math:`a`, :math:`b_1` and :math:`c` are correlated.

The communication flow is::

    Alice ──EPR_1──► Bob
    Bob ──EPR_2──► Charlie
    Charlie ──continue──► Bob
    Bob ──b_2──► Charlie
    Charlie ──continue──► Bob
    Bob ──continue──► Alice

Alice's code
------------

From ``aliceTest.py``::

    async def run_alice(reader: StreamReader, writer: StreamWriter) -> int:
        # This is "Alice": the start node of the GHZ chain
        this_node_name = "Alice"
        remote_node_name = "Bob"  # A node with this name *must* exist in "simulaqron_network.json"

        epr_socket = EPRSocket(remote_node_name)

        # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
        # Bob is reached via EPRSocket for quantum and reader/writer for classical.
        sim_conn = NetQASMConnection(this_node_name, epr_sockets=[epr_socket])

        # Create an entangled qubit with Bob
        A = epr_socket.create_keep()[0]

        # We need to flush the EPR pair creation, so the reciever does not timeout on the other side.
        sim_conn.flush()

        writer.write("receive_qubit".encode("utf-8"))
        answer = await reader.read(100)

        assert answer.decode("utf-8") == "continue"

        a = A.measure()

        # flush() executes all queued quantum operations and makes measurement
        # results available.  Before flush(), a is just a future/promise.
        sim_conn.flush()

        # int(a) extracts the measurement outcome — only valid after flush().
        a_val = int(a)
        sim_conn.close()

        print(f"{node_name}: My outcome is '{a_val}'")
        return 0

Bob's code
----------

Bob is the key node — he has EPR sockets to *both* Alice and Charlie. However, Bob also has 2 roles in the protocol.

Bob acts as a *server* when communicating with Alice::

    async def run_bob(reader: StreamReader, writer: StreamWriter) -> int:
        # This is "Bob": the middle node of the GHZ chain
        this_node_name = "Bob"
        start_node_name = "Alice"  # A node with this name *must* exist in "simulaqron_network.json"
        end_node_name = "Charlie"  # A node with this name *must* exist in "simulaqron_network.json"

        message = await reader.read(100)
        assert message.decode("utf-8") == "receive_qubit"

        epr_socket_alice = EPRSocket(start_node_name)
        epr_socket_charlie = EPRSocket(end_node_name)

        sockets = SocketsConfig(network_config, "default", NodeConfigType.APP)

        charlie_client = SimulaQronClassicalClient(sockets)

        # sim_conn is our connection to the quantum backend (SimulaQron), not to
        # Alice or Charlie.  They are reached via EPRSockets for quantum and
        # reader/writer for classical.
        sim_conn = NetQASMConnection(this_node_name, epr_sockets=[epr_socket_alice, epr_socket_charlie])

        # Receive an entangled qubit from Alice
        B_1 = epr_socket_alice.recv_keep()[0]

        # Create a new entangled pair with Charlie
        B_2 = epr_socket_charlie.create_keep()[0]

        # We need to flush the EPR pair creation, so the reciever does not timeout on the other side.
        sim_conn.flush()

        # The next part of the protocol needs to be executed between Bob and Charlie.
        # In this interaction, Bob acts as client
        await charlie_client.connect_and_run(end_node_name, send_to_charlie, sim_conn, B_1, B_2)

        # At this point, we have achieved |GHZ>_{AB_1C}
        # Tell Alice to continue
        writer.write("continue".encode("utf-8"))

        # We can measure the B_1 qubit, part of the GHZ
        b_1 = B_1.measure()

        # flush() executes all queued quantum operations and makes measurement
        # results available. Before flush(), c is just a future/promise.
        sim_conn.flush()

        b_1_val = int(b_1)
        sim_conn.close()
        print(f"{this_node_name}: My outcome is '{b_1_val}'")
        return 0

However, Bob acts as a *client* when comunicating with Charlie::

    async def send_to_charlie(reader: StreamReader, writer: StreamWriter,
                              sim_conn: NetQASMConnection, B_1: Qubit, B_2: Qubit) -> None:
        # Tell Bob to receive the EPR half
        writer.write("receive_qubit".encode("utf-8"))

        # Await for the green light from Charlie
        message = await reader.read(100)
        assert message.decode("utf-8") == "continue"

        # Create the GHZ state by entangling the qubit entangled with Alice
        B_1.cnot(B_2)

        # We now measure the entagled qubit with Charlie
        b_2 = B_2.measure()

        # flush() executes all queued quantum operations and makes measurement
        # results available.  Before flush(), b_2 is just a future/promise.
        sim_conn.flush()

        # int(b_2) extracts the measurement outcome — only valid after flush().
        b_2_val = int(b_2)

        # We send the measurement b_2 to Charlie, for corrections.
        writer.write(f"{b_2_val}".encode("utf-8"))

        # We wait for green light from Charlie, again
        charlie_msg = await reader.read(100)
        assert charlie_msg.decode("utf-8") == "continue"

Charlie's code
--------------

Charlie is the end receiver of the GHZ state. It only needs to communicate with Bob::

    async def run_charlie(reader: StreamReader, writer: StreamWriter) -> int:
        # This is "Charlie": the end node of the GHZ chain
        this_node_name = "Charlie"
        remote_node_name = "Bob"
        message = await reader.read(100)

        assert message.decode("utf-8") == "receive_qubit"
        epr_socket = EPRSocket(remote_node_name)

        # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
        # Bob is reached via EPRSocket for quantum and reader/writer for classical.
        sim_conn = NetQASMConnection(this_node_name, epr_sockets=[epr_socket])

        # Receive an entangled qubit
        C = epr_socket.recv_keep()[0]

        # We need to flush the EPR pair creation, so the reciever does not timeout on the other side.
        sim_conn.flush()

        # Signal Bob to send us the b_2 measurement
        writer.write("continue".encode("utf-8"))

        # Receive b_2 measurement from Bob
        b_2_bytes: bytes = await reader.read(100)
        b_2_val = int(b_2_bytes.decode("utf-8"))

        # Perform an X correction depending on Bob's measurement
        if b_2_val == 1:
            C.X()

        sim_conn.flush()

        # At this point, we have achieved |GHZ>_{AB_1C}
        # Tell Bob to continue
        writer.write("continue".encode("utf-8"))

        # We can measure the C qubit, part of the GHZ
        c = C.measure()

        # flush() executes all queued quantum operations and makes measurement
        # results available.  Before flush(), c is just a future/promise.
        sim_conn.flush()

        # int(c) extracts the measurement outcome — only valid after flush().
        c_val = int(c)
        sim_conn.close()
        print(f"{this_node_name}: My outcome is '{c_val}'")
        return 0


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

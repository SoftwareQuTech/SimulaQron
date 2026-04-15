Template: Getting started
=========================

SimulaQron provides two starter templates in ``examples/new-sdk/``:

- ``template-quantum-local/`` — single node, local qubit operations only
- ``template-client-server/`` — two nodes with classical messaging and quantum operations

Single-node template
--------------------

The simplest possible program: create a qubit, apply gates, measure.
Found in ``examples/new-sdk/template-quantum-local/nodeTest.py``::

    def run_node(this_node_name: str) -> int:
        # sim_conn is our connection to the quantum backend (SimulaQron).
        # All qubit operations are queued through this connection.
        sim_conn = NetQASMConnection(this_node_name)

        # Create a qubit — note we pass sim_conn so the backend knows where
        # to allocate it.
        q = Qubit(sim_conn)

        # Perform some local quantum operations
        q.H()
        q.X()
        m1 = q.measure()

        # flush() executes all queued quantum operations and makes measurement
        # results available.  Before flush(), m1 is just a future/promise.
        sim_conn.flush()

        # int(m) extracts the measurement outcome — only valid after flush().
        m1_val = int(m1)
        sim_conn.close()
        return m1_val

Key points:

- ``NetQASMConnection`` connects to the local SimulaQron backend, not to another node.
- ``Qubit(sim_conn)`` allocates a qubit on that backend.
- Gates like ``H()``, ``X()`` are queued — nothing executes until ``flush()``.
- ``int(m)`` only works after ``flush()``.

Client-server template
----------------------

For two-node programs, one node runs as a **client** and the other as a **server**.
Found in ``examples/new-sdk/template-client-server/``.

The server (``nodeTest-server.py``) starts first and listens for connections::

    server = SimulaQronClassicalServer(sockets_config, "Bob")
    server.register_client_handler(run_bob)
    server.start_serving()

The client (``nodeTest-client.py``) connects to the server::

    client = SimulaQronClassicalClient(sockets_config)
    results = client.run_client("Bob", run_alice)

Both ``run_alice`` and ``run_bob`` receive ``(reader, writer)`` for classical messaging.
Inside these functions you can also create quantum connections::

    async def run_alice(reader: StreamReader, writer: StreamWriter):
        # Classical messaging
        writer.write(b"Hello World")
        answer = await reader.read(100)

        # Quantum operations
        epr_socket = EPRSocket("Bob")
        sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])
        epr = epr_socket.create_keep()[0]
        m = epr.measure()
        sim_conn.flush()
        result = int(m)
        sim_conn.close()

Configuration files
-------------------

``simulaqron_network.json`` defines the nodes and their socket ports::

    [
        {
            "name": "default",
            "nodes":  [
                {
                    "Alice": {
                        "app_socket": ["localhost", 8821],
                        "qnodeos_socket": ["localhost", 8822],
                        "vnode_socket": ["localhost", 8823]
                    }
                },
                {
                    "Bob": {
                        "app_socket": ["localhost", 8831],
                        "qnodeos_socket": ["localhost", 8832],
                        "vnode_socket": ["localhost", 8833]
                    }
                }
            ],
            "topology": null
        }
    ]

``simulaqron_settings.json`` configures the simulation backend::

    {
        "max_qubits": 20,
        "max_registers": 1000,
        "sim_backend": "qutip",
        ...
    }

Use ``qutip`` backend by default. Use ``stabilizer`` when you need Clifford gates.

Running
-------

::

    cd examples/new-sdk/template-client-server
    bash run.sh

New SDK Overview
================

The new SDK is the recommended way to write quantum network programs for SimulaQron.
It uses the **NetQASM** library for quantum operations and SimulaQron's own classical
networking classes for message passing between nodes.

Key concepts
------------

NetQASMConnection (``sim_conn``)
    Your connection to the **quantum backend** (SimulaQron's virtual quantum node).
    This is *not* a connection to another party — it is how your node talks to its
    local simulated quantum hardware.  All qubit operations are queued through this
    connection.

    Create it once and reuse it::

        sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

EPRSocket
    Used to create or receive entangled qubit pairs with a remote node.
    ``create_keep()`` on one side, ``recv_keep()`` on the other::

        # Alice’s side
        epr_socket = EPRSocket("Bob")
        epr = epr_socket.create_keep()[0]
        # Bob’s side
        epr_socket = EPRSocket("Alice")
        epr = epr_socket.recv_keep()[0]

flush()
    Sends all queued quantum operations to the backend and waits for them to complete.
    Before ``flush()``, measurement results are just futures/promises.
    After ``flush()``, you can read them with ``int(m)``::

        m = qubit.measure()
        sim_conn.flush()        # execute everything
        result = int(m)         # NOW this works

    You can call ``flush()`` multiple times on the same connection — this is how
    mid-circuit classical logic works (see :doc:`MidCircuitLogic <MidCircuitLogic>`).

close()
    Similarly to ``flush``, sends all queued quantum operations to the backend, waits
    for them to complete *but also* sends a ``StopSignal`` to the simulaqron backend.
    This signal releases any resource used by the application and closes the connection
    with the simulaqron backend, leaving in a clean state, ready for executing another
    (or the same) application::

        sim_conn.flush()        # execute everything
        result = int(m)         # NOW this works
        simm_conn.close()       # Close the connection with the backend

Qubit
    A qubit allocated on the local quantum backend.  Pass ``sim_conn`` so the
    backend knows where to allocate it::

        q = Qubit(sim_conn)
        q.H()       # Hadamard
        q.X()       # Pauli X

Classical networking
    ``SimulaQronClassicalClient`` and ``SimulaQronClassicalServer`` handle TCP
    connections between nodes.  Your quantum program function receives
    ``(reader, writer)`` for sending/receiving classical messages::

        async def run_alice(reader: StreamReader, writer: StreamWriter):
            writer.write(b"hello")
            reply = await reader.read(255)

    Both ``SimulaQronClassicalClient`` and ``SimulaQronClassicalServer`` classes make use
    of *Python Coroutines* as the main entry points for clients and servers. These are simple
    python functions that are declared using the ``async`` keyword. For more information about
    Python Coroutines, please check the `official python documentation <https://docs.python.org/3/library/asyncio-task.html#coroutines>`_.

File structure
--------------

Every example follows the same structure:

- One Python file per node (e.g. ``aliceTest.py``, ``bobTest.py``)
- ``simulaqron_network.json`` — defines node names and socket ports
- ``simulaqron_settings.json`` — backend settings (``qutip`` by default. For more information check :ref:`SimulaQron backends<sim_backends>`).
- ``run.sh`` — starts the SimulaQron backend and launches all node scripts
- ``terminate.sh`` — stops background processes

To run any example::

    cd examples/new-sdk/<example_name>
    bash run.sh

Examples
--------

The examples are ordered from simplest to most complex:

.. list-table::
    :header-rows: 1
    :widths: 25 75

    * - Example
      - What it teaches
    * - :doc:`Template <Template>`
      - Basic setup: single node with local qubits, and client-server template
    * - :doc:`CorrRNG <CorrRNG>`
      - EPR pairs between two nodes, correlated measurement
    * - :doc:`Teleport <Teleport>`
      - Quantum teleportation with classical correction messages
    * - :doc:`ExtendGHZ <ExtendGHZ>`
      - Three-party entanglement, multiple EPR sockets on one connection
    * - :doc:`MidCircuitLogic <MidCircuitLogic>`
      - Multiple ``flush()`` calls for mid-circuit classical decisions

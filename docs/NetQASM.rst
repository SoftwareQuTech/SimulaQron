The NetQASM interface
=====================

SimulaQron applications are written using the **NetQASM SDK**. This page describes the core concepts and
programming model. For complete working examples, see :doc:`Examples <Examples>`.

------------
Installation
------------

The NetQASM library is included as a dependency of SimulaQron. For the instructions how to install SimulaQron
please check the :doc:`Getting Started<GettingStarted>` section.

--------------
Core concepts
--------------

^^^^^^^^^^^^^^^^^
NetQASMConnection
^^^^^^^^^^^^^^^^^

This objects represent your connection to the **local quantum backend** (SimulaQron's virtual quantum node).
This is *not* a connection to another party — it is how your node talks to its local simulated quantum hardware.
All qubit operations are queued through this connection.

Create it once, use it throughout your program, and close it at the end::

    from netqasm.sdk.external import NetQASMConnection

    conn = NetQASMConnection("Alice")
    # ... queue quantum operations ...
    conn.flush()
    conn.close()

If your program uses EPR pairs, pass the EPR sockets at creation time::

    from netqasm.sdk import EPRSocket

    epr_socket = EPRSocket("Bob")
    conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

^^^^^
Qubit
^^^^^

A qubit allocated on the local quantum backend. The qubit gets initialized to the :math:`|0\rangle` state.
Pass the connection so the backend knows where to allocate it::

    from netqasm.sdk import Qubit

    q = Qubit(conn)
    q.H()           # Hadamard
    q.X()           # Pauli X
    q.cnot(other)   # CNOT with another qubit
    m = q.measure()

Gates are **queued** — nothing executes until you call ``flush()``.

^^^^^^^^^
EPRSocket
^^^^^^^^^

Used to create or receive entangled qubit pairs with a remote node::

    from netqasm.sdk import EPRSocket

    # On Alice's side:
    epr_socket = EPRSocket("Bob")
    epr = epr_socket.create_keep()[0]

    # On Bob's side:
    epr_socket = EPRSocket("Alice")
    epr = epr_socket.recv_keep()[0]

^^^^^^^
flush()
^^^^^^^

The **sync point** that executes all queued quantum operations and makes measurement results available.
Before ``flush()``, measurement results are just futures/promises. After ``flush()``, you can read them
with ``int(m)``::

    m = q.measure()
    conn.flush()          # execute everything queued so far
    result = int(m)       # NOW this works

You can call ``flush()`` multiple times on the same connection. This enables **mid-circuit classical logic**
— measure, read the result, and decide what to do next::

    m1 = q.measure()
    conn.flush()
    if int(m1) == 1:
        other_qubit.X()   # conditional correction
    conn.flush()

See the mid-circuit logic example in :doc:`Examples <Examples>` for a full demonstration.

---------------
Minimal example
---------------

A single-node program that creates a qubit, applies a Hadamard gate, and measures::

    from netqasm.runtime.settings import set_simulator
    set_simulator("simulaqron")
    from netqasm.sdk.external import NetQASMConnection
    from netqasm.sdk import Qubit

    conn = NetQASMConnection("Alice")
    q = Qubit(conn)
    q.H()
    m = q.measure()
    conn.flush()
    print("Measurement outcome:", int(m))
    conn.close()

If you want to run this minimal example, remember to start the SimulaQron backend before executing the code:
``simulaqron start``.

--------------------
Two-node EPR example
--------------------

Alice and Bob generate an EPR pair and each measure their qubit to get correlated random numbers.

**Alice** (creates the EPR pair)::

    epr_socket = EPRSocket("Bob")
    conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])
    epr = epr_socket.create_keep()[0]
    m = epr.measure()
    conn.flush()
    print("Alice:", int(m))
    conn.close()

**Bob** (receives the EPR pair)::

    epr_socket = EPRSocket("Alice")
    conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])
    epr = epr_socket.recv_keep()[0]
    m = epr.measure()
    conn.flush()
    print("Bob:", int(m))
    conn.close()

Both sides will print the same random number (0 or 1), demonstrating quantum correlation. A full working example
of this can be found in the ``new-sdk/corrRNG`` example. See the :doc:`Correlated RNG<new-sdk/CorrRNG>` section for
more details.

-----------------------
Classical communication
-----------------------

For exchanging classical messages between nodes (e.g. measurement outcomes for teleportation corrections),
SimulaQron provides ``SimulaQronClassicalClient`` and ``SimulaQronClassicalServer``.

Your quantum program function receives ``(reader, writer)`` — standard asyncio streams — for sending and
receiving classical messages::

    from asyncio import StreamReader, StreamWriter

    async def run_alice(reader: StreamReader, writer: StreamWriter):
        # Quantum operations
        conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])
        m = epr_socket.create_keep()[0].measure()
        conn.flush()

        # Send classical message to Bob
        writer.write(str(int(m)).encode("utf-8"))
        conn.close()

    async def run_bob(reader: StreamReader, writer: StreamWriter):
        # Receive classical message from Alice
        data = await reader.read(255)
        correction = int(data.decode("utf-8"))

        # Use correction in quantum operations
        conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])
        epr = epr_socket.recv_keep()[0]
        if correction == 1:
            epr.X()
        conn.flush()
        conn.close()

See the :doc:`Template <new-sdk/Template>` page for how to set up the client and server, and the
:doc:`teleportation example <new-sdk/Teleport>` for a complete two-node program with classical messaging.

-----------------------
Configuration
-----------------------

Each program needs two configuration files in its directory:

* ``simulaqron_network.json`` — defines the nodes and their socket ports. See :doc:`Configuring the Network <ConfNodes>`
  for details.
* ``simulaqron_settings.json`` — configures the simulation backend and other settings. See the
  Settings section in :doc:`Getting Started <GettingStarted>`.

The ``qutip`` backend is used by default and is recommended unless you need Clifford gates (use
``stabilizer`` in that case).

-----------------------
Further reading
-----------------------

* :doc:`Examples <Examples>` — complete working examples from simple to complex
* :doc:`New SDK Overview <new-sdk/Overview>` — detailed SDK concepts and file structure
* `NetQASM library documentation <https://netqasm.readthedocs.io/en/latest/>`_

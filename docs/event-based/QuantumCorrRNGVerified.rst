Quantum Correlated RNG with Verification
=========================================

Extends the previous example by adding a classical verification step after the
quantum measurement.  After both nodes measure their EPR halves, Alice sends her
result to Bob so he can confirm the correlation.
Found in ``examples/event-based/quantumCorrRNGVerified/``.

This demonstrates the full cycle:
**classical negotiation → quantum operation → classical verification**

The protocol
------------

1. Alice sends "generate randomness?" to Bob.
2. Bob replies "yes", then both create an EPR pair and measure.
3. Alice sends her measurement result to Bob.
4. Bob compares both results and sends back a verification message.

Alice's state diagram
---------------------

::

    (connect)
       │ send "generate randomness?"
       ▼
    WAITING_ACCEPT
       │ recv "yes" → EPR create + measure, send result to Bob
       ▼
    WAITING_VERIFICATION
       │ recv "verified: ..."
       ▼
      DONE

Bob's state diagram
-------------------

::

    WAITING_PROPOSAL
       │ recv "generate randomness?" → send "yes", EPR recv + measure
       ▼
    WAITING_ALICE_RESULT
       │ recv Alice's bit → compare, send verdict
       ▼
      DONE

Multi-state quantum protocol
-----------------------------

The key difference from the simple version: Bob now has **two states** after the
quantum operation.  His handler stores the measurement result, and a second handler
processes Alice's result::

    bob_result = None  # module-level storage

    async def handle_generate(writer: StreamWriter) -> str:
        global bob_result

        # Classical: agree
        writer.write("yes".encode("utf-8"))
        await writer.drain()

        # Quantum: receive EPR pair and measure
        epr_socket = EPRSocket("Alice")
        sim_conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])
        epr = epr_socket.recv_keep()[0]
        m = epr.measure()
        sim_conn.flush()

        bob_result = int(m)
        sim_conn.close()
        return STATE_WAITING_ALICE_RESULT

    async def handle_alice_result(writer: StreamWriter, alice_result: int) -> str:
        match = alice_result == bob_result
        verdict = f"verified: Alice={alice_result}, Bob={bob_result}, match={match}"
        writer.write(verdict.encode("utf-8"))
        await writer.drain()
        return STATE_DONE

Handling variable messages
--------------------------

In ``WAITING_ALICE_RESULT``, the message content is Alice's measurement bit — it
could be "0" or "1".  Since the exact message is not known ahead of time, Bob's
event loop handles this state specially rather than through the dispatch table::

    while state != STATE_DONE:
        data = await reader.read(255)
        msg = data.decode("utf-8")

        # Special handling: in WAITING_ALICE_RESULT, the message IS the data
        if state == STATE_WAITING_ALICE_RESULT:
            alice_bit = int(msg)
            state = await handle_alice_result(writer, alice_bit)
            continue

        # Normal dispatch for other states
        handler = BOB_DISPATCH.get((state, msg))
        ...

Key concepts
------------

- **Multi-phase protocols**: The state machine naturally handles protocols with
  multiple phases (negotiate → quantum → verify).
- **Data-carrying messages**: Not all messages are fixed strings.  When a state
  expects variable data (like a measurement result), handle it directly in the
  event loop rather than through the dispatch table.
- **Cross-handler state**: Use module-level variables (like ``bob_result``) to
  pass data between handlers that execute in different states.

Running
-------

::

    cd examples/event-based/quantumCorrRNGVerified
    bash run.sh

Expected output::

    Alice: sending 'generate randomness?'
    Bob: sending 'yes'
    Alice: my random bit is 0
    Bob: my random bit is 0
    Bob: verified: Alice=0, Bob=0, match=True

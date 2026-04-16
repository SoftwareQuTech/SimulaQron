Polite Ping-Pong: The State Machine Pattern
============================================

Extends the basic ping-pong into a proper state machine with dispatch tables.
Alice and Bob have a polite exchange: ping, pong, thank you, you're welcome.
Found in ``examples/event-based/politePingPong/``.

This is still purely classical, but introduces the **state machine pattern**
that all subsequent quantum examples will use.

Alice's state diagram
---------------------

::

    (connect)
       │ send "ping"
       ▼
    WAITING_PONG
       │ recv "pong" → send "thank you"
       ▼
    WAITING_YOURE_WELCOME
       │ recv "you're welcome"
       ▼
      DONE

Alice's dispatch table
----------------------

::

    ALICE_DISPATCH = {
        (STATE_WAITING_PONG,          "pong"):           handle_pong,
        (STATE_WAITING_YOURE_WELCOME, "you're welcome"): handle_youre_welcome,
    }

Each handler is a focused function that performs one action and returns the next state::

    async def handle_pong(writer: StreamWriter) -> str:
        reply = "thank you"
        writer.write(reply.encode("utf-8"))
        await writer.drain()
        return STATE_WAITING_YOURE_WELCOME

The event loop
--------------

The event loop is generic — it works for any protocol by just changing the dispatch
table and initial state::

    async def run_alice(reader: StreamReader, writer: StreamWriter):
        # Initial action (before the loop)
        writer.write(b"ping")
        await writer.drain()

        state = STATE_WAITING_PONG

        while state != STATE_DONE:
            data = await reader.read(255)
            if not data:
                break
            msg = data.decode("utf-8")

            handler = ALICE_DISPATCH.get((state, msg))
            if handler is None:
                print(f"no transition for '{msg}' — ignoring.")
                continue

            state = await handler(writer)

Key concepts
------------

- **Dispatch table = state machine**: the ``(state, message) → handler`` mapping
  *is* the protocol definition.  Every valid transition is listed; anything not
  listed is automatically rejected.
- **Handlers are independent**: each handler only knows about its own transition,
  making the code modular and easy to extend.
- **The event loop is reusable**: the same loop structure works for every example
  that follows.

Bob's side
----------

Bob uses the same pattern with his own states (``WAITING_PING``, ``WAITING_THANKS``,
``DONE``) and dispatch table.  See ``politeBob.py`` for the full code.

Running
-------

::

    cd examples/event-based/politePingPong
    bash run.sh

"""
Test for the eventBased/politePingPong example.

Runs both Alice and Bob in a single process using asyncio tasks.
Exercises the (state, message) dispatch table state machine and verifies
that each node traverses the expected sequence of states.
"""
import asyncio
import pytest


# ── Bob state machine (mirrors politeBob.py) ─────────────────────────────────

STATE_WAITING_PING   = "WAITING_PING"
STATE_WAITING_THANKS = "WAITING_THANKS"
STATE_DONE           = "DONE"


async def bob_handler(reader, writer):
    """
    In-process replica of run_bob from politeBob.py.

    Returns the sequence of (state_before, message, reply) triples so the
    test can check every transition.
    """
    log = []
    state = STATE_WAITING_PING

    while state != STATE_DONE:
        data = await reader.read(255)
        if not data:
            break
        msg = data.decode("utf-8")

        if state == STATE_WAITING_PING and msg == "ping":
            reply = "pong"
            writer.write(reply.encode("utf-8"))
            await writer.drain()
            log.append((state, msg, reply))
            state = STATE_WAITING_THANKS

        elif state == STATE_WAITING_THANKS and msg == "thank you":
            reply = "you're welcome"
            writer.write(reply.encode("utf-8"))
            await writer.drain()
            log.append((state, msg, reply))
            state = STATE_DONE

        else:
            # Invalid transition — ignore (no reply, state unchanged)
            log.append((state, msg, None))

    return log


# ── Alice state machine (mirrors politeAlice.py) ──────────────────────────────

STATE_WAITING_PONG          = "WAITING_PONG"
STATE_WAITING_YOURE_WELCOME = "WAITING_YOURE_WELCOME"
ALICE_DONE                  = "DONE"


async def alice_handler(port):
    """
    In-process replica of run_alice from politeAlice.py.

    Returns the sequence of (state_before, sent, received) triples.
    """
    reader, writer = await asyncio.open_connection("localhost", port)
    log = []
    state = STATE_WAITING_PONG

    # Initial action: send "ping" before entering the loop
    opening = "ping"
    writer.write(opening.encode("utf-8"))
    await writer.drain()

    while state != ALICE_DONE:
        data = await reader.read(255)
        if not data:
            break
        msg = data.decode("utf-8")

        if state == STATE_WAITING_PONG and msg == "pong":
            reply = "thank you"
            writer.write(reply.encode("utf-8"))
            await writer.drain()
            log.append((state, msg, reply))
            state = STATE_WAITING_YOURE_WELCOME

        elif state == STATE_WAITING_YOURE_WELCOME and msg == "you're welcome":
            log.append((state, msg, None))
            state = ALICE_DONE

        else:
            log.append((state, msg, None))

    writer.close()
    await writer.wait_closed()
    return log


# ── Test harness ──────────────────────────────────────────────────────────────

async def run_exchange(port):
    """Run a complete polite ping-pong exchange and return both logs."""
    bob_log = []
    handler_done = asyncio.Event()

    async def on_connect(reader, writer):
        result = await bob_handler(reader, writer)
        bob_log.extend(result)
        handler_done.set()

    server = await asyncio.start_server(on_connect, "localhost", port)

    alice_log = await asyncio.create_task(alice_handler(port))

    await asyncio.wait_for(handler_done.wait(), timeout=5.0)
    server.close()

    return alice_log, bob_log


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_full_exchange_completes():
    """The happy path: Alice and Bob complete the full polite exchange."""
    alice_log, bob_log = asyncio.run(run_exchange(19877))

    # Bob's two transitions
    assert len(bob_log) == 2
    assert bob_log[0] == (STATE_WAITING_PING,   "ping",      "pong")
    assert bob_log[1] == (STATE_WAITING_THANKS, "thank you", "you're welcome")

    # Alice's two transitions
    assert len(alice_log) == 2
    assert alice_log[0] == (STATE_WAITING_PONG,          "pong",           "thank you")
    assert alice_log[1] == (STATE_WAITING_YOURE_WELCOME, "you're welcome", None)


def test_bob_rejects_unexpected_message_in_wrong_state():
    """
    If Bob receives an unexpected message it stays in its current state
    (the invalid-transition branch logs the message with reply=None).
    """

    async def run():
        log = []
        handler_done = asyncio.Event()

        async def on_connect(reader, writer):
            result = await bob_handler(reader, writer)
            log.extend(result)
            handler_done.set()

        server = await asyncio.start_server(on_connect, "localhost", 19878)

        # Alice sends "thank you" first (wrong message for WAITING_PING),
        # then the correct "ping".
        reader, writer = await asyncio.open_connection("localhost", 19878)

        # Wrong message in WAITING_PING state
        writer.write(b"thank you")
        await writer.drain()
        # Give Bob time to process (no reply expected)
        await asyncio.sleep(0.05)

        # Now the correct sequence
        writer.write(b"ping")
        await writer.drain()
        reply = await reader.read(255)
        assert reply.decode() == "pong"

        writer.write(b"thank you")
        await writer.drain()
        reply2 = await reader.read(255)
        assert reply2.decode() == "you're welcome"

        writer.close()
        await writer.wait_closed()
        await asyncio.wait_for(handler_done.wait(), timeout=5.0)
        server.close()
        return log

    log = asyncio.run(run())

    # First entry: invalid transition (no reply)
    assert log[0] == (STATE_WAITING_PING, "thank you", None)
    # Second and third: normal transitions
    assert log[1] == (STATE_WAITING_PING,   "ping",      "pong")
    assert log[2] == (STATE_WAITING_THANKS, "thank you", "you're welcome")

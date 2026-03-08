"""
Test for the eventBased/pingPong example.

Runs both Alice and Bob in a single process using asyncio tasks.
"""
import asyncio
import pytest


async def bob_handler(reader, writer):
    """Bob's event loop — same logic as the example."""
    replies = []
    while True:
        data = await reader.read(255)
        if not data:
            break
        message = data.decode("utf-8")
        if message == "ping":
            reply = "pong"
        else:
            reply = "no way!"
        replies.append((message, reply))
        writer.write(reply.encode("utf-8"))
        await writer.drain()
    return replies


async def run_scenario(port, messages):
    """Run a full ping-pong and return Alice's results + Bob's log."""
    bob_log = []
    handler_done = asyncio.Event()

    async def on_connect(reader, writer):
        result = await bob_handler(reader, writer)
        bob_log.extend(result)
        handler_done.set()

    server = await asyncio.start_server(on_connect, "localhost", port)

    # Alice connects and exchanges messages
    alice_task = asyncio.create_task(_run_alice(port, messages))
    alice_results = await alice_task

    # Wait for Bob's handler to finish
    await asyncio.wait_for(handler_done.wait(), timeout=5.0)

    # Shut down
    server.close()

    return alice_results, bob_log


async def _run_alice(port, messages):
    r, w = await asyncio.open_connection("localhost", port)
    results = []
    for msg in messages:
        w.write(msg.encode("utf-8"))
        await w.drain()
        reply_data = await r.read(255)
        results.append((msg, reply_data.decode("utf-8")))
    w.close()
    await w.wait_closed()
    return results


@pytest.mark.parametrize("messages,expected", [
    (
        ["ping"],
        [("ping", "pong")],
    ),
    (
        ["hello"],
        [("hello", "no way!")],
    ),
    (
        ["ping", "ping", "hello", "ping"],
        [("ping", "pong"), ("ping", "pong"), ("hello", "no way!"), ("ping", "pong")],
    ),
    (
        ["hi", "what", "test"],
        [("hi", "no way!"), ("what", "no way!"), ("test", "no way!")],
    ),
])
def test_ping_pong(messages, expected):
    alice, bob = asyncio.run(run_scenario(19876, messages))
    assert alice == expected
    assert bob == expected

"""
Polite Ping-Pong — Bob (server).

Bob's behaviour is defined as a finite state machine.  The event loop
reads one message at a time, looks up the (current_state, message) pair
in the dispatch table, and calls the corresponding handler.  The handler
performs an action (typically sending a reply) and returns the next state.

Bob's state diagram
-------------------

                      recv "ping"          send "pong"
    WAITING_PING  ─────────────────────────────────────►  WAITING_THANKS
                                                                │
                                                   recv "thank you"
                                                   send "you're welcome"
                                                                │
                                                                ▼
                                                              DONE

As a transition table (this maps directly to BOB_DISPATCH below):

    Current state    │ Message received │ Action                 │ Next state
    ─────────────────┼──────────────────┼────────────────────────┼──────────────────
    WAITING_PING     │ "ping"           │ send "pong"            │ WAITING_THANKS
    WAITING_THANKS   │ "thank you"      │ send "you're welcome"  │ DONE

Any (state, message) pair NOT in the table is rejected with a warning;
the state does not change and the loop continues.
"""
from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


# ── States ───────────────────────────────────────────────────────────────────
# Each constant names a state in Bob's state machine.
# The string value is used in log output so keep it human-readable.

STATE_WAITING_PING   = "WAITING_PING"   # noqa: E221
STATE_WAITING_THANKS = "WAITING_THANKS"
STATE_DONE           = "DONE"           # noqa: E221


# ── Handlers ─────────────────────────────────────────────────────────────────
# One handler per valid transition.  A handler receives the writer (to send
# a reply) and returns the next state.  It does NOT need to validate the
# current state — that is guaranteed by the dispatch table.

async def handle_ping(writer: StreamWriter) -> str:
    """
    Transition: WAITING_PING ──[recv "ping"]──► WAITING_THANKS

    Bob receives a ping and replies with a pong.
    """
    reply = "pong"
    print(f"Bob: sending '{reply}'", flush=True)
    writer.write(reply.encode("utf-8"))
    await writer.drain()
    return STATE_WAITING_THANKS


async def handle_thank_you(writer: StreamWriter) -> str:
    """
    Transition: WAITING_THANKS ──[recv "thank you"]──► DONE

    Bob receives a thank you and replies politely before finishing.
    """
    reply = "you're welcome"
    print(f"Bob: sending '{reply}'", flush=True)
    writer.write(reply.encode("utf-8"))
    await writer.drain()
    return STATE_DONE


# ── Dispatch table ────────────────────────────────────────────────────────────
# Maps (current_state, message) → handler.
# This table IS the state machine: every valid transition is listed here,
# and anything not listed is automatically an invalid transition.

BOB_DISPATCH = {
    (STATE_WAITING_PING,   "ping"):      handle_ping,  # noqa: E241
    (STATE_WAITING_THANKS, "thank you"): handle_thank_you,
}


# ── Event loop ────────────────────────────────────────────────────────────────

async def run_bob(reader: StreamReader, writer: StreamWriter):
    """
    Bob's event loop.

    Repeatedly:
      1. Read the next message from Alice.
      2. Look up (current_state, message) in BOB_DISPATCH.
      3. If found, call the handler and move to the returned next state.
      4. If not found, log a warning and stay in the current state.
    Loop exits when the state reaches STATE_DONE or the connection drops.
    """
    print("Bob: Alice connected.", flush=True)
    state = STATE_WAITING_PING

    while state != STATE_DONE:
        # 1. Wait for the next event (message from Alice)
        data = await reader.read(255)
        if not data:
            print(f"Bob [{state}]: connection dropped unexpectedly.", flush=True)
            break
        msg = data.decode("utf-8")
        print(f"Bob [{state}]: received '{msg}'", flush=True)

        # 2. Look up the transition
        handler = BOB_DISPATCH.get((state, msg))

        # 3a. Invalid transition — warn and stay in current state
        if handler is None:
            print(
                f"Bob [{state}]: no transition for message '{msg}' — ignoring.",
                flush=True,
            )
            continue

        # 3b. Valid transition — execute handler, advance state
        state = await handler(writer)

    print(f"Bob: event loop finished (final state: {state}).", flush=True)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _here = Path(__file__).parent
    simulaqron_settings.read_from_file(_here / "simulaqron_settings.json")
    network_config.read_from_file(_here / "simulaqron_network.json")

    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)
    server = SimulaQronClassicalServer(sockets_config, "Bob")
    server.register_client_handler(run_bob)

    print("Bob: starting server...")
    server.start_serving()

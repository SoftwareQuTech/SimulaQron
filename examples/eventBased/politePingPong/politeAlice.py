"""
Polite Ping-Pong — Alice (client).

Alice's behaviour is defined as a finite state machine.  She always
initiates the exchange by sending "ping" before entering the event loop.
The event loop then reads one message at a time, looks up the
(current_state, message) pair in the dispatch table, and calls the
corresponding handler.  The handler performs an action and returns the
next state.

Alice's state diagram
---------------------

                              ┌─ (connect) ─────────────────────────────┐
                              │  send "ping"                            │
                              ▼                                         │
    ──────────────►  WAITING_PONG                                    (start)
                       │
            recv "pong"
            send "thank you"
                       │
                       ▼
            WAITING_YOURE_WELCOME
                       │
            recv "you're welcome"
                       │
                       ▼
                      DONE

As a transition table (this maps directly to ALICE_DISPATCH below):

    Current state          │ Message received   │ Action           │ Next state
    ───────────────────────┼────────────────────┼──────────────────┼──────────────────────
    WAITING_PONG           │ "pong"             │ send "thank you" │ WAITING_YOURE_WELCOME
    WAITING_YOURE_WELCOME  │ "you're welcome"   │ (none)           │ DONE

Any (state, message) pair NOT in the table is rejected with a warning;
the state does not change and the loop continues.

Note: the initial "ping" is sent before the loop starts — it is not a
state transition but simply Alice's opening move as the initiator.
"""
from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


# ── States ───────────────────────────────────────────────────────────────────

STATE_WAITING_PONG          = "WAITING_PONG"           # noqa: E221
STATE_WAITING_YOURE_WELCOME = "WAITING_YOURE_WELCOME"
STATE_DONE                  = "DONE"                    # noqa: E221


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_pong(writer: StreamWriter) -> str:
    """
    Transition: WAITING_PONG ──[recv "pong"]──► WAITING_YOURE_WELCOME

    Alice receives a pong and politely says thank you.
    """
    reply = "thank you"
    print(f"Alice: sending '{reply}'")
    writer.write(reply.encode("utf-8"))
    await writer.drain()
    return STATE_WAITING_YOURE_WELCOME


async def handle_youre_welcome(writer: StreamWriter) -> str:
    """
    Transition: WAITING_YOURE_WELCOME ──[recv "you're welcome"]──► DONE

    Alice receives the final courtesy and the exchange is complete.
    No reply is needed.
    """
    print("Alice: received 'you're welcome' — exchange complete.")
    return STATE_DONE


# ── Dispatch table ────────────────────────────────────────────────────────────
# Maps (current_state, message) → handler.
# This table IS the state machine: every valid transition is listed here,
# and anything not listed is automatically an invalid transition.

ALICE_DISPATCH = {
    (STATE_WAITING_PONG,          "pong"):           handle_pong,  # noqa: E241
    (STATE_WAITING_YOURE_WELCOME, "you're welcome"): handle_youre_welcome,
}


# ── Event loop ────────────────────────────────────────────────────────────────

async def run_alice(reader: StreamReader, writer: StreamWriter):
    """
    Alice's event loop.

    Alice initiates by sending "ping", then enters the state machine loop:
      1. Read the next message from Bob.
      2. Look up (current_state, message) in ALICE_DISPATCH.
      3. If found, call the handler and move to the returned next state.
      4. If not found, log a warning and stay in the current state.
    Loop exits when the state reaches STATE_DONE or the connection drops.
    """
    # Initial action: Alice always opens the exchange with a ping.
    # This happens before the loop — it is not a state transition.
    opening = "ping"
    print(f"Alice: sending '{opening}'")
    writer.write(opening.encode("utf-8"))
    await writer.drain()

    state = STATE_WAITING_PONG

    while state != STATE_DONE:
        # 1. Wait for the next event (message from Bob)
        data = await reader.read(255)
        if not data:
            print(f"Alice [{state}]: connection dropped unexpectedly.")
            break
        msg = data.decode("utf-8")
        print(f"Alice [{state}]: received '{msg}'")

        # 2. Look up the transition
        handler = ALICE_DISPATCH.get((state, msg))

        # 3a. Invalid transition — warn and stay in current state
        if handler is None:
            print(
                f"Alice [{state}]: no transition for message '{msg}' — ignoring."
            )
            continue

        # 3b. Valid transition — execute handler, advance state
        state = await handler(writer)

    print(f"Alice: event loop finished (final state: {state}).")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _here = Path(__file__).parent
    simulaqron_settings.read_from_file(_here / "simulaqron_settings.json")
    network_config.read_from_file(_here / "simulaqron_network.json")

    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)
    client = SimulaQronClassicalClient(sockets_config)

    print("Alice: connecting to Bob...")
    client.run_client("Bob", run_alice)

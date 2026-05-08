"""
Ping-Pong — Bob (server).

Bob listens for Alice's PINGs and replies with PONGs.
Both sides know NUM_ROUNDS, so no BYE is needed — Bob stops after
sending the last PONG and the connection closes naturally.

This is a purely classical example — no quantum operations.
It demonstrates the event-based state-machine pattern used throughout
SimulaQron examples.

Bob's state diagram
-------------------

          ┌─ (connect) ──────────────────────────────────────┐
          │                                                   │
          ▼                                                   │
        IDLE ──[recv "PING"]──► PLAYING                   (start)
                                    │
                               send "PONG"
                                    │
                                    ▼
                                  IDLE  (next round)
                          ... after NUM_ROUNDS ...
                                    │
                               recv "PING" (last)
                                    ▼
                                  DONE

Transition table:

    State    │ Event        │ Action       │ Next state
    ─────────┼──────────────┼──────────────┼─────────────
    IDLE     │ recv "PING"  │ —            │ PLAYING
    PLAYING  │ (entry)      │ send "PONG"  │ IDLE
    PLAYING  │ (entry)      │ (last round) │ DONE

    PLAYING → IDLE/DONE is an *entry action*: Bob sends PONG immediately
    on entering PLAYING, before waiting for the next message.
"""

from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


NUM_ROUNDS = 5

# ── States ───────────────────────────────────────────────────────────────────

STATE_IDLE    = "IDLE"     # noqa: E221
STATE_PLAYING = "PLAYING"  # noqa: E221
STATE_DONE    = "DONE"     # noqa: E221


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_ping(_writer: StreamWriter) -> str:
    """Transition: IDLE ──[recv "PING"]──► PLAYING"""
    print("Bob: received PING", flush=True)
    return STATE_PLAYING


# ── Dispatch table ────────────────────────────────────────────────────────────

BOB_DISPATCH = {
    (STATE_IDLE, "PING"): handle_ping,
}


# ── Event loop ────────────────────────────────────────────────────────────────

async def run_bob(reader: StreamReader, writer: StreamWriter) -> None:
    print("Bob: Alice connected.", flush=True)
    rounds_done = 0
    state = STATE_IDLE

    while state != STATE_DONE:
        # Entry action: PLAYING → send PONG → IDLE (or DONE)
        if state == STATE_PLAYING:
            rounds_done += 1
            writer.write(b"PONG\n")
            print(f"Bob [round {rounds_done}]: sent PONG", flush=True)
            state = STATE_IDLE if rounds_done < NUM_ROUNDS else STATE_DONE
            continue

        data = await reader.readline()
        if not data:
            print(f"Bob [{state}]: connection dropped unexpectedly.", flush=True)
            break
        # Since reader.readLine() reads until newline is found, and returns the string
        # with the newline character, we need to get rid of it to correctly transition
        # to the next stage of the state machine.
        msg = data.decode("utf-8").replace("\n", "")
        print(f"Bob [{state}]: received '{msg}'", flush=True)

        handler = BOB_DISPATCH.get((state, msg))

        if handler is None:
            print(
                f"Bob [{state}]: no transition for '{msg}' — ignoring.",
                flush=True,
            )
            continue

        state = await handler(writer)

    print(f"Bob: event loop finished (final state: {state}).", flush=True)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Load configuration files — paths are relative to this script's location
    # so the script can be run from any working directory.
    _here = Path(__file__).parent
    simulaqron_settings.read_from_file(_here / "simulaqron_settings.json")
    network_config.read_from_file(_here / "simulaqron_network.json")

    # Set up Bob's server using the network configuration
    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)
    server = SimulaQronClassicalServer(sockets_config, "Bob")
    server.register_client_handler(run_bob)

    print("Bob: starting server...")
    server.start_serving()

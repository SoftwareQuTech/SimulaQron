"""
Ping-Pong — Alice (client).

Alice connects to Bob and they exchange PING / PONG messages for NUM_ROUNDS
rounds.  Both sides know NUM_ROUNDS, so no BYE is needed — the connection
simply closes after the last round.

This is a purely classical example — no quantum operations.
It demonstrates the event-based state-machine pattern used throughout
SimulaQron examples.

Alice's state diagram
---------------------

          ┌─ (connect) ──────────────────────────────────────┐
          │                                                   │
          ▼                                                   │
        IDLE ──[send "PING"]──► PLAYING                   (start)
                                    │
                               recv "PONG"
                                    │
                                    ▼
                                  IDLE  (next round)
                          ... after NUM_ROUNDS ...
                                    │
                               recv "PONG" (last)
                                    ▼
                                  DONE

Transition table:

    State    │ Event        │ Action       │ Next state
    ─────────┼──────────────┼──────────────┼─────────────
    IDLE     │ (entry)      │ send "PING"  │ PLAYING
    PLAYING  │ recv "PONG"  │ —            │ IDLE
    PLAYING  │ recv "PONG"  │ (last round) │ DONE

    IDLE → PLAYING is an *entry action*: Alice sends PING immediately on
    entering IDLE, before waiting for the next message.
"""

from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


NUM_ROUNDS = 5

# ── States ───────────────────────────────────────────────────────────────────

STATE_IDLE    = "IDLE"     # noqa: E221
STATE_PLAYING = "PLAYING"  # noqa: E221
STATE_DONE    = "DONE"     # noqa: E221


# ── Event loop ───────────────────────────────────────────────────────────────

async def run_alice(reader: StreamReader, writer: StreamWriter) -> None:
    rounds_done = 0

    async def handle_pong(_writer: StreamWriter) -> str:
        """Transition: PLAYING ──[recv "PONG"]──► IDLE (or DONE)"""
        nonlocal rounds_done
        print(f"Alice [round {rounds_done}]: received PONG")
        if rounds_done < NUM_ROUNDS:
            return STATE_IDLE
        return STATE_DONE

    dispatch = {
        (STATE_PLAYING, "PONG"): handle_pong,
    }

    state = STATE_IDLE

    while state != STATE_DONE:
        # Entry action: IDLE → send PING → PLAYING
        if state == STATE_IDLE:
            rounds_done += 1
            writer.write(b"PING\n")
            print(f"Alice [round {rounds_done}]: sent PING")
            state = STATE_PLAYING

        data = await reader.readline()
        if not data:
            print(f"Alice [{state}]: connection dropped unexpectedly.")
            break
        msg = data.decode("utf-8")

        handler = dispatch.get((state, msg))

        if handler is None:
            print(f"Alice [{state}]: no transition for '{msg}' — ignoring.")
            continue

        state = await handler(writer)

    print(f"Alice: event loop finished (final state: {state}).")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Load configuration files — paths are relative to this script's location
    # so the script can be run from any working directory.
    _here = Path(__file__).parent
    simulaqron_settings.read_from_file(_here / "simulaqron_settings.json")
    network_config.read_from_file(_here / "simulaqron_network.json")

    # Set up Alice's client using the network configuration
    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)
    client = SimulaQronClassicalClient(sockets_config)

    print("Alice: connecting to Bob...")
    client.run_client("Bob", run_alice)

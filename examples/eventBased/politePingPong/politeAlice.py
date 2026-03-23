"""
Polite Ping-Pong — Alice (client).

Alice waits for Bob's "READY" signal before sending each "PING".  After
NUM_ROUNDS pings she sends "BYE" instead, ending the exchange.

Alice's state diagram
---------------------

              ┌─ (connect) ──────────────────────────────────────────┐
              │                                                       │
              ▼                                                       │
    WAITING_FOR_READY ──[recv "READY"]──► WAITING_FOR_PONG        (start)
                                              │
                                     recv "PONG"
                                              │
                                              ▼
                                    WAITING_FOR_READY  (next round)
                                      ... after NUM_ROUNDS ...
                                              │
                                     recv "READY"  (last)
                                     send "BYE"
                                              ▼
                                            DONE

Transition table:

    Current state       │ Message  │ Action                      │ Next state
    ────────────────────┼──────────┼─────────────────────────────┼──────────────────
    WAITING_FOR_READY   │ "READY"  │ send "PING" (or "BYE")      │ WAITING_FOR_PONG
                        │          │                             │  (or DONE)
    WAITING_FOR_PONG    │ "PONG"   │ —                           │ WAITING_FOR_READY
"""
from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


NUM_ROUNDS = 5

# ── States ───────────────────────────────────────────────────────────────────

STATE_WAITING_FOR_READY = "WAITING_FOR_READY"
STATE_WAITING_FOR_PONG  = "WAITING_FOR_PONG"   # noqa: E221
STATE_DONE              = "DONE"                # noqa: E221


# ── Event loop ───────────────────────────────────────────────────────────────

async def run_alice(reader: StreamReader, writer: StreamWriter) -> None:
    rounds_left = NUM_ROUNDS

    async def handle_ready(writer: StreamWriter) -> str:
        nonlocal rounds_left
        if rounds_left > 0:
            rounds_left -= 1
            round_num = NUM_ROUNDS - rounds_left
            writer.write(b"PING\n")
            print(f"Alice [round {round_num}]: sent PING")
            return STATE_WAITING_FOR_PONG
        else:
            writer.write(b"BYE\n")
            print("Alice: sent BYE, done.")
            return STATE_DONE

    async def handle_pong(writer: StreamWriter) -> str:
        print("Alice: received PONG")
        return STATE_WAITING_FOR_READY

    dispatch = {
        (STATE_WAITING_FOR_READY, "READY"): handle_ready,
        (STATE_WAITING_FOR_PONG,  "PONG"):  handle_pong,  # noqa: E241
    }

    state = STATE_WAITING_FOR_READY

    while state != STATE_DONE:
        data = await reader.readline()
        if not data:
            print(f"Alice [{state}]: connection dropped unexpectedly.")
            break
        msg = data.decode().strip()
        print(f"Alice [{state}]: received '{msg}'")

        handler = dispatch.get((state, msg))

        if handler is None:
            print(f"Alice [{state}]: no transition for '{msg}' — ignoring.")
            continue

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

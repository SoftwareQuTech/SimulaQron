"""
Polite Ping-Pong — Bob (server).

Extends plain ping pong with a greeting phase: Bob sends "HI" immediately
on connect and waits for Alice's "HI" before the game begins.

Bob's state diagram
-------------------

    (connect) → send "HI"
        │
        ▼
  WAITING_HI ──[recv "HI"]──► IDLE            ← greeting phase
                                │
                           recv "PING"
                                ▼
                            PLAYING
                                │ (entry action: send "PONG")
                          ┌─────┴──────────────┐
                    rounds left?             done?
                          │                   │
                          ▼                   ▼
                        IDLE                DONE

Transition table:

    State       │ Event        │ Action       │ Next state
    ────────────┼──────────────┼──────────────┼────────────────
    WAITING_HI  │ recv "HI"   │ —            │ IDLE
    IDLE        │ recv "PING"  │ —            │ PLAYING
    PLAYING     │ (entry)      │ send "PONG"  │ IDLE or DONE
"""

from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


NUM_ROUNDS = 5

# ── States ───────────────────────────────────────────────────────────────────

STATE_WAITING_HI = "WAITING_HI"
STATE_IDLE       = "IDLE"      # noqa: E221
STATE_PLAYING    = "PLAYING"   # noqa: E221
STATE_DONE       = "DONE"      # noqa: E221


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_hi(_writer: StreamWriter) -> str:
    """Transition: WAITING_HI ──[recv "HI"]──► IDLE"""
    print("Bob: received HI — greeting done, game starting", flush=True)
    return STATE_IDLE


async def handle_ping(_writer: StreamWriter) -> str:
    """Transition: IDLE ──[recv "PING"]──► PLAYING"""
    print("Bob: received PING", flush=True)
    return STATE_PLAYING


# ── Dispatch table ────────────────────────────────────────────────────────────

BOB_DISPATCH = {
    (STATE_WAITING_HI, "HI"):   handle_hi,
    (STATE_IDLE,       "PING"): handle_ping,  # noqa: E241
}


# ── Event loop ────────────────────────────────────────────────────────────────

async def run_bob(reader: StreamReader, writer: StreamWriter) -> None:
    print("Bob: Alice connected.", flush=True)
    rounds_done = 0

    # Greet Alice before starting the game.
    writer.write(b"HI\n")
    print("Bob: sent HI", flush=True)
    state = STATE_WAITING_HI

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
        msg = data.decode("utf-8")
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
    _here = Path(__file__).parent
    simulaqron_settings.read_from_file(_here / "simulaqron_settings.json")
    network_config.read_from_file(_here / "simulaqron_network.json")

    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)
    server = SimulaQronClassicalServer(sockets_config, "Bob")
    server.register_client_handler(run_bob)

    print("Bob: starting server...", flush=True)
    server.start_serving()

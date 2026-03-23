"""
Polite Ping-Pong — Bob (server).

Bob sends "READY" immediately on connection and after each "PONG", signalling
to Alice that he is ready for the next round.  He handles "PING" (reply PONG
then READY) and "BYE" (close).

Bob's state diagram
-------------------

          ┌─ (connect) ──────────────────────────────────────────┐
          │  send "READY"                                         │
          ▼                                                        │
WAITING_FOR_PING_OR_BYE                                        (start)
          │
   recv "PING" → send "PONG", send "READY" → (stay)
   recv "BYE"  → DONE

Transition table:

    Current state           │ Message │ Action                   │ Next state
    ────────────────────────┼─────────┼──────────────────────────┼───────────────────────
    WAITING_FOR_PING_OR_BYE │ "PING"  │ send "PONG", send "READY"│ WAITING_FOR_PING_OR_BYE
    WAITING_FOR_PING_OR_BYE │ "BYE"   │ —                        │ DONE
"""
from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


# ── States ───────────────────────────────────────────────────────────────────

STATE_WAITING_FOR_PING_OR_BYE = "WAITING_FOR_PING_OR_BYE"
STATE_DONE                    = "DONE"                      # noqa: E221


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_ping(writer: StreamWriter) -> str:
    writer.write(b"PONG\n")
    print("Bob: sent PONG", flush=True)
    writer.write(b"READY\n")
    print("Bob: sent READY", flush=True)
    return STATE_WAITING_FOR_PING_OR_BYE


async def handle_bye(writer: StreamWriter) -> str:
    print("Bob: received BYE, closing.", flush=True)
    return STATE_DONE


# ── Dispatch table ────────────────────────────────────────────────────────────

BOB_DISPATCH = {
    (STATE_WAITING_FOR_PING_OR_BYE, "PING"): handle_ping,
    (STATE_WAITING_FOR_PING_OR_BYE, "BYE"):  handle_bye,   # noqa: E241
}


# ── Event loop ────────────────────────────────────────────────────────────────

async def run_bob(reader: StreamReader, writer: StreamWriter) -> None:
    print("Bob: Alice connected.", flush=True)

    writer.write(b"READY\n")
    print("Bob: sent READY", flush=True)
    state = STATE_WAITING_FOR_PING_OR_BYE

    while state != STATE_DONE:
        data = await reader.readline()
        if not data:
            print(f"Bob [{state}]: connection dropped unexpectedly.", flush=True)
            break
        msg = data.decode().strip()
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

"""
Quantum Correlated Random Number Generation — Alice (client).

Combines event-based classical messaging (state machine pattern from
politePingPong) with quantum operations.  Alice proposes generating
shared randomness with Bob.  If Bob agrees, both create an EPR pair
and measure their half, obtaining a correlated random bit.

Alice's state diagram
---------------------

              ┌─ (connect) ─────────────────────────────────┐
              │  send "generate randomness?"                 │
              ▼                                              │
    WAITING_ACCEPT                                        (start)
         │
    recv "yes"
    quantum: create EPR, measure, flush
         │
         ▼
        DONE

Transition table:

    Current state    │ Message received │ Action                        │ Next state
    ─────────────────┼──────────────────┼───────────────────────────────┼───────────
    WAITING_ACCEPT   │ "yes"            │ create EPR pair, measure      │ DONE
"""
from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType

from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import EPRSocket  # noqa: E402


# ── States ───────────────────────────────────────────────────────────────────

STATE_WAITING_ACCEPT = "WAITING_ACCEPT"
STATE_DONE           = "DONE"           # noqa: E221


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_yes(writer: StreamWriter) -> str:
    """
    Transition: WAITING_ACCEPT ──[recv "yes"]──► DONE

    Bob agreed — create an EPR pair with him and measure our half.
    """
    epr_socket = EPRSocket("Bob")

    # Open a connection to the quantum backend (not to Bob — that's the
    # classical reader/writer).  We pass the EPR socket so the backend
    # knows which nodes will share entanglement.
    sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

    # Create an EPR pair with Bob and keep our half
    epr = epr_socket.create_keep()[0]
    m = epr.measure()

    # flush() sends all queued quantum operations to the backend and waits
    # for them to complete.  After this call, measurement results like m
    # become real values (before flush they are just promises/futures).
    sim_conn.flush()

    # int(m) extracts the measurement outcome — only valid after flush()
    result = int(m)
    sim_conn.close()

    print(f"Alice: my random bit is {result}")
    return STATE_DONE


# ── Dispatch table ────────────────────────────────────────────────────────────

ALICE_DISPATCH = {
    (STATE_WAITING_ACCEPT, "yes"): handle_yes,
}


# ── Event loop ────────────────────────────────────────────────────────────────

async def run_alice(reader: StreamReader, writer: StreamWriter):
    """
    Alice's event loop.

    Opens by proposing shared randomness, then enters the state machine.
    """
    # Initial action: propose generating randomness
    opening = "generate randomness?"
    print(f"Alice: sending '{opening}'")
    writer.write(opening.encode("utf-8"))
    await writer.drain()

    state = STATE_WAITING_ACCEPT

    while state != STATE_DONE:
        data = await reader.read(255)
        if not data:
            print(f"Alice [{state}]: connection dropped unexpectedly.")
            break
        msg = data.decode("utf-8")
        print(f"Alice [{state}]: received '{msg}'")

        handler = ALICE_DISPATCH.get((state, msg))

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

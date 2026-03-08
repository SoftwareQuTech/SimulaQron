"""
Quantum Correlated Random Number Generation — Bob (server).

Combines event-based classical messaging (state machine pattern from
politePingPong) with quantum operations.  Bob waits for Alice's proposal.
If she asks to generate shared randomness, he agrees, then both create
an EPR pair and measure their half, obtaining a correlated random bit.

Bob's state diagram
-------------------

                recv "generate randomness?"
                send "yes"
                quantum: receive EPR, measure, flush
    WAITING_PROPOSAL  ───────────────────────────────────►  DONE

Transition table:

    Current state      │ Message received         │ Action                        │ Next state
    ───────────────────┼──────────────────────────┼───────────────────────────────┼───────────
    WAITING_PROPOSAL   │ "generate randomness?"   │ send "yes", recv EPR, measure │ DONE
"""
from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType

from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import EPRSocket  # noqa: E402


# ── States ───────────────────────────────────────────────────────────────────

STATE_WAITING_PROPOSAL = "WAITING_PROPOSAL"
STATE_DONE             = "DONE"


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_generate(writer: StreamWriter) -> str:
    """
    Transition: WAITING_PROPOSAL ──[recv "generate randomness?"]──► DONE

    Alice wants shared randomness — agree, then receive our half of the
    EPR pair and measure it.
    """
    # Classical: agree
    reply = "yes"
    print(f"Bob: sending '{reply}'", flush=True)
    writer.write(reply.encode("utf-8"))
    await writer.drain()

    # Quantum: receive our half of the EPR pair from Alice and measure it.
    # sim_conn is the connection to the quantum backend (not to Alice —
    # that's the classical reader/writer above).
    epr_socket = EPRSocket("Alice")
    sim_conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])

    epr = epr_socket.recv_keep()[0]
    m = epr.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  int(m) only works after flush().
    sim_conn.flush()

    result = int(m)
    sim_conn.close()

    print(f"Bob: my random bit is {result}", flush=True)
    return STATE_DONE


# ── Dispatch table ────────────────────────────────────────────────────────────

BOB_DISPATCH = {
    (STATE_WAITING_PROPOSAL, "generate randomness?"): handle_generate,
}


# ── Event loop ────────────────────────────────────────────────────────────────

async def run_bob(reader: StreamReader, writer: StreamWriter):
    """
    Bob's event loop.

    Waits for messages from Alice and dispatches via the state machine.
    """
    print("Bob: Alice connected.", flush=True)
    state = STATE_WAITING_PROPOSAL

    while state != STATE_DONE:
        data = await reader.read(255)
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

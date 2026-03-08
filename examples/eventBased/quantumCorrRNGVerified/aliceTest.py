"""
Quantum Correlated RNG with Verification — Alice (client).

Extends quantumCorrRNG by adding a classical verification step after the
quantum measurement.  After both nodes measure their EPR halves, Alice
sends her result to Bob so he can confirm the correlation.

This demonstrates the full cycle:
  classical negotiation -> quantum operation -> classical verification

Alice's state diagram
---------------------

              ┌─ (connect) ─────────────────────────────────┐
              │  send "generate randomness?"                 │
              ▼                                              │
    WAITING_ACCEPT                                        (start)
         │
    recv "yes"
    quantum: create EPR, measure, flush
    send result to Bob
         │
         ▼
    WAITING_VERIFICATION
         │
    recv "verified: ..."
         │
         ▼
        DONE

Transition table:

    Current state          │ Message received     │ Action                          │ Next state
    ───────────────────────┼──────────────────────┼─────────────────────────────────┼─────────────────────
    WAITING_ACCEPT         │ "yes"                │ EPR create+measure, send result │ WAITING_VERIFICATION
    WAITING_VERIFICATION   │ "verified: ..."      │ print confirmation              │ DONE
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

STATE_WAITING_ACCEPT       = "WAITING_ACCEPT"
STATE_WAITING_VERIFICATION = "WAITING_VERIFICATION"
STATE_DONE                 = "DONE"


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_yes(writer: StreamWriter) -> str:
    """
    Transition: WAITING_ACCEPT ──[recv "yes"]──► WAITING_VERIFICATION

    Bob agreed — create an EPR pair, measure our half, and send the
    result to Bob for verification.
    """
    epr_socket = EPRSocket("Bob")

    # Open a connection to the quantum backend (not to Bob — that's the
    # classical reader/writer).
    sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

    # Create an EPR pair with Bob and keep our half
    epr = epr_socket.create_keep()[0]
    m = epr.measure()

    # flush() sends all queued quantum operations to the backend and waits
    # for them to complete.  After this, int(m) gives the real value.
    sim_conn.flush()

    result = int(m)
    sim_conn.close()

    print(f"Alice: my random bit is {result}")

    # Send our result to Bob so he can verify the correlation
    writer.write(str(result).encode("utf-8"))
    await writer.drain()

    return STATE_WAITING_VERIFICATION


async def handle_verification(writer: StreamWriter) -> str:
    """
    Transition: WAITING_VERIFICATION ──[recv "verified: ..."]──► DONE

    Bob confirmed whether the results match.
    """
    # The message content is printed by the event loop, nothing else to do.
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

        # In WAITING_VERIFICATION, any message from Bob is the verification
        if state == STATE_WAITING_VERIFICATION:
            state = STATE_DONE
            continue

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

"""
Quantum Correlated RNG with Verification — Bob (server).

Extends quantumCorrRNG by adding a classical verification step after the
quantum measurement.  After both nodes measure their EPR halves, Alice
sends her result to Bob so he can confirm the correlation.

This demonstrates the full cycle:
  classical negotiation -> quantum operation -> classical verification

Bob's state diagram
-------------------

                recv "generate randomness?"
                send "yes"
                quantum: receive EPR, measure, flush
    WAITING_PROPOSAL  ─────────────────────────────►  WAITING_ALICE_RESULT
                                                            │
                                                  recv Alice's result
                                                  compare, send verification
                                                            │
                                                            ▼
                                                          DONE

Transition table:

    Current state          │ Message received       │ Action                           │ Next state
    ───────────────────────┼────────────────────────┼──────────────────────────────────┼────────────────────
    WAITING_PROPOSAL       │ "generate randomness?" │ send "yes", recv EPR, measure    │ WAITING_ALICE_RESULT
    WAITING_ALICE_RESULT   │ <alice's bit>          │ compare results, send verdict    │ DONE
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

STATE_WAITING_PROPOSAL     = "WAITING_PROPOSAL"      # noqa: E221
STATE_WAITING_ALICE_RESULT = "WAITING_ALICE_RESULT"
STATE_DONE                 = "DONE"                  # noqa: E221

# Bob stores his measurement result here so the verification handler can
# compare it with Alice's result.
bob_result = None


# ── Handlers ─────────────────────────────────────────────────────────────────

async def handle_generate(writer: StreamWriter) -> str:
    """
    Transition: WAITING_PROPOSAL ──[recv "generate randomness?"]──► WAITING_ALICE_RESULT

    Alice wants shared randomness — agree, then receive our half of the
    EPR pair and measure it.  Store result for later verification.
    """
    global bob_result

    # Classical: agree
    reply = "yes"
    print(f"Bob: sending '{reply}'", flush=True)
    writer.write(reply.encode("utf-8"))
    await writer.drain()

    # Quantum: receive our half of the EPR pair from Alice and measure it.
    # sim_conn is the connection to the quantum backend (not to Alice).
    epr_socket = EPRSocket("Alice")
    sim_conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])

    epr = epr_socket.recv_keep()[0]
    m = epr.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  int(m) only works after flush().
    sim_conn.flush()

    bob_result = int(m)
    sim_conn.close()

    print(f"Bob: my random bit is {bob_result}", flush=True)
    return STATE_WAITING_ALICE_RESULT


async def handle_alice_result(writer: StreamWriter, alice_result: int) -> str:
    """
    Transition: WAITING_ALICE_RESULT ──[recv result]──► DONE

    Alice sent her measurement result.  Compare with ours and send
    a verification message back.
    """
    match = alice_result == bob_result
    verdict = f"verified: Alice={alice_result}, Bob={bob_result}, match={match}"
    print(f"Bob: {verdict}", flush=True)
    writer.write(verdict.encode("utf-8"))
    await writer.drain()
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

        # In WAITING_ALICE_RESULT, the message is Alice's measurement bit
        if state == STATE_WAITING_ALICE_RESULT:
            alice_bit = int(msg)
            state = await handle_alice_result(writer, alice_bit)
            continue

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

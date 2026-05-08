"""
Polite Ping-Pong — Alice (client).

Extends plain ping pong with a greeting phase: Bob sends "HI" on connect,
Alice replies with "HI", then the game proceeds exactly as in ping pong.

Alice's state diagram
---------------------

    (connect)
        │
        ▼
  WAITING_HI ──[recv "HI"]──► IDLE            ← greeting phase
                  send "HI"     │
                                │ (entry action: send "PING")
                                ▼
                            PLAYING
                                │
                           recv "PONG"
                          ┌─────┴──────────────┐
                    rounds left?             done?
                          │                   │
                          ▼                   ▼
                        IDLE                DONE

Transition table:

    State       │ Event        │ Action       │ Next state
    ────────────┼──────────────┼──────────────┼────────────────
    WAITING_HI  │ recv "HI"   │ send "HI"    │ IDLE
    IDLE        │ (entry)      │ send "PING"  │ PLAYING
    PLAYING     │ recv "PONG"  │ —            │ IDLE or DONE
"""

from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


NUM_ROUNDS = 5

# ── States ───────────────────────────────────────────────────────────────────

STATE_WAITING_HI = "WAITING_HI"
STATE_IDLE       = "IDLE"      # noqa: E221
STATE_PLAYING    = "PLAYING"   # noqa: E221
STATE_DONE       = "DONE"      # noqa: E221


# ── Event loop ───────────────────────────────────────────────────────────────

async def run_alice(reader: StreamReader, writer: StreamWriter) -> None:
    rounds_done = 0

    async def handle_hi(writer: StreamWriter) -> str:
        """Transition: WAITING_HI ──[recv "HI"]──► IDLE"""
        writer.write(b"HI\n")
        print("Alice: sent HI — greeting done, game starting")
        return STATE_IDLE

    async def handle_pong(_writer: StreamWriter) -> str:
        """Transition: PLAYING ──[recv "PONG"]──► IDLE (or DONE)"""
        nonlocal rounds_done
        print(f"Alice [round {rounds_done}]: received PONG")
        if rounds_done < NUM_ROUNDS:
            return STATE_IDLE
        return STATE_DONE

    dispatch = {
        (STATE_WAITING_HI, "HI"):   handle_hi,    # noqa: E241
        (STATE_PLAYING,    "PONG"): handle_pong,  # noqa: E241
    }

    state = STATE_WAITING_HI

    while state != STATE_DONE:
        # Entry action: IDLE → send PING → PLAYING
        if state == STATE_IDLE:
            rounds_done += 1
            writer.write(b"PING\n")
            print(f"Alice [round {rounds_done}]: sent PING")
            state = STATE_PLAYING

        print("here")

        data = await reader.readline()
        if not data:
            print(f"Alice [{state}]: connection dropped unexpectedly.")
            break
        # Since reader.readLine() reads until newline is found, and returns the string
        # with the newline character, we need to get rid of it to correctly transition
        # to the next stage of the state machine.
        msg = data.decode("utf-8").replace("\n", "")
        print(f"here2: {msg}")

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

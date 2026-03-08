"""
Mid-circuit classical logic example.

Demonstrates how to use sim_conn.flush() to read measurement results
mid-circuit, make classical decisions based on them, and then continue
with more quantum operations.

Without flush(), measurement results are "futures" that only become real
values after the connection is closed.  With flush(), you can read them at
any point and branch your quantum program accordingly.

This example implements a simple 3-round protocol:

  Round 1: Prepare |+> and measure.
  Round 2: Based on the round-1 outcome, prepare the *opposite* state.
  Round 3: Based on the XOR of rounds 1 and 2, decide what to prepare.

All three rounds happen inside ONE connection — no need to create multiple
connections.
"""
from pathlib import Path

from simulaqron.settings import network_config, simulaqron_settings

from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import Qubit  # noqa: E402


def run_node(node_name: str):
    results = []

    # sim_conn is our connection to the quantum backend (SimulaQron).
    # All qubit operations are queued through this connection.
    sim_conn = NetQASMConnection(node_name)

    # --- Round 1: prepare |+> and measure ---
    q1 = Qubit(sim_conn)
    q1.H()                   # |0> -> |+>
    m1 = q1.measure()
    # flush() executes all queued quantum operations and makes measurement
    # results available.  We call it after each round so we can use the
    # result to decide what to do next (mid-circuit classical logic).
    sim_conn.flush()
    # int(m) extracts the measurement outcome — only valid after flush().
    r1 = int(m1)
    results.append(r1)
    print(f"  Round 1: measured |+> -> {r1}")

    # --- Round 2: classical decision ---
    # If round 1 gave 0, prepare |1>.  If 1, prepare |0>.
    q2 = Qubit(sim_conn)
    if r1 == 0:
        q2.X()               # flip to |1>
        print("  Round 2: r1 was 0, so preparing |1>")
    else:
        print("  Round 2: r1 was 1, so preparing |0>")
    m2 = q2.measure()
    sim_conn.flush()
    r2 = int(m2)
    results.append(r2)
    print(f"  Round 2: measured -> {r2}  (should be {1 - r1})")

    # --- Round 3: compound classical logic ---
    # XOR of r1 and r2.  Since r2 = 1-r1, XOR is always 1.
    xor = r1 ^ r2
    q3 = Qubit(sim_conn)
    if xor:
        q3.X()
        print(f"  Round 3: r1 XOR r2 = {xor}, preparing |1>")
    else:
        print(f"  Round 3: r1 XOR r2 = {xor}, preparing |0>")
    m3 = q3.measure()
    sim_conn.flush()
    r3 = int(m3)
    results.append(r3)
    print(f"  Round 3: measured -> {r3}  (should be {xor})")

    sim_conn.close()

    # Summary
    print(f"\nAll rounds: {results}")
    print(f"Check: r2 == 1-r1? {results[1] == 1 - results[0]}")
    print(f"Check: r3 == r1 XOR r2? {results[2] == results[0] ^ results[1]}")
    return results


if __name__ == "__main__":
    simulaqron_config_file = Path("simulaqron_settings.json")
    simulaqron_settings.read_from_file(simulaqron_config_file)

    network_config_file = Path("simulaqron_network.json")
    network_config.read_from_file(network_config_file)

    node_name = "Alice"

    print(f"=== Mid-circuit classical logic demo ({node_name}) ===\n")
    run_node(node_name)

from pathlib import Path

from simulaqron.settings import network_config, simulaqron_settings

# This is recipe to use NetQASM with simulaqron backend.
from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

# Importing NetQASM connection, Qubit and EPR socket must be *after*
# setting the simulator for NetQASM
from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import Qubit  # noqa: E402


def run_node(this_node_name: str) -> int:
    # sim_conn is our connection to the quantum backend (SimulaQron).
    # All qubit operations are queued through this connection.
    sim_conn = NetQASMConnection(this_node_name)

    # Create a qubit — note we pass sim_conn so the backend knows where
    # to allocate it.
    q = Qubit(sim_conn)

    # Perform some local quantum operations
    q.H()
    q.X()
    m1 = q.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  Before flush(), m1 is just a future/promise.
    sim_conn.flush()

    # int(m) extracts the measurement outcome — only valid after flush().
    m1_val = int(m1)
    sim_conn.close()
    return m1_val


if __name__ == "__main__":
    # Load the simulaqron settings file
    simulaqron_config_file = Path("simulaqron_settings.json")
    simulaqron_settings.read_from_file(simulaqron_config_file)

    # Load the file network configuration file
    # We still need this file to correctly interact with the SimulaQron backend (QNodeOS and Virtual Node)
    network_config_file = Path("simulaqron_network.json")
    network_config.read_from_file(network_config_file)

    # Some data for this node:
    network_name = "default"  # A network with this name *must* exist in "simulaqron_network.json"
    node_name = "Alice"  # A node with this name *must* exist in "simulaqron_network.json"

    result = run_node(node_name)
    print(result)

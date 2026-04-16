import logging

from pathlib import Path

from simulaqron.settings import network_config, simulaqron_settings

# This is recipe to use NetQASM with simulaqron backend.
from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

# Importing NetQASM connection, Qubit and EPR socket must be *after*
# setting the simulator for NetQASM
from netqasm.logging.glob import set_log_level  # noqa: E402
from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import EPRSocket  # noqa: E402


def run_alice(this_node_name: str, remote_node_name: str) -> int:
    epr_socket = EPRSocket(remote_node_name)

    # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
    # Bob is reached via EPRSocket for quantum and reader/writer for classical.
    sim_conn = NetQASMConnection(this_node_name, epr_sockets=[epr_socket])

    # Create an entangled qubit
    A = epr_socket.create_keep()[0]

    # And simply measure it
    a = A.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  Before flush(), a is just a future/promise.
    sim_conn.flush()

    # int(m) extracts the measurement outcome — only valid after flush().
    a_val = int(a)
    sim_conn.close()
    return a_val


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(name)s:%(filename)s:%(lineno)d:%(message)s",
        level=logging.DEBUG,
        force=True
    )
    # We set the netqasm log level to "info" to avoid verbose output from the internals.
    set_log_level(logging.INFO)

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
    other_node_name = "Bob"

    result = run_alice(node_name, other_node_name)
    print(f"{node_name}: My Random Number is '{result}'")

import logging

from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings import network_config, simulaqron_settings

# This is recipe to use NetQASM with simulaqron backend.
from netqasm.runtime.settings import set_simulator

from simulaqron.settings.network_config import NodeConfigType

set_simulator("simulaqron")

# Importing NetQASM connection, Qubit and EPR socket must be *after*
# setting the simulator for NetQASM
from netqasm.logging.glob import set_log_level  # noqa: E402
from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import EPRSocket  # noqa: E402


async def run_charlie(reader: StreamReader, writer: StreamWriter) -> int:
    # This is "Charlie": the end node of the GHZ chain
    this_node_name = "Charlie"
    remote_node_name = "Bob"
    message = await reader.read(100)
    assert message.decode("utf-8") == "receive_qubit"
    epr_socket = EPRSocket(remote_node_name)

    # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
    # Bob is reached via EPRSocket for quantum and reader/writer for classical.
    sim_conn = NetQASMConnection(this_node_name, epr_sockets=[epr_socket])

    # Receive an entangled qubit
    epr = epr_socket.recv_keep()[0]

    writer.write("continue".encode("utf-8"))

    # And simply measure it
    m1 = epr.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  Before flush(), m1 is just a future/promise.
    sim_conn.flush()

    # int(m) extracts the measurement outcome — only valid after flush().
    m1_val = int(m1)
    sim_conn.close()
    print(f"{this_node_name}: My outcome is '{m1_val}'")
    return 0


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
    node_name = "Charlie"  # A node with this name *must* exist in "simulaqron_network.json"
    other_node_name = "Bob"

    sockets = SocketsConfig(network_config, network_name, NodeConfigType.APP)

    server = SimulaQronClassicalServer(sockets, node_name)
    server.register_client_handler(run_charlie)
    server.start_serving()

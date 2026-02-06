import logging

from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient, SimulaQronClassicalServer
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


async def send_to_charlie(reader: StreamReader, writer: StreamWriter):
    writer.write("receive_qubit".encode("utf-8"))
    message = await  reader.read(100)
    assert message.decode("utf-8") == "continue"


# This function contains the code of the classical client
async def bob_program(reader: StreamReader, writer: StreamWriter) -> int:
    # This is "Bob": the middle node of the GHZ chain
    this_node_name = "Bob"
    start_node_name = "Alice"  # A node with this name *must* exist in "simulaqron_network.json"
    end_node_name = "Charlie"  # A node with this name *must* exist in "simulaqron_network.json"

    logging.debug("LOCAL %s: Running client side program.", this_node_name)

    message = await reader.read(100)
    assert message.decode("utf-8") == "receive_qubit"

    epr_socket_alice = EPRSocket(start_node_name)
    epr_socket_charlie = EPRSocket(end_node_name)

    sockets = SocketsConfig(network_config, "default", NodeConfigType.APP)

    charlie_client = SimulaQronClassicalClient(sockets)
    # To start executing quantum operations, we need to create a NetQASM connection
    with NetQASMConnection(this_node_name, epr_sockets=[epr_socket_alice, epr_socket_charlie]) as bob:
        # Receive an entangled qubit
        epr_alice = epr_socket_alice.recv_keep()[0]

        # Create a new entangled with Charlie
        epr_charlie = epr_socket_charlie.create_keep()[0]

        await charlie_client.connect_and_run(end_node_name, send_to_charlie)

        # Create the GHZ state by entangling the fresh qubit
        epr_alice.cnot(epr_charlie)

        writer.write("continue".encode("utf-8"))

        # And simply measure it
        m1 = epr_charlie.measure()
    # Any value that comes from NetQASM *need* to be retrieved ("casted" to int)
    # *after* the connection is closed (or after flushing the connection, untested)
    m1_val = int(m1)
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
    node_name = "Bob"  # A node with this name *must* exist in "simulaqron_network.json"
    start_node_name = "Alice"  # A node with this name *must* exist in "simulaqron_network.json"
    end_node_name = "Charlie"  # A node with this name *must* exist in "simulaqron_network.json"

    classical_sockets = SocketsConfig(network_config, network_name, NodeConfigType.APP)

    server = SimulaQronClassicalServer(classical_sockets, node_name)
    client = SimulaQronClassicalClient(classical_sockets)

    server.register_client_handler(bob_program)
    server.start_serving()

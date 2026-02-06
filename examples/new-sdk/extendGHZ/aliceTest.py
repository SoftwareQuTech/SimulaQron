import logging

from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
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


# This function contains the code of the classical client
async def alice_program(reader: StreamReader, writer: StreamWriter) -> int:
    # This is "Alice": the start node of the GHZ chain
    this_node_name = "Alice"
    remote_node_name = "Bob"  # A node with this name *must* exist in "simulaqron_network.json"

    logging.debug("LOCAL %s: Running client side program.", this_node_name)

    epr_socket = EPRSocket(remote_node_name)
    # To start executing quantum operations, we need to create a NetQASM connection
    with NetQASMConnection(this_node_name, epr_sockets=[epr_socket]):
        # Create an entangled qubit with Bob
        epr = epr_socket.create_keep()[0]

        writer.write("receive_qubit".encode("utf-8"))
        answer = await reader.read(100)

        assert answer.decode("utf-8") == "continue"

        m1 = epr.measure()
    # Any value that comes from NetQASM *need* to be retrieved ("casted" to int)
    # *after* the connection is closed (or after flushing the connection, untested)
    m1_val = int(m1)
    return m1_val


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
    node_name = "Alice"
    other_node_name = "Bob"  # A node with this name *must* exist in "simulaqron_network.json"

    classical_sockets = SocketsConfig(network_config, network_name, NodeConfigType.APP)

    # The general nodes interaction of this application is
    # Alice ----> Bob ----> Charlie ----> Bob ----> Alice
    # This means:
    # 1. Alice entangles a qubit with Bob, and waits until Bob has finished.
    # 2. Bob received the entangled qubit, creates a new local one and entangles it with the one received

    # This node will act as a classical client, waiting for a classical answer from Bob
    # to measure the qubit
    client = SimulaQronClassicalClient(classical_sockets)

    result = client.run_client(other_node_name, alice_program)
    #result = alice_program(1, 0)

    print(f"{node_name}: My outcome is '{result}'")

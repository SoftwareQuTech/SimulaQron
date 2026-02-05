from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType

# This is recipe to use NetQASM with simulaqron backend.
from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

# Importing NetQASM connection, Qubit and EPR socket must be *after*
# setting the simulator for NetQASM
from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import Qubit, EPRSocket  # noqa: E402


# This function contains the code of the classical client
def quantum_program(this_node_name: str) -> int:
    # To start executing quantum operations, we need to create a NetQASM connection
    with NetQASMConnection(this_node_name, epr_sockets=[epr_socket]) as alice:
        # Create a qubit
        q = Qubit(alice)

        # Perform some local quantum operations
        q.H()
        q.X()
        m1 = q.measure()
    # Any value that comes from NetQASM *need* to be retrieved ("casted" to int)
    # *after* the connection is closed (or after flushing the connection, untested)
    m1_val = int(m1)
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
    node_name = "YourName"  # A node with this name *must* exist in "simulaqron_network.json"

    # Get the socket configuration for the sockets used for the application layer
    sockets_config = SocketsConfig(network_config, network_name, NodeConfigType.APP)

    # Name of one node to classically connect to
    server_name = "Bob"

    result = quantum_program()
    print(result)

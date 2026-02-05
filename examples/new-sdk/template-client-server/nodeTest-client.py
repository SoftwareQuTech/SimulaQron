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
# "reader" is an object connected to the server, which can be used to read data from the server
# "writer" is an object connected to the server, which can be used to send data to the server
async def run_client(reader: StreamReader, writer: StreamWriter):
    # To send a messsage, we can simply use the "wirte" method from the "writer" object
    # The argument *must* be a python bytes object, which we can get by encoding (using
    # the UTF-8 charmap) any python string
    message = "Hello World"
    writer.write(message.encode("utf-8"))

    # If you want to receive a message (such a response) from the server, you can
    # use the "read" method from the "reader" object. The argument is an integer that
    # configures the maximum bytes that we are allowed to read in a single operation.
    # Note: Since "read" is a python coroutine, we need to "await" it, so python can
    # execute other coroutines until the data becomes available to read.
    answer = await reader.read(100)
    # Messages received from the server come as "bytes", which need to be decoded
    # (using UTF-8 encoding) before using it as a string.
    print(answer.decode("utf-8"))

    this_node_name = "Alice"
    other_node_name = "Bob"

    # We ca create an EPR socket with the other node
    epr_socket = EPRSocket(other_node_name)
    # To start executing quantum operations, we need to create a NetQASM connection
    with NetQASMConnection(this_node_name, epr_sockets=[epr_socket]) as alice:
        # Create a qubit
        q = Qubit(alice)
        q.H()
        # Create an entangled qubit with the other node
        epr = epr_socket.create_keep()[0]
        # Teleport
        q.cnot(epr)
        q.H()
        m1 = q.measure()
        m2 = epr.measure()
    # Any value that comes from NetQASM *need* to be retrieved ("casted" to int)
    # *after* the connection is closed (or after flushing the connection, untested)
    m1_val = int(m1)
    m2_val = int(m2)
    return m1_val, m2_val


if __name__ == "__main__":
    # Load the simulaqron settings file
    simulaqron_config_file = Path("simulaqron_settings.json")
    simulaqron_settings.read_from_file(simulaqron_config_file)

    # Load the file network configuration file
    network_config_file = Path("simulaqron_network.json")
    network_config.read_from_file(network_config_file)

    # Some data for this node:
    network_name = "default"  # A network with this name *must* exist in "simulaqron_network.json"
    node_name = "YourName"  # A node with this name *must* exist in "simulaqron_network.json"

    # Get the socket configuration for the sockets used for the application layer
    sockets_config = SocketsConfig(network_config, network_name, NodeConfigType.APP)

    # Name of one node to classically connect to
    server_name = "Bob"

    # Create the client
    client = SimulaQronClassicalClient(sockets_config)
    # Run a classical client invoking the `run_client` method. This also has the effect to
    # immediately execute the `run_client` method.
    results = client.run_client(server_name, run_client)

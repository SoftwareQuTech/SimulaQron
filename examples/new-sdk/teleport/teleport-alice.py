from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings import network_config
from simulaqron.settings.network_config import NodeConfigType

# This is recipe to use NetQASM with simulaqron backend.
from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

# Importing NetQASM connection, Qubit and EPR socket must be *after*
# setting the simulator for NetQASM
from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import Qubit, EPRSocket  # noqa: E402


async def run_alice(reader: StreamReader, writer: StreamWriter):
    epr_socket = EPRSocket("Bob")
    with NetQASMConnection("Alice", epr_sockets=[epr_socket]) as alice:
        # Create a qubit
        q = Qubit(alice)
        q.H()
        # Create entanglement
        epr = epr_socket.create_keep()[0]
        # Teleport
        q.cnot(epr)
        q.H()
        m1 = q.measure()
        m2 = epr.measure()
    # Any value that comes from NetQASm *need* to be retrieved ("casted" to int)
    # *after* the connection is closed (or after flushing the connection, untested)
    m1_val = int(m1)
    m2_val = int(m2)
    message = f"{m1_val}:{m2_val}"  # noqa: E231
    writer.write(message.encode("utf-8"))
    return m1_val, m2_val


if __name__ == "__main__":
    # Load the file network configuration file
    network_config_file = Path("simulaqron_network.json")
    network_config.read_from_file(network_config_file)

    # Get the socket configuration for the sockets used for the application layer
    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)

    # Create the client
    client = SimulaQronClassicalClient(sockets_config)
    results = client.run_client("Bob", run_alice)
    print(f"Alice measurements: m1={results[0]}, m2={results[1]}")

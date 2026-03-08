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

    # sim_conn is our connection to the quantum backend (SimulaQron), not to Bob.
    # Bob is reached via EPRSocket for quantum and reader/writer for classical.
    sim_conn = NetQASMConnection("Alice", epr_sockets=[epr_socket])

    # Create a qubit to teleport
    q = Qubit(sim_conn)
    q.H()
    # Create entanglement
    epr = epr_socket.create_keep()[0]
    # Teleport circuit: CNOT + H + measure both
    q.cnot(epr)
    q.H()
    m1 = q.measure()
    m2 = epr.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  Before flush(), m1 and m2 are just futures/promises.
    sim_conn.flush()

    # int(m) extracts the measurement outcome — only valid after flush().
    m1_val = int(m1)
    m2_val = int(m2)
    sim_conn.close()
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

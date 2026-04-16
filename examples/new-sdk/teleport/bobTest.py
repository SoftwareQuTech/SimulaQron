from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings import network_config
from simulaqron.settings.network_config import NodeConfigType

from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import EPRSocket  # noqa: E402


async def run_bob(reader: StreamReader, writer: StreamWriter):
    # We wait for the classical message first
    corrections_bytes = await reader.read(255)
    corrections = corrections_bytes.decode("utf-8").split(":")
    (q_val, a_val) = corrections
    epr_socket = EPRSocket("Alice")

    # sim_conn is our connection to the quantum backend (SimulaQron), not to Alice.
    # Alice is reached via EPRSocket for quantum and reader/writer for classical.
    sim_conn = NetQASMConnection("Bob", epr_sockets=[epr_socket])

    B = epr_socket.recv_keep()[0]

    # Apply teleportation corrections based on Alice's classical message
    if int(a_val) == 1:
        B.X()
    if int(q_val) == 1:
        B.Z()
    meas = B.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  Before flush(), meas is just a future/promise.
    sim_conn.flush()

    # int(m) extracts the measurement outcome — only valid after flush().
    meas_val = int(meas)
    sim_conn.close()
    print(f"Bob measurement: {meas_val}")


if __name__ == "__main__":
    # Load the file network configuration file
    network_config_file = Path("simulaqron_network.json")
    network_config.read_from_file(network_config_file)

    # Get the socket configuration for the sockets used for the application layer
    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)

    # Create the server
    server = SimulaQronClassicalServer(sockets_config, "Bob")
    server.register_client_handler(run_bob)
    server.start_serving()

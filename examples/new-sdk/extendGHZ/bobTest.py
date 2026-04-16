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
from netqasm.sdk import EPRSocket, Qubit  # noqa: E402


async def send_to_charlie(reader: StreamReader, writer: StreamWriter,
                          sim_conn: NetQASMConnection, B_1: Qubit, B_2: Qubit) -> None:
    # Tell Bob to receive the EPR half
    writer.write("receive_qubit".encode("utf-8"))

    # Await for the green light from Charlie
    message = await reader.read(100)
    assert message.decode("utf-8") == "continue"

    # Create the GHZ state by entangling the qubit entangled with Alice
    B_1.cnot(B_2)

    # We now measure the entagled qubit with Charlie
    b_2 = B_2.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available.  Before flush(), b_2 is just a future/promise.
    sim_conn.flush()

    # int(b_2) extracts the measurement outcome — only valid after flush().
    b_2_val = int(b_2)

    # We send the measurement b_2 to Charlie, for corrections.
    writer.write(f"{b_2_val}".encode("utf-8"))

    # We wait for green light from Charlie, again
    charlie_msg = await reader.read(100)
    assert charlie_msg.decode("utf-8") == "continue"


async def run_bob(reader: StreamReader, writer: StreamWriter) -> int:
    # This is "Bob": the middle node of the GHZ chain
    this_node_name = "Bob"
    start_node_name = "Alice"  # A node with this name *must* exist in "simulaqron_network.json"
    end_node_name = "Charlie"  # A node with this name *must* exist in "simulaqron_network.json"

    message = await reader.read(100)
    assert message.decode("utf-8") == "receive_qubit"

    epr_socket_alice = EPRSocket(start_node_name)
    epr_socket_charlie = EPRSocket(end_node_name)

    sockets = SocketsConfig(network_config, "default", NodeConfigType.APP)

    charlie_client = SimulaQronClassicalClient(sockets)

    # sim_conn is our connection to the quantum backend (SimulaQron), not to
    # Alice or Charlie.  They are reached via EPRSockets for quantum and
    # reader/writer for classical.
    sim_conn = NetQASMConnection(this_node_name, epr_sockets=[epr_socket_alice, epr_socket_charlie])

    # Receive an entangled qubit from Alice
    B_1 = epr_socket_alice.recv_keep()[0]

    # Create a new entangled pair with Charlie
    B_2 = epr_socket_charlie.create_keep()[0]

    # We need to flush the EPR pair creation, so the reciever does not timeout on the other side.
    sim_conn.flush()

    # The next part of the protocol needs to be executed between Bob and Charlie.
    # In this interaction, Bob acts as client
    await charlie_client.connect_and_run(end_node_name, send_to_charlie, sim_conn, B_1, B_2)

    # At this point, we have achieved |GHZ>_{AB_1C}
    # Tell Alice to continue
    writer.write("continue".encode("utf-8"))

    # We can measure the B_1 qubit, part of the GHZ
    b_1 = B_1.measure()

    # flush() executes all queued quantum operations and makes measurement
    # results available. Before flush(), c is just a future/promise.
    sim_conn.flush()

    b_1_val = int(b_1)
    sim_conn.close()
    print(f"{this_node_name}: My outcome is '{b_1_val}'")
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

    server.register_client_handler(run_bob)
    server.start_serving()

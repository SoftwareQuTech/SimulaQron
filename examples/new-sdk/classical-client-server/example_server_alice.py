from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.settings import network_config
from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings.network_config import NodeConfigType

async def connection_handler(reader: StreamReader, writer: StreamWriter):
    result = await reader.read(255)
    print(f"Server received message: '{result.decode("utf-8")}'")
    writer.write(result)
    print(f"Server send message: '{result.decode("utf-8")}'")
    writer.close()

if __name__ == "__main__":
    # This is "Alice" - the server
    # Load the file network configuration file
    network_config_file = Path("simulaqron_network.json")
    network_config.read_from_file(network_config_file)

    # Get the socket configuration for the sockets used for the application layer
    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)

    # Create the server
    server = SimulaQronClassicalServer(sockets_config, "Alice")

    # Register a new client handler. The given function will be called once a new client
    # opens a connection with this node.
    server.register_client_handler(connection_handler)

    # Start serving the clients
    server.start_serving()
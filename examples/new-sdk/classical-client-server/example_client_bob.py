from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.settings import network_config
from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings.network_config import NodeConfigType

async def client_code(reader: StreamReader, writer: StreamWriter):
    data = "Hello World!".encode("utf-8")
    writer.write(data)
    print(f"Client sent message '{data.decode("utf-8")}'")
    result = await reader.read(255)
    print(f"Client received message: '{result.decode("utf-8")}'")
    writer.close()

if __name__ == "__main__":
    # This is "Bob" - the client
    # Load the file network configuration file
    network_config_file = Path("simulaqron_network.json")
    network_config.read_from_file(network_config_file)

    # Get the socket configuration for the sockets used for the application layer
    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)

    # Create the client
    client = SimulaQronClassicalClient(sockets_config)

    # Run the client. The given function will be called once the connection with
    #m the given server was established
    client.run_client("Alice", client_code)
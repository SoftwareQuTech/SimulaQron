"""
Ping-Pong server (Bob).

Bob listens for messages from Alice. For each message he receives:
  - If the message is "ping", he replies with "pong".
  - For anything else, he replies with "no way!".

Bob keeps listening until Alice disconnects.

This is a purely classical example — no quantum operations.
It demonstrates the event-based programming pattern that we will
later extend with quantum operations (teleportation, etc.).
"""
from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalServer
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


async def run_bob(reader: StreamReader, writer: StreamWriter):
    """
    Bob's event loop.

    Each iteration:
      1. Wait for a message from Alice
      2. Decide on a reply based on the message content
      3. Send the reply back
    """
    print("Bob: Alice connected, waiting for messages...", flush=True)

    while True:
        # Wait until Alice sends something
        data = await reader.read(255)

        # If we get empty data, Alice has disconnected
        if not data:
            print("Bob: Alice disconnected.", flush=True)
            break

        message = data.decode("utf-8")
        print(f"Bob: received '{message}'", flush=True)

        # Decide on a reply
        if message == "ping":
            reply = "pong"
        else:
            reply = "no way!"

        # Send the reply
        print(f"Bob: sending  '{reply}'", flush=True)
        writer.write(reply.encode("utf-8"))
        await writer.drain()


if __name__ == "__main__":
    # Load configuration files — paths are relative to this script's location
    # so the script can be run from any working directory.
    _here = Path(__file__).parent
    simulaqron_settings.read_from_file(_here / "simulaqron_settings.json")
    network_config.read_from_file(_here / "simulaqron_network.json")

    # Set up Bob's server using the network configuration
    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)
    server = SimulaQronClassicalServer(sockets_config, "Bob")
    server.register_client_handler(run_bob)

    print("Bob: starting server...")
    server.start_serving()

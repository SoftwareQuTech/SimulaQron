"""
Ping-Pong client (Alice).

Alice connects to Bob and sends a sequence of messages.
After each message she waits for Bob's reply and prints it.

Try changing the messages list to see how Bob reacts!

This is a purely classical example — no quantum operations.
It demonstrates the event-based programming pattern that we will
later extend with quantum operations (teleportation, etc.).
"""
from asyncio import StreamReader, StreamWriter
from pathlib import Path

from simulaqron.general.host_config import SocketsConfig
from simulaqron.sdk.protocol import SimulaQronClassicalClient
from simulaqron.settings import network_config, simulaqron_settings
from simulaqron.settings.network_config import NodeConfigType


async def run_alice(reader: StreamReader, writer: StreamWriter):
    """
    Alice sends a sequence of messages and prints Bob's replies.

    Try changing this list to see what Bob does with different messages!
    """
    messages = ["ping", "ping", "hello", "ping"]

    for msg in messages:
        # Send a message to Bob
        print(f"Alice: sending  '{msg}'")
        writer.write(msg.encode("utf-8"))
        await writer.drain()

        # Wait for Bob's reply
        reply_data = await reader.read(255)
        reply = reply_data.decode("utf-8")
        print(f"Alice: received '{reply}'")

    print("Alice: done, disconnecting.")


if __name__ == "__main__":
    # Load configuration files — paths are relative to this script's location
    # so the script can be run from any working directory.
    _here = Path(__file__).parent
    simulaqron_settings.read_from_file(_here / "simulaqron_settings.json")
    network_config.read_from_file(_here / "simulaqron_network.json")

    # Set up Alice's client using the network configuration
    sockets_config = SocketsConfig(network_config, "default", NodeConfigType.APP)
    client = SimulaQronClassicalClient(sockets_config)

    print("Alice: connecting to Bob...")
    client.run_client("Bob", run_alice)

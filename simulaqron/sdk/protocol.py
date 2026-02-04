import asyncio
from asyncio import StreamWriter, StreamReader
from enum import IntEnum
from typing import Any, Awaitable, Optional, Callable

from simulaqron.general.host_config import SocketsConfig


class ServingStatus(IntEnum):
    CONTINUE = 0
    STOP = 1


class SimulaQronState:
    # State of the SimulaQron simulator
    def __init__(self):
        """
        Keeps the state of the quantum memories across multiple invocations of the message handler.
        A handler can use this object to make a quantum memory
        """
        # TODO - Implement this constructor!
        pass

    def add_return_values(self, *ret_val: Any) -> None:
        """
        Adds a return value to the message handler. The returned value will be sent back to
        the other endpoint of the connection.

        :param ret_val: The values to return.
        :type ret_val: Any
        """
        # TODO - Implement this!
        pass

    def continue_serving(self) -> ServingStatus:
        """
        Creates a "continue" value used to signal the server to keep waiting for new messages.

        :return: The "continue" value of the ``ServingStatus`` class.
        :rtype: ServingStatus
        """
        return ServingStatus.CONTINUE

    def stop_serving(self) -> ServingStatus:
        """
        Creates a "stop" value used to signal the server to stop serving new messages.

        :return: The "stop" value of the ``ServingStatus`` class.
        :rtype: ServingStatus
        """
        return ServingStatus.STOP


class SimulaQronClassicalClient:
    def __init__(self, sockets_config: SocketsConfig):
        """
        Classical client used to send classical messages to remote nodes. The given node name
        must exist on the given network configuration.

        :param sockets_config: The sockets configuration for the whole network.
        :type sockets_config: SocketsConfig
        """
        self._sockets_config = sockets_config

    async def _run_client(self, hostname: str, port: int, callback: Callable[[StreamReader, StreamWriter], Awaitable[None]]):
        reader, writer = await asyncio.open_connection(hostname, port)
        await callback(reader, writer)


    def run_client(self, node_name: str, callback: Callable[[StreamReader, StreamWriter], Awaitable[None]]) -> None:
        """
        Connects to the node with the given name. Once the connection has been established,
        the given callback will be executed to start the interaction with the server.
        The given function must have the following signature::

        async def connected_handler(reader: StreamReader, writer: StreamWriter):
            # Send a message to the server
            writer.write("Hello world!".encode("utf-8"))
            # Afterwards, you might want to receive an answer
            message = await reader.read(255)
            print(message.decode("utf-8"))

        After calling this function, the

        :param node_name: The name of the node to connect to. The name *must* exist in the
                          configuration file given when constructing this client.
        :type node_name: str
        :param callback: The function to be called when the connection is established.
        :type callback: Callable[[StreamReader, StreamWriter], Awaitable[None]]
        """
        if node_name not in self._sockets_config.hostDict:
            raise RuntimeError(f"The node with name '{node_name}' is not on the network configuration.")
        socket_config = self._sockets_config.hostDict[node_name]
        asyncio.run(self._run_client(socket_config.hostname, socket_config.port, callback))

    def send_message(self, message: str) -> None:
        """
        Sends a message to the remote endpoint of the connection.

        :param message: The message to send.
        :type message: str
        """
        pass


class SimulaQronClassicalServer:
    def __init__(self, sockets_config: SocketsConfig, name: str):
        self._node_name = name
        self._sockets_data = sockets_config.hostDict[self._node_name]
        self._connection_handler: Optional[Callable[[StreamReader, StreamWriter], Awaitable[None]]] = None

    def register_client_handler(self, handler: Callable[[StreamReader, StreamWriter], Awaitable[None]]) -> None:
        """
        Registers the given function as a client handler. The given function must have the following signature::

        async def handler(reader: StreamReader, writer: StreamWriter):
            reader = await reader.read(255)
            ...
            # Handle a new connection here
            # E.g. send a response to the client
            writer.write("answer".encode("utf-8"))

        The passed function will be called once a new client connects.

        :param handler: The function to be used as a handler. This *must* be a python coroutine
                        (python "async" function).
        :type handler: Callable[[StreamReader, StreamWriter], Awaitable[None]]
        """
        self._connection_handler = handler

    async def _build_server(self):
        if self._connection_handler is None:
            print("No connection handler - Did you forget to register it?")
            return
        server = await asyncio.start_server(self._connection_handler, self._sockets_data.hostname, self._sockets_data.port)
        print(f"BOB INFO: === {self._node_name} Server ===")
        print(f"BOB DEBUG: Listening on {self._sockets_data.hostname}:{self._sockets_data.port}")
        async with server:
            await server.serve_forever()

    def start_serving(self) -> None:
        """
        Starts the serving the clients using the registered handlers.
        """
        asyncio.run(self._build_server())

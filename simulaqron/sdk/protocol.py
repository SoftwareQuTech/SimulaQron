import asyncio
from asyncio import StreamWriter, StreamReader
from typing import Awaitable, Optional, Callable, Coroutine, Any, TypeVar

from simulaqron.general.host_config import SocketsConfig

_T = TypeVar("_T")


class SimulaQronClassicalClient:
    def __init__(self, sockets_config: SocketsConfig):
        """
        Classical client used to send classical messages to remote nodes. The given socket configs
        object contains the specification of the available nodes on the network to connect to.

        :param sockets_config: The sockets configuration for the whole network.
        :type sockets_config: SocketsConfig
        """
        self._sockets_config = sockets_config

    async def connect_and_run(self, server_name: str, callback: Coroutine[Any, Any, _T],
                              *args: Any, **kwargs: Any) -> _T:
        """
        "Async" version of the `run_client` method, which can be awaited in a context of a python coroutine.
        For more information check the documentation of the `run_client` method.

        :param server_name: The name of the server to connect to. The name *must* exist in the
                          configuration file given when constructing this client.
        :type server_name: str
        :param callback: The function to be called when the connection is established. This function
                         implements the logic for interacting with the server. The passed function
                         *must* be a python "async" function.
        :type callback: Callable[[StreamReader, StreamWriter], Awaitable[None]]
        :param args: Positional arguments you want to pass into the callback.
        :type args: Any
        :param kwargs: Keyword arguments you want to pass into the callback.
        :type kwargs: Any
        """
        if server_name not in self._sockets_config.hostDict:
            raise RuntimeError(f"The node with name '{server_name}' is not on the network configuration.")
        socket_config = self._sockets_config.hostDict[server_name]
        return await self._run_client(socket_config.hostname, socket_config.port, callback, *args, **kwargs)

    async def _run_client(self, hostname: str, port: int,
                          callback: Coroutine[Any, Any, _T], *args: Any, **kwargs: Any) -> _T:
        """
        Python coroutine that opens the connection and runs the function provided by the user.
        """
        reader, writer = await asyncio.open_connection(hostname, port)
        result = await callback(reader, writer, *args, **kwargs)
        writer.close()
        return result

    def run_client(self, server_name: str, callback: Coroutine[Any, Any, _T], *args: Any, **kwargs: Any) -> _T:
        """
        Runs a function implementing a client that connects to the node with the given name.
        Once the connection has been established, the given callback will be executed to start
        the interaction with the server.
        The given client function must have the following signature::

            async def connected_handler(reader: StreamReader, writer: StreamWriter):
                # Send a message to the server
                writer.write("Hello world!".encode("utf-8"))
                # Afterwards, you might want to receive an answer
                message = await reader.read(255)
                print(message.decode("utf-8"))

        Where ``reader`` and ``writer`` objects are the streams used to read and write
        messages to/from the server respectively.
        Once the execution of the given function, the client will close the connection to
        the server.

        :param server_name: The name of the server to connect to. The name *must* exist in the
                          configuration file given when constructing this client.
        :type server_name: str
        :param callback: The function to be called when the connection is established. This function
                         implements the logic for interacting with the server. The passed function
                         *must* be a python "async" function.
        :type callback: Callable[[StreamReader, StreamWriter], Awaitable[None]]
        :param args: Positional arguments you want to pass into the callback.
        :type args: Any
        :param kwargs: Keyword arguments you want to pass into the callback.
        :type kwargs: Any
        """
        if server_name not in self._sockets_config.hostDict:
            raise RuntimeError(f"The node with name '{server_name}' is not on the network configuration.")
        socket_config = self._sockets_config.hostDict[server_name]
        return asyncio.run(self._run_client(socket_config.hostname, socket_config.port, callback, *args, **kwargs))


class SimulaQronClassicalServer:
    def __init__(self, sockets_config: SocketsConfig, name: str):
        """
        Classical server used to serve classical clients sending classical messages. The given socket configs
        object contains the specification of the available nodes on the network that this server can
        interact with. Please note that this configuration *does not limit* the clients that can
        connect to this server.

        :param sockets_config: The sockets configuration for the whole network.
        :type sockets_config: SocketsConfig
        :param name: The node name of the server. The name *must* exist in the
                     configuration file given when constructing this server.
        :type name: str
        """
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

        Where ``reader`` and ``writer`` objects are the streams used to read and write
        messages to/from the client respectively.
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
        server = await asyncio.start_server(
            self._connection_handler,
            self._sockets_data.hostname,
            self._sockets_data.port
        )
        print(f"{self._node_name.lower()} INFO: === {self._node_name} Server ===")
        print(f"{self._node_name.lower()} DEBUG: Listening on {self._sockets_data.hostname}:{self._sockets_data.port}")  # noqa: E231,E501
        async with server:
            await server.serve_forever()

    def start_serving(self) -> None:
        """
        Starts the serving the clients using the registered handlers.
        """
        asyncio.run(self._build_server())

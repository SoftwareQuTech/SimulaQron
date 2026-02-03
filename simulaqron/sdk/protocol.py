from enum import IntEnum
from pathlib import Path
from typing import Any, List, Callable, Optional

from netqasm.sdk.external import NetQASMConnection
from simulaqron.sdk import SimulaQronConnection, Socket


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


class SimulaQronProtocol:
    def __init__(self, network_config: str | Path, name: str):
        self._network_config = network_config
        self._node_name = name
        # TODO - Load the network configuration in simulaqron!
        pass


class SimulaQronClassicalClient(SimulaQronProtocol):
    def __init__(self, network_config: str | Path, name: str):
        """
        Classical client used to send classical messages to remote nodes. The given node name
        must exist on the given network configuration.

        :param network_config: The path of the Network configuration.
        :type network_config: str | Path
        :param name: The name of the node to connect to. The name *must* exist in the network
                     configuration file.
        :type name: str
        """
        super().__init__(network_config, name)

    def connect_to(self, node_name: str) -> None:
        """
        Connects to the node with the given name.

        :param node_name: The name of the node to connect to. The name *must* exist in the
                          configuration file given when constructing this client.
        :type node_name: str
        """
        pass

    def send_message(self, message: str) -> None:
        """
        Sends a message to the remote endpoint of the connection.

        :param message: The message to send.
        :type message: str
        """


class SimulaQronClassicalServer(SimulaQronProtocol):
    def __init__(self, network_config: str | Path, name: str, simulaqron_connection: Optional[SimulaQronConnection] = None):
        super().__init__(network_config, name)
        self._message_handlers: List[Callable[[SimulaQronState, str], ServingStatus]] = []
        self._connection = simulaqron_connection
        self._message_handlers: List[Callable[[SimulaQronState, str, NetQASMConnection], ServingStatus]] = []
        # TODO - Define what else to do in the constructor

    def register_message_handler(self, handler: Callable[[SimulaQronState, str], ServingStatus]) -> None:
        """
        Registers the given function as a message handler. The given function must have the following signature::

        def handler(state: SimulaQronState, message: str, connection: NetQASMConnection) -> ServingStatus:
            return ServingStatus.CONTINUE

        The passed function will be called once a message arrives form the remote.
        The function must return a value to signal the server loop to keep handling or not.
        Any other value that must be returned to the remote, must be passed using the ``add_return_values`` method
        from the ``SimulaQronState`` object passed to the handler.

        :param handler: The function to be used as a handler.
        :type handler: Callable[[SimulaQronState, str], ServingStatus]
        """
        self._message_handlers.append(handler)

    def start_serving(self) -> None:
        """
        Starts the serving the clients using the registered handlers.
        """
        # TODO - Implement
        pass

import ctypes
import socket
import time
from enum import Enum
from typing import Type, Optional, Callable, List, Tuple, Set, Dict

from multiprocess.pool import Pool
from netqasm.backend.messages import (MessageHeader,
                                      MsgDoneMessage, ReturnArrayMessage,
                                      ReturnRegMessage, ReturnMessage, deserialize_return_msg,
                                      ErrorCode, Message, APP_ID)
from netqasm.lang.ir import GenericInstr
from netqasm.lang.operand import Address, Register
import logging
from netqasm.sdk import EPRSocket
from netqasm.sdk.config import LogConfig
from netqasm.sdk.connection import BaseNetQASMConnection
from netqasm.sdk.network import NetworkInfo
from netqasm.sdk.shared_memory import SharedMemoryManager, SharedMemory
from netqasm.sdk.transpile import SubroutineTranspiler

from simulaqron.general import SimUnsupportedError
from simulaqron.general.host_config import (SocketsConfig,
                                            get_node_id_from_net_config)
from simulaqron.settings import network_config

logger = logging.getLogger("SimulaQronConnection")


class SimulaQronConnection(BaseNetQASMConnection):
    NON_STABILIZER_INSTR = [GenericInstr.T]

    # Process pool will be set externally when launching the applications
    # This is due to the fact that the code creating the connections will run
    # *inside a pool worker*, so it cannot create a new process pool because the
    # worker itself is a daemon process.
    PROCESS_POOL: Optional[Pool] = None

    def __init__(
            self,
            app_name: str,
            app_id: Optional[int] = None,
            max_qubits: int = 5,
            log_config: Optional[LogConfig] = None,
            epr_sockets: Optional[List[EPRSocket]] = None,
            compiler: Optional[Type[SubroutineTranspiler]] = None,
            socket_address=None,
            conn_retry_time: float = 0.1,
            network_name: str = "default",
    ):
        """
        Main class representing the connection from NetQASM to the SimulaQron simulator.
        This class implements the

        :param app_name: Name of the app to run.
        :type app_name: str
        :param app_id: The ID of the application. If not given, a new one will be created.
        :type app_id: int | None
        :param max_qubits: Maximum number of qubits tu simulate in the simulator.
        :type max_qubits: int
        :param log_config: Configuration of the logging. Check the documentation of
                           ``netqasm.sdk.config.LogConfig`` for more information about this.
        :type log_config: LogConfig
        :param epr_sockets: List of ``EPRSocket`` s to use in the simulator.
        :type epr_sockets: List[EPRSocket]
        :param compiler: A transpiler object that transpiles the NetQASM instructions.
        :type compiler: Type[SubroutineTranspiler] | None
        :param socket_address: A tuple containing a hostname and port to use to connect to the QNodeOS server.
        :type socket_address: Tuple[str, int]
        :param conn_retry_time: Maximum time in seconds to wait between attempts to connect to the QNoseOS server.
        :type conn_retry_time: float
        :param network_name: The name of the network to connect to
        :type network_name: str
        """
        super().__init__(
            app_name=app_name,
            # NOTE currently node_name and app_name are the same in simulaqron
            node_name=app_name,
            app_id=app_id,
            max_qubits=max_qubits,
            log_config=log_config,
            epr_sockets=epr_sockets,
            compiler=compiler,
            _init_app=False,
            _setup_epr_sockets=False,
        )

        self._qnodeos_net, self._socket = self._create_socket(
            name=self.node_name,
            socket_address=socket_address,
            network_name=network_name,
            retry_time=conn_retry_time,
        )

        # Next message ID
        self._next_msg_id: int = 0

        # Messages ID's with deferred callbacks
        self._messages_callbacks: Dict[int, Callable] = {}

        # Messages IDs we're waiting to be done
        self._waiting_msg_ids: Set[int] = set()

        # Keep track of finished msg IDs
        self._done_msg_ids: Set[int] = set()

        # Stores an error received from the backend so it can be raised after
        # _wait_for_done unblocks, rather than raising inside _handle_reply
        # (which would leave the msg_id in _waiting_msg_ids and break close())
        self._pending_error: Optional[Exception] = None

        # Buffer for returned messages
        self.buf = b""

        # Buffer for retrieved qubit states
        self._qubit_states: Dict[int, List[List[complex]]] = {}

        self._shared_memory: SharedMemory = SharedMemoryManager.create_shared_memory(app_name)

        self._init_new_app(max_qubits=max_qubits)

        self._setup_epr_sockets(epr_sockets=epr_sockets)

    @staticmethod
    def try_connection(
            name: str,
            socket_address: Optional[Tuple[str, int]] = None,
            network_name: str = "default",
    ):
        """
        Try to establish a connection to the specified node name. The connection can be made
        by specifying the ``socket_address`` tuple (as a hostname and port number tuple) or
        by specifying the node and network names. In the latter case, SimulaQron will search
        for that node and network names on the loaded network configuration, and get the
        corresponding socket configuration (hostname and port number) to connect to.

        :param name: The name of the node to connect to.
        :type name: str
        :param socket_address: A hostname-port pair to specify the hostname and port number
                               to connect to. This argument is optional.
        :type socket_address: Tuple[str, int] | None
        :param network_name: The name of the network to search the node name.
        :type network_name: str
        """
        # NOTE using retry_time=None causes an error to be raised of the connection cannot
        # be established, which can be used to check if the connection is available
        logger.debug("Trying if connection is up yet")
        SimulaQronConnection._create_socket(
            name=name,
            socket_address=socket_address,
            network_name=network_name,
            retry_time=-1.0,
        )

    def close(
        self,
        clear_app: bool = True,
        stop_backend: bool = False,
        exception: bool = False,
    ) -> None:
        """
        Closes the SimulaQron connection. It also sends the corresponding messages
        to the backend to clean up the states associated with the connection.
        This leaves the quantum backend ready to be used with a new client.

        :param clear_app: Clear the application before closing the connection.
        :type clear_app: bool
        :param stop_backend: Stop the backend when closing the connection.
        :type stop_backend: bool
        :param exception: Whether the app is stopping due to an exception or not.
        :type exception: bool
        """
        super().close(clear_app, stop_backend, exception)
        # Clear the shared memories occupied by this connection
        SharedMemoryManager.reset_memories()

    @staticmethod
    def _create_socket(
            name: str,
            network_name: str,
            socket_address: Optional[Tuple[str, int]] = None,
            retry_time: float = 0.1,
    ) -> Tuple[SocketsConfig, socket.socket]:
        # Get network configuration and addresses
        addr, qnodeos_net = SimulaQronConnection._setup_network_data(
            name=name,
            socket_address=socket_address,
            network_name=network_name,
        )

        # Open a socket to the backend
        qnodeos_socket = SimulaQronConnection._setup_socket(
            name=name, addr=addr, retry_time=retry_time
        )
        return qnodeos_net, qnodeos_socket

    @staticmethod
    def _setup_network_data(
            name: str,
            socket_address: Tuple[str, int],
            network_name: str,
    ) -> Tuple[tuple[socket.AddressFamily, socket.SocketKind, int, str, tuple[str, int]], Optional[SocketsConfig]]:
        qnodeos_net: Optional[SocketsConfig] = None
        if socket_address is None:

            qnodeos_net = SocketsConfig(network_config, network_name=network_name, config_type="qnodeos")
            # Host data
            if name in qnodeos_net.hostDict:
                myHost = qnodeos_net.hostDict[name]
            else:
                raise ValueError(
                    f"Host name '{name}' is not in the qnodeos network"
                )

                # Get IP and port number
            addr = myHost.addr

        else:
            hostname, port = socket_address
            assert isinstance(hostname, str), "hostname should be a string"
            assert isinstance(port, int), "port should be an int"
            addrs = socket.getaddrinfo(
                hostname, port, proto=socket.IPPROTO_TCP, family=socket.AF_INET
            )
            addr = addrs[0]

        return addr, qnodeos_net

    @staticmethod
    def _setup_socket(
            name: str,
            addr: tuple[socket.AddressFamily, socket.SocketKind, int, str, Tuple[str, int]],
            retry_time: float = 0.1
    ) -> socket.socket:
        qnodeos_socket = None
        while True:
            try:
                logger.debug(
                    "App %s : Trying to connect to NetQASM server (at %s)", name, addr
                )

                qnodeos_socket = socket.socket(addr[0], addr[1], addr[2])
                qnodeos_socket.connect(addr[4])
                break
            except ConnectionRefusedError as err:
                if retry_time <= 0:
                    raise err
                logger.debug(
                    "App %s : Could not connect to NetQASM server, trying again...",
                    name
                )
                time.sleep(retry_time)
                qnodeos_socket.close()
            except Exception as err:
                logger.exception(
                    "App %s : Critical error when connection to NetQASM server: %s",
                    name, err
                )
                qnodeos_socket.close()
                raise err
        logger.debug(
            "App %s : Connected to NetQASM server at %s",
            name,
            addr
        )
        return qnodeos_socket

    def _get_network_info(self) -> Type[NetworkInfo]:
        return SimulaQronNetworkInfo

    def _commit_serialized_message(
            self, raw_msg: bytes, block: bool = True, callback: Optional[Callable] = None
    ):
        """Commit a message to the backend/qnodeos"""
        msg_id = self._get_new_msg_id()
        self._waiting_msg_ids.add(msg_id)
        length = MessageHeader.len() + len(raw_msg)
        msg_hdr = MessageHeader(id=msg_id, length=length)
        written = self._socket.send(bytes(msg_hdr) + raw_msg)
        self._logger.debug("Written %d bytes to NetQASM server", written)
        if block:
            self._wait_for_done(msg_id=msg_id, callback=callback)
        else:
            # Register the callback so it will be called once the message
            # is acknowledged
            self._messages_callbacks[msg_id] = callback

    def _wait_for_done(self, msg_id: Optional[int] = None, callback: Optional[Callable] = None):
        """Waits for a message to be declared done by qnodeos.
        If `msg_id` is None (default), then we wait once for any message to be done.
        The ID of this message is then returned.
        """
        if msg_id is None:
            self._logger.debug("Waiting for any msg to be done")
        else:
            self._logger.debug("Waiting for msg ID %d", msg_id)
        while True:
            done_msg_id = self._handle_reply()
            if msg_id is None:
                # Finished waiting for any message
                break
            elif msg_id == done_msg_id:
                # Finished waiting for specified message
                if callback is not None:
                    self._logger.debug("Executing callback for message %d", done_msg_id)
                    callback()
                break
            else:
                # Other message done, not the one we're waiting for
                # Wait for another don
                continue
        self._logger.debug("Received done for msg ID %d", done_msg_id)
        if self._pending_error is not None:
            err = self._pending_error
            self._pending_error = None
            raise err

    def _read_more_data(self):
        """Reads in some more data on the socket to qnodeos"""
        try:
            data = self._socket.recv(1024)
        except Exception as err:
            self._logger.exception("Error in recv from NetQASM server")
            raise err
        if self.buf:
            self.buf += data
        else:
            self.buf = data
        self._logger.debug("Got new data '%s' on socket to qnodeos", data)

    def _handle_reply(self) -> int:
        """Handle all next replies until a done message and return the msg ID for the done"""
        # Try to read next message from the buffer otherwise read some more and try again
        # TODO - Change the while to use a condition that can be controlled externally
        while True:
            try:
                ret_msg = deserialize_return_msg(self.buf)
            except ValueError:
                # Incomplete message
                self._logger.debug("Incomplete message")
                time.sleep(0.1)
                self._read_more_data()
                continue
            except Exception as exc:
                self._logger.exception("Unexpected exception:", exc)
                continue

            # Remove the data of this message from the buffer
            self.buf = self.buf[len(ret_msg):]

            self._logger.debug("Got message %s", ret_msg)
            match ret_msg:
                case MsgDoneMessage():
                    if ret_msg.msg_id in self._done_msg_ids:
                        # Duplicate: already handled by a preceding RichErrorMessage for
                        # the same subroutine. The backend sends both; skip this one so
                        # _wait_for_done keeps looking for the message it actually needs.
                        return -1
                    self._waiting_msg_ids.remove(ret_msg.msg_id)
                    self._done_msg_ids.add(ret_msg.msg_id)
                    # Call the registered callback, if any
                    if ret_msg.msg_id in self._messages_callbacks:
                        if SimulaQronConnection.PROCESS_POOL is None:
                            raise RuntimeError("Callback process pool was not set correctly")
                        if self._messages_callbacks[ret_msg.msg_id] is not None:
                            SimulaQronConnection.PROCESS_POOL.apply_async(
                                self._messages_callbacks[ret_msg.msg_id]
                            )
                        del self._messages_callbacks[ret_msg.msg_id]
                    return ret_msg.msg_id
                case ReturnRegMessage():
                    self._update_shared_memory(
                        entry=Register.from_raw(raw=ret_msg.register),
                        value=ret_msg.value,
                    )
                    return -1
                case ReturnArrayMessage():
                    self._update_shared_memory(
                        entry=Address(address=ret_msg.address),
                        value=ret_msg.values,
                    )
                    return -1
                case ReturnQubitStateMessage():
                    # We locally store the state info to return it later. We have to
                    # do this since _handle_reply cannot return values others than the
                    # message id when handling the reply of the original message
                    self._store_qubit_state(
                        ret_msg.qubit_id,
                        ret_msg.dimension,
                        ret_msg.get_real_part(),
                        ret_msg.get_imag_part()
                    )
                    return -1
                case RichErrorMessage():
                    # Treat the error as terminal for this msg_id: unblock _wait_for_done
                    # so the client loop exits cleanly and close() can still run afterward.
                    if ret_msg.msg_id in self._waiting_msg_ids:
                        self._waiting_msg_ids.remove(ret_msg.msg_id)
                    self._done_msg_ids.add(ret_msg.msg_id)
                    if ret_msg.err_code == ErrorCode.UNSUPP.value:
                        self._pending_error = SimUnsupportedError("Operation not supported")
                    else:
                        self._pending_error = RuntimeError(
                            f"Quantum node rejected request: {ret_msg.get_err_msg()}"
                        )
                    return ret_msg.msg_id
                case _:
                    raise NotImplementedError(f"Unknown return message of type {type(ret_msg)}")

    def block(self):
        """
        Blocks the handling of new messages until all the pending message IDs are acknowledged.
        """
        while len(self._waiting_msg_ids) > 0:
            self._logger.debug(
                "Blocking and waiting for msg IDs %s", self._waiting_msg_ids
            )
            # Wait for any msg to be done
            self._wait_for_done()
        self._logger.debug("All messages done, finished blocking")

    def _update_shared_memory(self, entry: Register | Address, value: int | Optional[List[Optional[int]]]):
        shared_memory = self.shared_memory
        if isinstance(entry, Register):
            shared_memory.set_register(entry, value)
        elif isinstance(entry, Address):
            address = entry.address
            shared_memory.init_new_array(address=address, new_array=value)
        else:
            raise TypeError(
                f"Cannot update shared memory with entry specified as {entry}"
            )

    def _store_qubit_state(
            self,
            qubit_id: int,
            dimension: int,
            real_part: List[List[float]],
            imag_part: List[List[float]]
    ):
        self._logger.debug("Storing qubit state for qubit_id %d: real=%s, imag=%s",
                           qubit_id, str(real_part), str(imag_part)
                           )
        density_matrix: List[List[complex]] = []
        for i in range(dimension):
            row: List[complex] = []
            for j in range(dimension):
                row.append(real_part[i][j] + (1j * imag_part[i][j]))
            density_matrix.append(row)
        self._qubit_states[qubit_id] = density_matrix

    def _retrieve_qubit_state(self, qubit_id: int) -> List[complex]:
        if qubit_id not in self._qubit_states:
            logger.error("State for the qubit with id '%d' cannot be found in the conneciton buffer", qubit_id)
            return []
        state = self._qubit_states[qubit_id]
        del self._qubit_states[qubit_id]
        return state

    def _is_done(self, msg_id) -> bool:
        return msg_id in self._done_msg_ids

    def _get_new_msg_id(self) -> int:
        msg_id = self._next_msg_id
        self._next_msg_id += 1
        return msg_id

    def get_qubit_state(self, app_id: int, qubit_id: int) -> List[complex]:
        # Check if there are some pending (unflushed) operations on the qubit
        if len(self.builder._pending_commands) > 0:
            raise RuntimeError(f"Qubit {qubit_id} has unflushed operations")
        # Here we craft the special message that signals QNodeOS to
        # retrieve the state of a qubit.
        msg = GetQubitStateMessage(app_id=app_id, qubit_id=qubit_id)
        # We commit the message, and block until receiving a response
        self._commit_message(msg, block=True)
        # Retrieve and return the qubit state
        return self._retrieve_qubit_state(qubit_id)


# Definitions for the new message types
QUBIT_REGISTRY_NUM = ctypes.c_uint8
MAX_QUBIT_STATE_LEN = 5
MAX_ERR_MSG_LEN = 500


# "Extend" (by redefining the enum) the Message Type
class NewMessageType(Enum):
    INIT_NEW_APP = 0x00
    OPEN_EPR_SOCKET = 0x01
    SUBROUTINE = 0x02
    STOP_APP = 0x03
    SIGNAL = 0x04
    GET_QUBIT_STATE = 0xCA


# New class for the get qubit state message
class GetQubitStateMessage(Message):
    _fields_ = [
        ("app_id", APP_ID),  # type: ignore
        ("qubit_id", QUBIT_REGISTRY_NUM),
    ]
    TYPE = NewMessageType.GET_QUBIT_STATE

    def __init__(self, app_id: int = 0, qubit_id: int = 0):
        """
        Implements a specific NetQASM message to get the state of a qubit from the
        SimulaQron simulator.

        :param app_id: The app ID to get the qubit from.
        :type app_id: int
        :param qubit_id: The qubit ID to retrieve the state.
        :type qubit_id: int
        """
        super().__init__(self.TYPE.value)
        self.app_id = app_id
        self.qubit_id = qubit_id


class NewReturnMessageType(Enum):
    DONE = 0x00
    ERR = 0x01
    RET_ARR = 0x02
    RET_REG = 0x03
    RET_QUBIT_STATE = 0xFE


class RichErrorMessage(ReturnMessage):
    _fields_ = [
        ("msg_id", ctypes.c_uint32),
        ("err_code", ctypes.c_uint8),
        ("err_msg_len", ctypes.c_uint32),
        ("err_msg", MAX_ERR_MSG_LEN * ctypes.c_uint8),
    ]

    # This works because the enum types are mapped to the very same value
    TYPE = NewReturnMessageType.ERR

    def __init__(self, err_code: ErrorCode, err_msg: str, msg_id: int = 0):
        """
        Enriched message to the Host that an error occurred at the quantum node controller.

        :param err_code: The error code to report.
        :type err_code: ErrorCode
        :param err_msg: The error message.
        :type err_msg: str
        :param msg_id: The ID of the subroutine message that caused the error, so the
                       client can unblock its _wait_for_done loop for that message.
        :type msg_id: int
        """
        super().__init__(self.TYPE.value)
        self.msg_id = msg_id
        err_bytes = err_msg.encode("utf-8")
        if len(err_bytes) > MAX_ERR_MSG_LEN:
            logger.warning("Reported error message too long")
        self.err_code = err_code.value
        self.err_msg_len = len(err_bytes)
        for i, v in enumerate(err_bytes):
            self.err_msg[i] = v

    def get_err_msg(self) -> str:
        bytes_vals: List[int] = []
        for i in range(self.err_msg_len):
            bytes_vals.append(self.err_msg[i])
        return bytes(bytes_vals).decode("utf-8")


# New class for the return of the get qubit state message
class ReturnQubitStateMessage(ReturnMessage):
    # TODO - Adapt this class to accept square, 2-dim arrays
    _fields_ = [
        ("qubit_id", QUBIT_REGISTRY_NUM),
        ("dim", ctypes.c_uint32),
        ("real_part", MAX_QUBIT_STATE_LEN * (MAX_QUBIT_STATE_LEN * ctypes.c_float)),  # type: ignore
        ("imag_part", MAX_QUBIT_STATE_LEN * (MAX_QUBIT_STATE_LEN * ctypes.c_float)),  # type: ignore
    ]
    TYPE = NewReturnMessageType.RET_QUBIT_STATE

    def __init__(self, qubit_id: int, real_part: List[List[float]], imag_part: List[List[float]]):
        """
        Specific NetQASM message used to transmit the qubit state back to the application.

        :param qubit_id: The qubit ID.
        :type qubit_id: int
        :param real_part: The real part of the qubit state.
        :type real_part: List[List[float]]
        :param imag_part: The imaginary part of the qubit state.
        :type imag_part: List[List[float]]
        """
        super().__init__(self.TYPE.value)

        # Sanity checks - given matrices are square
        assert len(real_part) > 0
        assert len(imag_part) > 0
        assert len(real_part) == len(imag_part) and True
        for row in real_part:
            assert len(row) > 0
            assert len(row) == len(real_part)
        for row in imag_part:
            assert len(row) > 0
            assert len(row) == len(imag_part)

        self.qubit_id = qubit_id
        self.dim = len(real_part)
        if self.dim > MAX_QUBIT_STATE_LEN:
            logger.warning("Return qubit state message too long")
        for i in range(self.dim):
            for j in range(self.dim):
                self.real_part[i][j] = real_part[i][j]
                self.imag_part[i][j] = imag_part[i][j]

    @property
    def dimension(self) -> int:
        return self.dim

    def get_real_part(self) -> List[List[float]]:
        real_part: List[List[float]] = []
        for i in range(self.dim):
            row: List[float] = []
            for j in range(self.dim):
                row.append(float(self.real_part[i][j]))
            real_part.append(row)
        return real_part

    def get_imag_part(self) -> List[List[float]]:
        imag_part: List[List[float]] = []
        for i in range(self.dim):
            row: List[float] = []
            for j in range(self.dim):
                row.append(float(self.imag_part[i][j]))
            imag_part.append(row)
        return imag_part


# Really dark magic to *replace* the definitions from the netqasm library
import netqasm.backend.messages as nmsg  # noqa: E402

nmsg.MessageType = NewMessageType
nmsg.ReturnMessageType = NewReturnMessageType
nmsg.MESSAGE_CLASSES = {
    nmsg.MessageType.INIT_NEW_APP: nmsg.InitNewAppMessage,
    nmsg.MessageType.OPEN_EPR_SOCKET: nmsg.OpenEPRSocketMessage,
    nmsg.MessageType.SUBROUTINE: nmsg.SubroutineMessage,
    nmsg.MessageType.STOP_APP: nmsg.StopAppMessage,
    nmsg.MessageType.SIGNAL: nmsg.SignalMessage,
    NewMessageType.GET_QUBIT_STATE: GetQubitStateMessage
}
nmsg.RETURN_MESSAGE_CLASSES = {
    nmsg.ReturnMessageType.DONE: MsgDoneMessage,
    nmsg.ReturnMessageType.ERR: RichErrorMessage,
    nmsg.ReturnMessageType.RET_REG: ReturnRegMessage,
    nmsg.ReturnMessageType.RET_ARR: ReturnArrayMessage,
    NewReturnMessageType.RET_QUBIT_STATE: ReturnQubitStateMessage,
}


class SimulaQronNetworkInfo(NetworkInfo):
    @classmethod
    def _get_node_id(cls, node_name: str) -> int:
        """Returns the node id for the node with the given name"""
        # TODO always use network name "default"?
        _qnodeos_net = SocketsConfig(network_config, config_type="qnodeos")
        return get_node_id_from_net_config(_qnodeos_net, node_name)

    @classmethod
    def _get_node_name(cls, node_id: int) -> str:
        """Returns the node name for the node with the given ID"""
        # TODO always use network name "default"?
        _qnodeos_net = SocketsConfig(network_config, config_type="qnodeos")
        for node_name, host in _qnodeos_net.hostDict.items():
            if node_id == host.ip:
                return node_name
        raise KeyError("Unknown node ID {node_id}")

    @classmethod
    def get_node_id_for_app(cls, app_name: str) -> int:
        """
        Returns the node id for the app with the given name.

        :param app_name: The app name.
        :type app_name: str
        :return: The node ID.
        :rtype: int
        """
        # NOTE app_name and node_name are for now the same in simulaqron
        return cls._get_node_id(node_name=app_name)

    @classmethod
    def get_node_name_for_app(cls, app_name: str) -> str:
        """
        Returns the node name for the app with the given name.

        :param app_name: The app name.
        :type app_name: str
        :return: The node name.
        :rtype: str
        """
        # NOTE app_name and node_name are for now the same in simulaqron
        return app_name

import ctypes
import socket
import time
from enum import Enum
from threading import Thread
from typing import Type, Optional, Callable, List, Tuple, Set, Dict

from netqasm.backend.messages import (MessageHeader,
                                      MsgDoneMessage, ReturnArrayMessage,
                                      ReturnRegMessage, ReturnMessage, deserialize_return_msg,
                                      ErrorCode, Message, APP_ID)
from netqasm.lang.ir import GenericInstr
from netqasm.lang.operand import Address, Register
from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk import EPRSocket
from netqasm.sdk.config import LogConfig
from netqasm.sdk.connection import BaseNetQASMConnection
from netqasm.sdk.network import NetworkInfo
from netqasm.sdk.shared_memory import SharedMemoryManager, SharedMemory
from netqasm.sdk.transpile import SubroutineTranspiler

from simulaqron.general import SimUnsupportedError
from simulaqron.general.host_config import (SocketsConfig,
                                            get_node_id_from_net_config)
from simulaqron.settings import simulaqron_settings

logger = get_netqasm_logger("SimulaQronConnection")


class SimulaQronConnection(BaseNetQASMConnection):
    NON_STABILIZER_INSTR = [GenericInstr.T]

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
            network_name: Optional[str] = None,
    ):
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

        # Messages IDs we're waiting to be done
        self._waiting_msg_ids: Set[int] = set()

        # Keep track of finished msg IDs
        self._done_msg_ids: Set[int] = set()

        # Buffer for returned messages
        self.buf = b""

        # Buffer for retrieved qubit states
        self._qubit_states: Dict[int, List[complex]] = {}

        self._shared_memory: SharedMemory = SharedMemoryManager.create_shared_memory(app_name)

        self._init_new_app(max_qubits=max_qubits)

        self._setup_epr_sockets(epr_sockets=epr_sockets)

    @staticmethod
    def try_connection(
            name: str,
            socket_address: Optional[Tuple[str, int]] = None,
            network_name: str = None,
    ):
        # NOTE using retry_time=None causes an error to be raised of the connection cannot
        # be established, which can be used to check if the connection is available
        logger.debug("Trying if connection is up yet")
        SimulaQronConnection._create_socket(
            name=name,
            socket_address=socket_address,
            network_name=network_name,
            retry_time=None,
        )

    @staticmethod
    def _create_socket(
            name: str,
            socket_address: Optional[Tuple[str, int]] = None,
            network_name: str = None,
            retry_time: Optional[float] = 0.1,
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
            qnodeos_net = _get_qnodeos_net_config(network_name=network_name)

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
                if retry_time is None or retry_time == 0:
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
        self._socket.send(bytes(msg_hdr) + raw_msg)
        if block:
            self._wait_for_done(msg_id=msg_id)
        else:
            # Execute callback in a new thread after the subroutine is finished
            thread = Thread(
                target=self._wait_for_done,
                kwargs={
                    "msg_id": msg_id,
                    "callback": callback,
                }
            )
            thread.daemon = True
            thread.start()

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

    def _read_more_data(self):
        """Reads in some more data on the socket to qnodeos"""
        data = self._socket.recv(1024)
        if self.buf:
            self.buf += data
        else:
            self.buf = data
        self._logger.debug("Got new data %s on socket to qnodeos", data)

    def _handle_reply(self) -> int:
        """Handle all next replies until a done message and return the msg ID for the done"""
        # Try to read next message from the buffer otherwise read some more and try again
        try:
            ret_msg = deserialize_return_msg(self.buf)
        except ValueError:
            # Incomplete message
            self._logger.debug("Incomplete message")
            time.sleep(0.1)
            self._read_more_data()
            return self._handle_reply()

        # Remove the data of this message from the buffer
        self.buf = self.buf[len(ret_msg):]

        self._logger.debug("Got message %s", ret_msg)
        if isinstance(ret_msg, MsgDoneMessage):
            self._waiting_msg_ids.remove(ret_msg.msg_id)
            self._done_msg_ids.add(ret_msg.msg_id)
            return ret_msg.msg_id
        elif isinstance(ret_msg, ReturnRegMessage):
            self._update_shared_memory(
                entry=Register.from_raw(raw=ret_msg.register),
                value=ret_msg.value,
            )
        elif isinstance(ret_msg, ReturnArrayMessage):
            self._update_shared_memory(
                entry=Address(address=ret_msg.address),
                value=ret_msg.values,
            )
        elif isinstance(ret_msg, ReturnQubitStateMessage):
            # We locally store the state info to return it later. We have to
            # do this since _handle_reply cannot return values others than the
            # message id when handling the reply of the original message
            self._store_qubit_state(
                ret_msg.qubit_id,
                ret_msg.get_real_part(),
                ret_msg.get_imag_part()
            )
        elif isinstance(ret_msg, RichErrorMessage):
            if ret_msg.err_code == ErrorCode.UNSUPP.value:
                raise SimUnsupportedError("Operation not supported")
            else:
                raise RuntimeError(f"Received error message from backend: {ret_msg.get_err_msg()}")
        else:
            raise NotImplementedError(f"Unknown return message of type {type(ret_msg)}")
        # Continue handling replies until a done
        return self._handle_reply()

    def block(self):
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

    def _store_qubit_state(self, qubit_id: int, real_part: List[float], imag_part: List[float]):
        self._logger.debug("Storing qubit state for qubit_id %d: real=%s, imag=%s",
                           qubit_id, str(real_part), str(imag_part)
                           )
        # Reconstruct the complex numbers
        self._qubit_states[qubit_id] = [r + (1j * j) for r, j in zip(real_part, imag_part)]

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
MAX_ERR_MSG_LEN = 100


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
    """Enriched message to the Host that an error occurred at the quantum node controller."""

    _fields_ = [
        ("err_code", ctypes.c_uint8),
        ("err_msg_len", ctypes.c_uint32),
        ("err_msg", MAX_ERR_MSG_LEN * ctypes.c_uint8),
    ]

    # This works because the enum types are mapped to the very same value
    TYPE = NewReturnMessageType.ERR

    def __init__(self, err_code: ErrorCode, err_msg: str):
        super().__init__(self.TYPE.value)
        err_bytes = err_msg.encode("utf-8")
        if len(err_bytes) > MAX_ERR_MSG_LEN:
            logger.warning("Reported error message too long")
        self.err_code = err_code.value
        self.err_msg_len = len(err_bytes)
        for i, v in enumerate(err_bytes):
            self.err_msg[i] = v
        print("here")

    def get_err_msg(self) -> str:
        bytes_vals: List[int] = []
        for i in range(self.err_msg_len):
            bytes_vals.append(self.err_msg[i])
        return bytes(bytes_vals).decode("utf-8")


# New class for the return of the get qubit state message
class ReturnQubitStateMessage(ReturnMessage):
    _fields_ = [
        ("qubit_id", QUBIT_REGISTRY_NUM),
        ("len_real", ctypes.c_uint32),
        ("len_imag", ctypes.c_uint32),
        ("real_part", MAX_QUBIT_STATE_LEN * ctypes.c_float),  # type: ignore
        ("imag_part", MAX_QUBIT_STATE_LEN * ctypes.c_float),  # type: ignore
    ]
    TYPE = NewReturnMessageType.RET_QUBIT_STATE

    def __init__(self, qubit_id: int, real_part: List[float], imag_part: List[float]):
        super().__init__(self.TYPE.value)
        self.qubit_id = qubit_id
        self.len_real = len(real_part)
        self.len_imag = len(imag_part)
        if self.len_real > MAX_QUBIT_STATE_LEN or self.len_imag > MAX_QUBIT_STATE_LEN:
            logger.warning("Return qubit state message too long")
        for i, v in enumerate(real_part):
            self.real_part[i] = v
        for i, v in enumerate(imag_part):
            self.imag_part[i] = v

    def get_real_part(self) -> List[float]:
        real_part: List[float] = []
        for i in range(self.len_real):
            real_part.append(float(self.real_part[i]))
        return real_part

    def get_imag_part(self) -> List[float]:
        imag_part: List[float] = []
        for i in range(self.len_imag):
            imag_part.append(float(self.imag_part[i]))
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


def _get_qnodeos_net_config(network_name: str) -> SocketsConfig:
    network_config_file = simulaqron_settings.network_config_file
    return SocketsConfig(
        network_config_file, network_name=network_name, config_type="qnodeos"
    )


class SimulaQronNetworkInfo(NetworkInfo):
    @classmethod
    def _get_node_id(cls, node_name: str) -> int:
        """Returns the node id for the node with the given name"""
        # TODO always use network name "default"?
        _qnodeos_net = _get_qnodeos_net_config(network_name="default")
        return get_node_id_from_net_config(_qnodeos_net, node_name)

    @classmethod
    def _get_node_name(cls, node_id: int) -> str:
        """Returns the node name for the node with the given ID"""
        # TODO always use network name "default"?
        _qnodeos_net = _get_qnodeos_net_config(network_name="default")
        for node_name, host in _qnodeos_net.hostDict.items():
            if node_id == host.ip:
                return node_name
        raise KeyError("Unknown node ID {node_id}")

    @classmethod
    def get_node_id_for_app(cls, app_name: str) -> int:
        """Returns the node id for the app with the given name"""
        # NOTE app_name and node_name are for now the same in simulaqron
        return cls._get_node_id(node_name=app_name)

    @classmethod
    def get_node_name_for_app(cls, app_name: str) -> str:
        """Returns the node name for the app with the given name"""
        # NOTE app_name and node_name are for now the same in simulaqron
        return app_name

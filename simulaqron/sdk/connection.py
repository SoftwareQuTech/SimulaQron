import socket
import time
from typing import Type

from netqasm.backend.messages import (ErrorMessage, MessageHeader,
                                      MsgDoneMessage, ReturnArrayMessage,
                                      ReturnRegMessage, deserialize_return_msg)
from netqasm.lang.ir import GenericInstr
from netqasm.lang.operand import Address, Register
from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.connection import BaseNetQASMConnection
from netqasm.sdk.network import NetworkInfo
from netqasm.sdk.shared_memory import SharedMemoryManager
from simulaqron.general import SimUnsupportedError
from simulaqron.general.host_config import (SocketsConfig,
                                            get_node_id_from_net_config)
from simulaqron.settings import SimBackend, simulaqron_settings

logger = get_netqasm_logger("SimulaQronConnection")


class SimulaQronConnection(BaseNetQASMConnection):

    NON_STABILIZER_INSTR = [GenericInstr.T]

    def __init__(
        self,
        app_name,
        app_id=None,
        max_qubits=5,
        log_config=None,
        epr_sockets=None,
        compiler=None,
        socket_address=None,
        conn_retry_time=0.1,
        network_name=None,
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
        self._next_msg_id = 0

        # Messages IDs we're waiting to be done
        self._waiting_msg_ids = set()

        # Keep track of finished msg IDs
        self._done_msg_ids = set()

        # Buffer for returned messages
        self.buf = b""

        self._shared_memory = SharedMemoryManager.create_shared_memory(app_name)

        self._init_new_app(max_qubits=max_qubits)

        self._setup_epr_sockets(epr_sockets=epr_sockets)

    @staticmethod
    def try_connection(
        name,
        socket_address=None,
        network_name=None,
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
        name,
        socket_address=None,
        network_name=None,
        retry_time=0.1,
    ):
        # Get network configuraton and addresses
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
        name,
        socket_address,
        network_name,
    ):
        addr = None
        qnodeos_net = None
        if socket_address is None:
            qnodeos_net = _get_qnodeos_net_config(network_name=network_name)

            # Host data
            if name in qnodeos_net.hostDict:
                myHost = qnodeos_net.hostDict[name]
            else:
                raise ValueError(
                    "Host name '{}' is not in the qnodeos network".format(name)
                )

                # Get IP and port number
            addr = myHost.addr

        if socket_address is not None:
            hostname, port = socket_address
            assert isinstance(hostname, str), "hostname should be a string"
            assert isinstance(port, int), "port should be an int"
            addrs = socket.getaddrinfo(
                hostname, port, proto=socket.IPPROTO_TCP, family=socket.AF_INET
            )
            addr = addrs[0]

        return addr, qnodeos_net

    @staticmethod
    def _setup_socket(name, addr, retry_time=0.1):
        qnodeos_socket = None
        while True:
            try:
                logger.debug(
                    f"App {name} : Trying to connect to NetQASM server (at {addr[-1]})"
                )

                qnodeos_socket = socket.socket(addr[0], addr[1], addr[2])
                qnodeos_socket.connect(addr[4])
                break
            except ConnectionRefusedError as err:
                if retry_time is None or retry_time == 0:
                    raise err
                logger.debug(
                    "App {} : Could not connect to  NetQASM server, trying again...".format(
                        name
                    )
                )
                time.sleep(retry_time)
                qnodeos_socket.close()
            except Exception as err:
                logger.exception(
                    "App {} : Critical error when connection to NetQASM server: {}".format(
                        name, err
                    )
                )
                qnodeos_socket.close()
                raise err
        logger.debug(
            "App {} : Could not connect to  NetQASM server, trying again...".format(
                name
            )
        )
        return qnodeos_socket

    def _get_network_info(self) -> Type[NetworkInfo]:
        return SimulaQronNetworkInfo

    def _commit_serialized_message(self, raw_msg, block=True, callback=None):
        """Commit a message to the backend/qnodeos"""
        msg_id = self._get_new_msg_id()
        self._waiting_msg_ids.add(msg_id)
        length = MessageHeader.len() + len(raw_msg)
        msg_hdr = MessageHeader(id=msg_id, length=length)
        self._socket.send(bytes(msg_hdr) + raw_msg)
        if callback is not None:
            raise NotImplementedError("Callback not yet implemented")
        if block:
            self._wait_for_done(msg_id=msg_id)

    def _wait_for_done(self, msg_id=None):
        """Waits for a message to be declared done by qnodeos.
        If `msg_id` is None (default), then we wait once for any message to be done.
        The ID of this message is then returned.
        """
        if msg_id is None:
            self._logger.debug("Waiting for any msg to be done")
        else:
            self._logger.debug(f"Waiting for msg ID {msg_id}")
        while True:
            done_msg_id = self._handle_reply()
            if msg_id is None:
                # Finished waiting for any message
                break
            elif msg_id == done_msg_id:
                # Finished waiting for specified message
                break
            else:
                # Other message done, not the one we're waiting for
                # Wait for another don
                continue
        self._logger.debug(f"Received done for msg ID {done_msg_id}")

    def _read_more_data(self):
        """Reads in some more data on the socket to qnodeos"""
        data = self._socket.recv(1024)
        if self.buf:
            self.buf += data
        else:
            self.buf = data
        self._logger.debug(f"Got new data {data} on socket to qnodeos")

    def _handle_reply(self):
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

        self._logger.debug(f"Got message {ret_msg}")
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
        elif isinstance(ret_msg, ErrorMessage):
            raise RuntimeError(f"Received error message from backend: {ret_msg}")
        else:
            raise NotImplementedError(f"Unknown return message of type {type(ret_msg)}")
        # Continue handling replies until a done
        return self._handle_reply()

    def block(self):
        while len(self._waiting_msg_ids) > 0:
            self._logger.debug(
                f"Blocking and waiting for msg IDs {self._waiting_msg_ids}"
            )
            # Wait for any msg to be done
            self._wait_for_done()
        self._logger.debug("All messages done, finished blocking")

    def _update_shared_memory(self, entry, value):
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

    def add_single_qubit_commands(self, instr, qubit_id):
        # NOTE override to check that formalism supports operation
        if instr in self.NON_STABILIZER_INSTR:
            if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
                raise SimUnsupportedError(
                    f"Cannot perform instr {instr} when using stabilizer formalism"
                )
        super().add_single_qubit_commands(instr=instr, qubit_id=qubit_id)

    def add_single_qubit_rotation_commands(
        self, instruction, virtual_qubit_id, n=0, d=0, angle=None
    ):
        # NOTE override to check that formalism supports operation
        if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
            raise SimUnsupportedError(
                "Cannot perform rotations when using stabilizer formalism"
            )
        super().add_single_qubit_rotation_commands(
            instruction=instruction,
            virtual_qubit_id=virtual_qubit_id,
            n=n,
            d=d,
            angle=angle,
        )

    def _is_done(self, msg_id):
        return msg_id in self._done_msg_ids

    def _get_new_msg_id(self):
        msg_id = self._next_msg_id
        self._next_msg_id += 1
        return msg_id


def _get_qnodeos_net_config(network_name):
    network_config_file = simulaqron_settings.network_config_file
    qnodeos_net = SocketsConfig(
        network_config_file, network_name=network_name, config_type="qnodeos"
    )

    return qnodeos_net


class SimulaQronNetworkInfo(NetworkInfo):
    @classmethod
    def _get_node_id(cls, node_name):
        """Returns the node id for the node with the given name"""
        # TODO always use network name "default"?
        _qnodeos_net = _get_qnodeos_net_config(network_name="default")
        return get_node_id_from_net_config(_qnodeos_net, node_name)

    @classmethod
    def _get_node_name(cls, node_id):
        """Returns the node name for the node with the given ID"""
        # TODO always use network name "default"?
        _qnodeos_net = _get_qnodeos_net_config(network_name="default")
        for node_name, host in _qnodeos_net.hostDict.items():
            if node_id == host.ip:
                return node_name
        raise KeyError("Unknown node ID {node_id}")

    @classmethod
    def get_node_id_for_app(cls, app_name):
        """Returns the node id for the app with the given name"""
        # NOTE app_name and node_name are for now the same in simulaqron
        return cls._get_node_id(node_name=app_name)

    @classmethod
    def get_node_name_for_app(cls, app_name):
        """Returns the node name for the app with the given name"""
        # NOTE app_name and node_name are for now the same in simulaqron
        return app_name

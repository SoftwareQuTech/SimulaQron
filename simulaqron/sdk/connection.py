import time
import socket

from netqasm.logging import get_netqasm_logger
from netqasm.sdk.connection import NetQASMConnection
from netqasm.instructions.operand import Register, Address
from simulaqron.settings import simulaqron_settings
from simulaqron.general.host_config import SocketsConfig
# from simulaqron.sdk.messages import MessageID, MessageLength
from simulaqron.sdk.messages import MessageHeader, MsgDoneMessage, ReturnRegMessage, ReturnArrayMessage, ErrorMessage
from simulaqron.sdk.messages import deserialize as deserialize_return_message


logger = get_netqasm_logger("SimulaQronConnection")


class SimulaQronConnection(NetQASMConnection):
    def __init__(
        self,
        name,
        socket_address=None,
        conn_retry_time=0.1,
        network_name=None,
        epr_sockets=None,
        **kwargs,
    ):
        super().__init__(name=name, _init_app=False, _setup_epr_sockets=False, **kwargs)

        self._qnodeos_net, self._socket = self._create_socket(
            name=self.name,
            socket_address=socket_address,
            network_name=network_name,
            retry_time=conn_retry_time,
        )

        # Next message ID
        self._next_msg_id = 0

        # Keep track of finished msg IDs
        self._done_msg_ids = set()

        # Buffer for returned messages
        self.buf = None
     
        self._init_new_app(max_qubits=self._max_qubits)

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
        qnodeos_socket = SimulaQronConnection._setup_socket(name=name, addr=addr, retry_time=retry_time)
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
            qnodeos_net = SimulaQronConnection._get_qnodeos_net_config(network_name=network_name)

            # Host data
            if name in qnodeos_net.hostDict:
                myHost = qnodeos_net.hostDict[name]
            else:
                raise ValueError("Host name '{}' is not in the qnodeos network".format(name))

                # Get IP and port number
            addr = myHost.addr

        if socket_address is not None:
            hostname, port = socket_address
            assert isinstance(hostname, str), "hostname should be a string"
            assert isinstance(port, int), "port should be an int"
            addrs = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP, family=socket.AF_INET)
            addr = addrs[0]

        return addr, qnodeos_net

    @staticmethod
    def _get_qnodeos_net_config(network_name):
        network_config_file = simulaqron_settings.network_config_file
        qnodeos_net = SocketsConfig(network_config_file, network_name=network_name, config_type="qnodeos")

        return qnodeos_net

    @staticmethod
    def _setup_socket(name, addr, retry_time=0.1):
        qnodeos_socket = None
        while True:
            try:
                logger.debug(f"App {name} : Trying to connect to NetQASM server ({addr})")

                qnodeos_socket = socket.socket(addr[0], addr[1], addr[2])
                qnodeos_socket.connect(addr[4])
                break
            except ConnectionRefusedError as err:
                if retry_time is None or retry_time == 0:
                    raise err
                logger.debug("App {} : Could not connect to  NetQASM server, trying again...".format(name))
                time.sleep(retry_time)
                qnodeos_socket.close()
            except Exception as err:
                logger.exception(
                    "App {} : Critical error when connection to NetQASM server: {}"
                    .format(name, err)
                )
                qnodeos_socket.close()
                raise err
        return qnodeos_socket

    def _commit_serialized_message(self, raw_msg, block=True, callback=None):
        """Commit a message to the backend/qnodeos"""
        msg_id = self._get_new_msg_id()
        length = MessageHeader.len() + len(raw_msg)
        msg_hdr = MessageHeader(id=msg_id, length=length)
        print(f"{self.name} msg_hdr: {msg_hdr}")
        # length = MessageLength(MessageID.len() + MessageLength.len() + len(raw_msg))
        print(f"{self.name} msg_id: {msg_id}")
        print(f"{self.name} length: {length}")
        # self._socket.send(bytes(msg_id) + bytes(length) + raw_msg)
        self._socket.send(bytes(msg_hdr) + raw_msg)
        if callback is not None:
            raise NotImplementedError("Callback not yet implemented")
        print(f"{self.name} block = {block}")
        if block:
            self._wait_for_done(msg_id=msg_id)

    def _wait_for_done(self, msg_id):
        print(f'{self.name} waiting for msg ID {msg_id}')
        while not self._is_done(msg_id=msg_id):
            self._handle_reply()
            time.sleep(0.1)
        print(f'{self.name} finished waiting for msg ID {msg_id} ({self._done_msg_ids})')

    def _handle_reply(self):
        print("connection receiving")
        data = self._socket.recv(1024)
        if self.buf:
            self.buf += data
        else:
            self.buf = data
        logger.debug(f"Buffer is now {self.buf}")
       
        while True:
            try:
                ret_msg = deserialize_return_message(self.buf)
            except ValueError:
                logger.debug("Incomplete message")
                # Incomplete message
                return

            self.buf = self.buf[len(ret_msg):]

            logger.debug(f"Got message {ret_msg}")
            if isinstance(ret_msg, MsgDoneMessage):
                self._done_msg_ids.add(ret_msg.msg_id)
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

    def _update_shared_memory(self, entry, value):
        print(f"updating entry {entry} ({type(entry)}) to be {value} ({type(value)})")
        shared_memory = self.shared_memory
        if isinstance(entry, Register):
            shared_memory.set_register(entry, value)
        elif isinstance(entry, Address):
            address = entry.address
            shared_memory.init_new_array(address=address, new_array=value)
        else:
            raise TypeError(
                f"Cannot update shared memory with entry specified as {entry}")

    def _is_done(self, msg_id):
        return msg_id in self._done_msg_ids

    def _get_new_msg_id(self):
        msg_id = self._next_msg_id
        self._next_msg_id += 1
        return msg_id

    def _get_node_id(self, node_name):
        """Returns the node id for the node with the given name"""
        host = self._qnodeos_net.hostDict[node_name]
        # NOTE now only return IP (also port?)
        return host.ip

    def _get_node_name(self, node_id):
        """Returns the node name for the node with the given ID"""
        for node_name, host in self._qnodeos_net.hostDict.items():
            if node_id == host.ip:
                return node_name
        raise KeyError("Unknown node ID {node_id}")

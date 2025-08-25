import dill
import socket
import time
from typing import Optional

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.classical_communication.socket import Socket as _Socket
from simulaqron.general.host_config import SocketsConfig, Host
from simulaqron.settings import simulaqron_settings


class Socket(_Socket):

    RETRY_TIME = 0.1

    def __init__(
        self,
        app_name,
        remote_app_name,
        socket_id=0,
        timeout: Optional[int] = None,
        use_callbacks=False,
        network_name="default",
        log_config=None,
    ):
        assert socket_id == 0, (
            "SimulaQron socket does not support setting socket ID, this is instead done in the config file"
        )
        self._node_name = app_name
        self._remote_node_name = remote_app_name
        self._use_callbacks = use_callbacks
        self._network_name = network_name

        self._logger = get_netqasm_logger(f"{self.__class__.__name__}({app_name} <-> {remote_app_name})")
        self._timeout = timeout
        self._app_socket: socket.socket = self._connect()

    def __del__(self):
        if self._app_socket:
            self._app_socket.close()

    def send(self, msg: str):
        """Sends a message to the remote node."""
        self._logger.debug("Sending msg '%s'", msg)
        raw_msg = self._serialize_msg(msg=msg)
        self._app_socket.send(raw_msg)

    def send_structured(self, msg: StructuredMessage):
        self._logger.debug("Sending structured msg '%s'", msg)
        raw_msg = self._serialize_structured_msg(msg=msg)
        self._app_socket.send(raw_msg)

    def send_silent(self, msg: str):
        self.send(msg)

    def _base_recv(self, block: bool, timeout: float, maxsize: int) -> bytes:
        if block:
            self._app_socket.setblocking(block)

        old_timeout = self._app_socket.gettimeout()
        self._app_socket.settimeout(timeout)
        raw_msg = self._app_socket.recv(maxsize)
        self._app_socket.settimeout(old_timeout)

        if not block and not raw_msg:
            raise RuntimeError("No message to receive (not blocking)")
        return raw_msg

    def recv(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
        maxsize: Optional[int] = 1024
    ) -> str:
        """Receive a message from the remote node."""
        self._logger.debug("Receiving msg")
        raw_msg = self._base_recv(block, timeout, maxsize)
        msg = self._deserialize_msg(raw_msg=raw_msg)
        self._logger.debug("Msg '%s' received", msg)
        return msg

    def recv_structured(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
        maxsize: Optional[int] = 1024,
    ) -> StructuredMessage:
        self._logger.debug("Receiving structured msg")
        raw_msg = self._base_recv(block, timeout, maxsize)
        msg = self._deserialize_structured_msg(raw_msg=raw_msg)
        self._logger.debug("Msg '%s' received", msg)
        return msg

    def recv_silent(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
        maxsize: Optional[int] = None,
    ) -> str:
        return self.recv()

    @staticmethod
    def _serialize_msg(msg: str):
        return msg.encode('utf-8')

    @staticmethod
    def _deserialize_msg(raw_msg: bytes):
        return raw_msg.decode('utf-8')

    @staticmethod
    def _serialize_structured_msg(msg: StructuredMessage):
        return dill.dumps(msg)

    @staticmethod
    def _deserialize_structured_msg(raw_msg: bytes) -> StructuredMessage:
        return dill.loads(raw_msg)

    @property
    def is_server(self) -> bool:
        # Server will always be the "first"
        return self._node_name < self._remote_node_name

    def _connect(self) -> socket.socket:
        if self.is_server:
            server_name = self._node_name
        else:
            server_name = self._remote_node_name
        addr = self._get_addr_info(name=server_name)
        app_socket = socket.socket(addr[0], addr[1], addr[2])

        if self.is_server:
            self._logger.debug("Trying to open application socket as server")
            app_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            while True:
                try:
                    app_socket.bind(addr[4])
                except OSError as err:
                    self._logger.debug(
                        "Could not bind socket since: %s\nTrying again in %ds...",
                        err, self.RETRY_TIME
                    )
                    time.sleep(self.RETRY_TIME)
                else:
                    break
            app_socket.listen(1)
            app_socket.settimeout(self._timeout)
            conn, _ = app_socket.accept()
            connected_socket = conn
        else:
            self._logger.debug("Trying to open application socket as client")
            while True:
                try:
                    app_socket.settimeout(self._timeout)
                    app_socket.connect(addr[4])
                except ConnectionRefusedError:
                    self._logger.debug(
                        "Could not open application socket, trying again in %d s...",
                        self.RETRY_TIME
                    )
                    time.sleep(self.RETRY_TIME)
                else:
                    break
            connected_socket = app_socket

        self._logger.debug("Application socket opened")
        return connected_socket

    def _get_addr_info(self, name):
        app_net = self._get_app_net_config()
        remote_host: Host = app_net.hostDict.get(name)
        if remote_host is None:
            raise ValueError(f"Host name '{name}' is not in the app network")
        return remote_host.addr

    def _get_app_net_config(self) -> SocketsConfig:
        network_config_file = simulaqron_settings.network_config_file
        app_net = SocketsConfig(network_config_file, network_name=self._network_name, config_type="app")
        return app_net

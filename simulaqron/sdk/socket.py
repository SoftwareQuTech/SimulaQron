import pickle
import socket
import time

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.classical_communication.socket import Socket as _Socket
from simulaqron.general.host_config import SocketsConfig
from simulaqron.settings import simulaqron_settings


class Socket(_Socket):

    RETRY_TIME = 0.1

    def __init__(
        self,
        app_name,
        remote_app_name,
        socket_id=0,
        timeout=None,
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
        self._app_socket = None

        self._connect()

    def __del__(self):
        if self._app_socket:
            self._app_socket.close()

    def send(self, msg):
        """Sends a message to the remote node."""
        self._logger.debug(f"Sending msg '{msg}'")
        raw_msg = self._serialize_msg(msg=msg)
        self._app_socket.send(raw_msg)

    def send_structured(self, msg):
        self._logger.debug(f"Sending structured msg '{msg}'")
        raw_msg = self._serialize_structured_msg(msg=msg)
        self._app_socket.send(raw_msg)

    def send_silent(self, msg):
        self.send(msg)

    def recv(self, block=True, maxsize=1024):
        """Receive a message from the remote node."""
        self._logger.debug("Receiving msg")
        self._app_socket.setblocking(block)
        raw_msg = self._app_socket.recv(maxsize)
        if not block and not raw_msg:
            raise RuntimeError("No message to receive (not blocking)")
        msg = self._deserialize_msg(raw_msg=raw_msg)
        self._logger.debug(f"Msg '{msg}' received")
        return msg

    def recv_structured(self, block=True, maxsize=1024):
        self._logger.debug("Receiving structured msg")
        self._app_socket.setblocking(block)
        raw_msg = self._app_socket.recv(maxsize)
        if not block and not raw_msg:
            raise RuntimeError("No message to receive (not blocking)")
        msg = self._deserialize_structured_msg(raw_msg=raw_msg)
        self._logger.debug(f"Msg '{msg}' received")
        return msg

    def recv_silent(self):
        return self.recv()

    @staticmethod
    def _serialize_msg(msg):
        return msg.encode('utf-8')

    @staticmethod
    def _deserialize_msg(raw_msg):
        return raw_msg.decode('utf-8')

    @staticmethod
    def _serialize_structured_msg(msg):
        return pickle.dumps(msg)

    @ staticmethod
    def _deserialize_structured_msg(raw_msg):
        return pickle.loads(raw_msg)

    @ property
    def is_server(self):
        # Server will always be the "first"
        return self._node_name < self._remote_node_name

    def _connect(self):
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
                    self._logger.debug(f"Could not bind socket since: {err}\n"
                                       f"Trying again in {self.RETRY_TIME}s...")
                    time.sleep(self.RETRY_TIME)
                else:
                    break
            app_socket.listen(1)
            conn, _ = app_socket.accept()
            self._app_socket = conn
        else:
            self._logger.debug("Trying to open application socket as client")
            while True:
                try:
                    app_socket.connect(addr[4])
                except ConnectionRefusedError:
                    self._logger.debug(
                        f"Could not open application socket, "
                        f"trying again in {self.RETRY_TIME}s..."
                    )
                    time.sleep(self.RETRY_TIME)
                else:
                    break
            self._app_socket = app_socket

        self._logger.debug("Application socket opened")

    def _get_addr_info(self, name):
        app_net = self._get_app_net_config()
        remote_host = app_net.hostDict.get(name)
        if remote_host is None:
            raise ValueError(f"Host name '{name}' is not in the app network")
        return remote_host.addr

    def _get_app_net_config(self):
        network_config_file = simulaqron_settings.network_config_file
        app_net = SocketsConfig(network_config_file, network_name=self._network_name, config_type="app")
        return app_net

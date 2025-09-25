import pytest
from netqasm.runtime.application import default_app_instance

from simulaqron.run import run_applications
from simulaqron.sdk.socket import Socket


class TestClassicalSocket:
    @staticmethod
    def alice_program_sender():
        classical_socket: Socket = Socket("Alice", "Bob")
        classical_socket.send("ping")
        msg = classical_socket.recv()
        assert msg == "pong"

    @staticmethod
    def bob_program_receiver():
        classical_socket: Socket = Socket("Bob", "Alice")
        msg = classical_socket.recv()
        assert msg == "ping"
        classical_socket.send("pong")

    def test_classical_communication(self):
        apps = default_app_instance(
            [
                ("Alice", TestClassicalSocket.alice_program_sender),
                ("Bob", TestClassicalSocket.bob_program_receiver),
            ]
        )
        _ = run_applications(apps, use_app_config=False, enable_logging=False)

    def test_unknown_local(self):
        with pytest.raises(ValueError) as ex:
            # SimulaQron automatically decides that the node with a name
            # alphabetically before acts as the server.
            # In this case, we declare a local name not known by the (default)
            # network configuration, and try to connect to a known remote
            Socket("Alice-unknown", "Bob")
        assert ex.value.args[0] == "Host name 'Alice-unknown' is not in the app network"

    def test_unknown_remote(self):
        with pytest.raises(ValueError) as ex:
            # SimulaQron automatically decides that the node with a name
            # alphabetically before acts as the server.
            # In this case, we force to be in the "client" mode, by declaring
            # a local name *alphabetically after* the remote name, so the local
            # will try to connect to the unknown remote.
            Socket("Unknown", "Pedro")
        assert ex.value.args[0] == "Host name 'Pedro' is not in the app network"

    def test_connection_timeout(self):
        with pytest.raises(TimeoutError) as ex:
            Socket("Alice", "Bob", timeout=1)
        assert ex.value.args[0] == "timed out"

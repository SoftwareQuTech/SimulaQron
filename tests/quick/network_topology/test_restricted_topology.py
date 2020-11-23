import unittest
import logging
from functools import partial

from netqasm.logging.glob import set_log_level
from netqasm.sdk import EPRSocket
from netqasm.runtime.app_config import default_app_config

from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings
from simulaqron.sdk.connection import SimulaQronConnection
from simulaqron.run import run_applications


@unittest.skip("Restricted topology is not yet supported in the new version of simulaqron")
class TestRestrictedTopology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        simulaqron_settings.default_settings()
        simulaqron_settings._read_user = False
        simulaqron_settings.log_level = logging.CRITICAL
        nodes = ["Alice", "Bob", "Charlie"]
        cls.network = Network(nodes=nodes, topology="path", force=True)
        cls.network.start()

        cls.edges = [("Alice", "Bob"), ("Bob", "Charlie")]
        cls.non_edges = [(node, node) for node in nodes] + [("Alice", "Charlie")]

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def test_EPR(self):
        outcomes = []

        def create_func(name, remote_name):
            epr_socket = EPRSocket(remote_name)
            with SimulaQronConnection(name, epr_sockets=[epr_socket]):
                q = epr_socket.create()[0]
                m = q.measure()
                outcomes.append(m)

        def recv_func(name, remote_name):
            epr_socket = EPRSocket(remote_name)
            with SimulaQronConnection(name, epr_sockets=[epr_socket]):
                q = epr_socket.create()[0]
                m = q.measure()
                outcomes.append(m)

        for create_name, recv_name in self.edges:
            run_applications([
                default_app_config(create_name, partial(create_func, create_name, recv_name)),
                default_app_config(recv_name, partial(create_func, recv_name, create_name)),
            ], use_app_config=False)
            self.assertEqual(sum(outcomes) % 2, 0)
            return

        for sender_name, receiver_name in self.non_edges:
            with self.assertRaises(RuntimeError):  # TODO correct error
                run_applications([
                    default_app_config(create_name, partial(create_func, create_name, recv_name)),
                    default_app_config(recv_name, partial(create_func, recv_name, create_name)),
                ], use_app_config=False)


if __name__ == "__main__":
    set_log_level("DEBUG")
    unittest.main()

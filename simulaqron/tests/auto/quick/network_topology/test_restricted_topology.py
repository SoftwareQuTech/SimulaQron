import unittest
import logging

from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings
from cqc.pythonLib import CQCConnection, qubit, CQCUnsuppError


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

    def test_send(self):
        for sender_name, receiver_name in self.edges:
            with CQCConnection(sender_name) as sender:
                with CQCConnection(receiver_name) as receiver:
                    q = qubit(sender)
                    sender.sendQubit(q=q, name=receiver_name, remote_appID=receiver._appID)
                    q = receiver.recvQubit()
                    m = q.measure()
                    self.assertEqual(m, 0)
        for sender_name, receiver_name in self.non_edges:
            with CQCConnection(sender_name) as sender:
                with CQCConnection(receiver_name) as receiver:
                    q = qubit(sender)
                    with self.assertRaises(CQCUnsuppError):
                        sender.sendQubit(q=q, name=receiver_name, remote_appID=receiver._appID)
                    m = q.measure()
                    self.assertEqual(m, 0)

    def test_EPR(self):
        for sender_name, receiver_name in self.edges:
            with CQCConnection(sender_name) as sender:
                with CQCConnection(receiver_name) as receiver:
                    qs = sender.createEPR(name=receiver_name, remote_appID=receiver._appID)
                    qr = receiver.recvEPR()
                    ms = qs.measure()
                    mr = qr.measure()
                    self.assertEqual((ms + mr) % 2, 0)
        for sender_name, receiver_name in self.non_edges:
            with CQCConnection(sender_name) as sender:
                with CQCConnection(receiver_name) as receiver:
                    with self.assertRaises(CQCUnsuppError):
                        sender.createEPR(name=receiver_name, remote_appID=receiver._appID)


if __name__ == "__main__":
    unittest.main()

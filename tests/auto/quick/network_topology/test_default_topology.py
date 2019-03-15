import unittest

from simulaqron.network import Network
from simulaqron.settings import Settings
from cqc.pythonLib import CQCConnection, qubit, CQCUnsuppError


class TestDefaultTopology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Settings.default_settings()
        cls.node_names = ["Alice", "Bob", "Charlie"]
        cls.network = Network(cls.node_names)
        cls.network.start()
        print(cls.network.topology)
        print(Settings.CONF_TOPOLOGY_FILE)

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        Settings.default_settings()

    def test_send(self):
        for sender_name in self.node_names:
            for receiver_name in self.node_names:
                with CQCConnection(sender_name) as sender:
                    with CQCConnection(receiver_name) as receiver:
                        q = qubit(sender)
                        if sender_name == receiver_name:
                            with self.assertRaises(CQCUnsuppError):
                                sender.sendQubit(q=q, name=receiver_name, remote_appID=receiver._appID)
                        else:
                            sender.sendQubit(q=q, name=receiver_name, remote_appID=receiver._appID)
                            q = receiver.recvQubit()
                        m = q.measure()
                        self.assertEqual(m, 0)

    def test_EPR(self):
        for sender_name in self.node_names:
            for receiver_name in self.node_names:
                with CQCConnection(sender_name) as sender:
                    with CQCConnection(receiver_name) as receiver:
                        if sender_name == receiver_name:
                            with self.assertRaises(CQCUnsuppError):
                                sender.createEPR(name=receiver_name, remote_appID=receiver._appID)
                        else:
                            qs = sender.createEPR(name=receiver_name, remote_appID=receiver._appID)
                            qr = receiver.recvEPR()
                            ms = qs.measure()
                            mr = qr.measure()
                            self.assertEqual((ms + mr) % 2, 0)


if __name__ == "__main__":
    unittest.main()

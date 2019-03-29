import unittest
from cqc.pythonLib import CQCConnection, qubit, CQCNoQubitError
from simulaqron.settings import Settings
from simulaqron.network import Network


class TestContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Settings.default_settings()
        cls.network = Network(nodes=["Alice"])
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        Settings.default_settings()

    def setUp(self):
        self.cqcs = []

    def tearDown(self):
        for cqc in self.cqcs:
            cqc.close()

    def test_without_context(self):
        for _ in range(Settings.CONF_MAXQUBITS):
            cqc = CQCConnection("Alice")
            self.cqcs.append(cqc)
            qubit(cqc)
        with self.assertRaises(CQCNoQubitError):
            cqc = CQCConnection("Alice")
            self.cqcs.append(cqc)
            qubit(cqc)

    def test_with_context(self):
        for _ in range(Settings.CONF_MAXQUBITS):
            with CQCConnection("Alice") as cqc:
                qubit(cqc)
        with CQCConnection("Alice") as cqc:
            qubit(cqc)


if __name__ == "__main__":
    unittest.main()

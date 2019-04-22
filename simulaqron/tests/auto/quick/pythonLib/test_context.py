import unittest
import logging

from cqc.pythonLib import CQCConnection, qubit, CQCNoQubitError
from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network


class TestContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        simulaqron_settings.default_settings()
        simulaqron_settings._read_user = False
        simulaqron_settings.log_level = logging.CRITICAL
        cls.network = Network(nodes=["Alice"], force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def setUp(self):
        self.cqcs = []

    def tearDown(self):
        for cqc in self.cqcs:
            cqc.close()

    def test_without_context(self):
        for _ in range(simulaqron_settings.max_qubits):
            cqc = CQCConnection("Alice")
            self.cqcs.append(cqc)
            qubit(cqc)
        with self.assertRaises(CQCNoQubitError):
            cqc = CQCConnection("Alice")
            self.cqcs.append(cqc)
            qubit(cqc)

    def test_with_context(self):
        for _ in range(simulaqron_settings.max_qubits):
            with CQCConnection("Alice") as cqc:
                qubit(cqc)
        with CQCConnection("Alice") as cqc:
            qubit(cqc)


if __name__ == "__main__":
    unittest.main()

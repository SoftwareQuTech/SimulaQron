import unittest
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit, CQCNoQubitError
from SimulaQron.settings import Settings


class TestContext(unittest.TestCase):
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

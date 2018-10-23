import unittest
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit, CQCNoQubitError
from SimulaQron.settings import Settings

class TestContext(unittest.TestCase):
	def setUp(self):
		self.qubits = []
	def tearDown(self):
		for q in self.qubits:
			q.measure()

	def test_without_context(self):
		for _ in range(Settings.CONF_MAXQUBITS):
			cqc = CQCConnection("Alice")
			self.qubits.append(qubit(cqc))
		with self.assertRaises(CQCNoQubitError):
			cqc = CQCConnection("Alice")
			qubit(cqc)
		cqc.close()

	def test_with_context(self):
		for _ in range(Settings.CONF_MAXQUBITS):
			with CQCConnection("Alice") as cqc:
				qubit(cqc)
		with CQCConnection("Alice") as cqc:
			qubit(cqc)

if __name__ == '__main__':
	unittest.main()

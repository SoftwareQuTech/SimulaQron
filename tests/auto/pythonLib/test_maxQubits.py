import unittest
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit, CQCNoQubitError
from settings import Settings

class TestMaxQubit(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.alice = CQCConnection("Alice")
		cls.bob = CQCConnection("Bob")

	# def test_exact_max(self):
	# 	qubits = []
	# 	for _ in range(Settings.CONF_MAXQUBITS):
	# 		q = qubit(self.alice)
	# 		qubits.append(q)
	#
	# 	# Clean up
	# 	for q in qubits:
	# 		q.measure()
	#
	# def test_more_than_max(self):
	# 	qubits = []
	# 	for _ in range(Settings.CONF_MAXQUBITS):
	# 		q = qubit(self.alice)
	# 		qubits.append(q)
	#
	# 	with self.assertRaises(CQCNoQubitError):
	# 		q = qubit(self.alice)
	#
	# 	# Clean up
	# 	for q in qubits:
	# 		q.measure()

	def test_epr_for_last_position(self):
		qubits = []
		for _ in range(Settings.CONF_MAXQUBITS - 1):
			q = qubit(self.alice)
			qubits.append(q)
		for _ in range(Settings.CONF_MAXQUBITS - 1):
			q = qubit(self.bob)
			qubits.append(q)

		q = self.alice.createEPR("Bob", remote_appID=1)
		qubits.append(q)
		q = self.bob.recvEPR()
		qubits.append(q)

		with self.assertRaises(CQCNoQubitError):
			q = self.alice.createEPR("Bob", remote_appID=1)

		# remove one qubit from Alice
		m = qubits[0].measure()
		qubits.pop(0)
		print(m)

		with self.assertRaises(CQCNoQubitError):
			q = self.alice.createEPR("Bob", remote_appID=1)
		#
		# # remove one qubit from Bob
		# qubits[-1].measure()
		# qubits.pop(-1)
		#
		# q = self.alice.createEPR("Bob", remote_appID=1)
		# qubits.append(q)
		# q = self.bob.recvEPR()
		# qubits.append(q)

		# Clean up
		for q in qubits:
			q.measure()

if __name__ == '__main__':
	unittest.main()
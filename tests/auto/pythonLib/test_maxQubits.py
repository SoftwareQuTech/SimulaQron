import unittest
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit, CQCNoQubitError
from SimulaQron.settings import Settings

class TestMaxQubit(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.alice = CQCConnection("Alice")
		cls.bob = CQCConnection("Bob")

	@classmethod
	def tearDownClass(cls):
		cls.alice.close()
		cls.bob.close()

	def test_exact_max(self):
		with CQCConnection("Alice") as alice:
			for _ in range(Settings.CONF_MAXQUBITS):
				qubit(alice)

	def test_more_than_max(self):
		with CQCConnection("Alice") as alice:
			for _ in range(Settings.CONF_MAXQUBITS):
				qubit(alice)

			with self.assertRaises(CQCNoQubitError):
				qubit(alice)

	def test_send_for_last_position(self):
		with CQCConnection("Alice") as alice:
			with CQCConnection("Bob") as bob:
				alice_qubits = []
				bob_qubits = []
				for _ in range(Settings.CONF_MAXQUBITS):
					q = qubit(alice)
					alice_qubits.append(q)
				for _ in range(Settings.CONF_MAXQUBITS - 1):
					q = qubit(bob)
					bob_qubits.append(q)

				alice.sendQubit(alice_qubits[0], "Bob", remote_appID=bob._appID)
				q = bob.recvQubit()
				bob_qubits.append(q)

				with self.assertRaises(CQCNoQubitError):
					alice.sendQubit(alice_qubits[1], "Bob", remote_appID=bob._appID)

				# remove one qubit from Bob
				bob_qubits[0].measure()

				alice.sendQubit(alice_qubits[1], "Bob", remote_appID=bob._appID)
				bob.recvQubit()

	def test_epr_for_last_position(self):
		with CQCConnection("Alice") as alice:
			with CQCConnection("Bob") as bob:
				alice_qubits = []
				bob_qubits = []
				for _ in range(Settings.CONF_MAXQUBITS - 1):
					q = qubit(alice)
					alice_qubits.append(q)
				for _ in range(Settings.CONF_MAXQUBITS - 1):
					q = qubit(bob)
					bob_qubits.append(q)

				q = alice.createEPR("Bob", remote_appID=bob._appID)
				alice_qubits.append(q)
				q = bob.recvEPR()
				bob_qubits.append(q)

				with self.assertRaises(CQCNoQubitError):
					alice.createEPR("Bob", remote_appID=bob._appID)

				# remove one qubit from Alice
				alice_qubits[0].measure()

				with self.assertRaises(CQCNoQubitError):
					alice.createEPR("Bob", remote_appID=bob._appID)

				# remove one qubit from Bob
				bob_qubits[0].measure()

				alice.createEPR("Bob", remote_appID=bob._appID)
				bob.recvEPR()

if __name__ == '__main__':
	unittest.main()
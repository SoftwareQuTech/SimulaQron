import unittest
from SimulaQron.cqc.pythonLib.cqc import *

class TestDefaultTopology(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		alice = CQCConnection("Alice")
		bob = CQCConnection("Bob")
		charlie = CQCConnection("Charlie")
		cls.nodes = [alice, bob, charlie]

		print("Testing send and EPR in a fully connected topology")
	def test_send(self):
		for sender in self.nodes:
			for receiver in self.nodes:
				q = qubit(sender)
				if sender is receiver:
					with self.assertRaises(CQCUnsuppError):
						sender.sendQubit(q=q, name=receiver.name, remote_appID=receiver._appID)
				else:
					sender.sendQubit(q=q, name=receiver.name, remote_appID=receiver._appID)
					q = receiver.recvQubit()
				m = q.measure()
				self.assertEqual(m, 0)
	def test_EPR(self):
		for sender in self.nodes:
			for receiver in self.nodes:
				q = qubit(sender)
				if sender is receiver:
					with self.assertRaises(CQCUnsuppError):
						sender.createEPR(name=receiver.name, remote_appID=receiver._appID)
				else:
					qs = sender.createEPR(name=receiver.name, remote_appID=receiver._appID)
					qr = receiver.recvEPR()
					ms = qs.measure()
					mr = qr.measure()
					self.assertEqual((ms + mr) % 2, 0)

if __name__ == '__main__':
	unittest.main()
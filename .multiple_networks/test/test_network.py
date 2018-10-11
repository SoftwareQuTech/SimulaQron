from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
import sys
import os
import json
import unittest

class TestNetworks(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.top_path = os.environ['NETSIM'] + "/network_configs/topology.json"
		cls.networks_path = os.environ['NETSIM'] + "/network_configs/"
		cls.cqc_files = []
		for cqc_file in os.listdir(cls.networks_path):
			if cqc_file.endswith(".cfg"):
				cls.cqc_files.append(cls.networks_path + cqc_file)
		print(cls.cqc_files)

	@staticmethod
	def get_nodes(network_cqc_file):
		nodes = []
		with open(network_cqc_file) as cqcFile:
			for line in cqcFile:
				if not line.startswith('#'):
					words = line.split(',')
					node = words[0]
					nodes.append(node)
		return nodes

	@classmethod
	def get_edges(cls):
		with open(cls.top_path) as top_file:
			topology = json.load(top_file)
		edges = []
		while topology:
			nodeA, neighbors = topology.popitem()
			for nodeB in neighbors:
				edges.append((nodeA, nodeB))
				topology[nodeB].remove(nodeA)
		return edges

	def test_qubit_creation(self):
		for cqc_file in self.cqc_files:
			with self.subTest(cqc_file=cqc_file):
				nodes = self.get_nodes(cqc_file)
				# Test creating a qubit at each node
				for node in nodes:
					with CQCConnection(node, cqcFile=cqc_file) as cqc:
						qubit(cqc)
						self.assertEqual(len(cqc.active_qubits), 1)
					self.assertEqual(len(cqc.active_qubits), 0)

	def test_topology(self):
		pass


if __name__ == '__main__':
	unittest.main()

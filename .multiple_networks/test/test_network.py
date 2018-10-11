from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit, CQCUnsuppError
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
		for cqc_file in self.cqc_files:
			with self.subTest(cqc_file=cqc_file):
				network_name = cqc_file.split('/')[-1]
				topology = network_name.split('_')[1]
				nodes = self.get_nodes(cqc_file)
				if topology == "complete":
					for i in range(len(nodes)+1):
						if i == 0:
							with CQCConnection(nodes[0], cqcFile=cqc_file) as cqc:
								q = qubit(cqc)
								cqc.sendQubit(q, nodes[1])
						elif i == len(nodes):
							with CQCConnection(nodes[0], cqcFile=cqc_file) as cqc:
								cqc.recvQubit()
						else:
							with CQCConnection(nodes[i], cqcFile=cqc_file) as cqc:
								q = cqc.recvQubit()
								cqc.sendQubit(q, nodes[(i+1)%len(nodes)])
				elif topology == "topology":
					edges = self.get_edges()
					for edge in edges:
						with self.subTest(edge=edge):
							with CQCConnection(edge[0], cqcFile=cqc_file) as A:
								with CQCConnection(edge[1], cqcFile=cqc_file) as B:
									A.createEPR(B.name)
									B.recvEPR()

					# Find 5 non-edges
					n = len(nodes)
					non_edges = []
					for _ in range(int(n*(n-1)/2)):
						for nodeA in nodes:
							for nodeB in nodes:
								if (nodeA, nodeB) not in edges and (nodeB, nodeA) not in edges:
									non_edges.append((nodeA, nodeB))
									if len(non_edges) > 4:
										break
							if len(non_edges) > 4:
								break
						if len(non_edges) > 4:
							break
					else:
						raise RuntimeError("No non-edge")
					for non_edge in non_edges:
						with self.subTest(non_edge=non_edge):
							with CQCConnection(non_edge[0], cqcFile=cqc_file) as cqc:
								with self.assertRaises(CQCUnsuppError):
									cqc.createEPR(non_edge[1])
				else:
					raise RuntimeError()


if __name__ == '__main__':
	unittest.main()

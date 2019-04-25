import os
import json
import time
import unittest
from timeit import default_timer as timer

from simulaqron.toolbox import get_simulaqron_path
from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor
from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network


class TestInitNetwork(unittest.TestCase):
    def setUp(self):
        self.network = None
        self.default_nodes = ["Alice", "Bob", "Charlie", "David", "Eve"]
        self.default_topology = None

    def tearDown(self):
        self.check_nodes_and_topology(self.network)

    @classmethod
    def tearDownClass(cls):
        default_network_config_file = simulaqron_settings._default_config["network_config_file"]
        network_config = NetworksConfigConstructor(default_network_config_file)
        network_config.reset()
        network_config.write_to_file()
        simulaqron_settings.default_settings()

    def check_nodes_and_topology(self, network):
        simulaqron_path = get_simulaqron_path.main()
        network_config_file = os.path.join(simulaqron_path, "config", "network.json")
        with open(network_config_file, 'r') as f:
            network_config = json.load(f)
        nodes_in_file = list(network_config[network.name]["nodes"].keys())
        self.assertEqual(nodes_in_file, network.nodes)

        topology_in_file = network_config[network.name]["topology"]
        self.assertEqual(topology_in_file, network.topology)

    def test_init_no_argument(self):
        self.network = Network(force=True)
        self.assertEqual(self.network.nodes, self.default_nodes)
        self.assertEqual(self.network.topology, self.default_topology)

    def test_init_node_argument(self):
        nodes = ["Test3", "Test4"]
        self.network = Network(nodes=nodes, force=True)
        self.assertEqual(self.network.nodes, nodes)
        self.assertEqual(self.network.topology, self.default_topology)

    def test_init_topology_argument(self):
        topology = {"Test1": [], "Test2": [], "Test3": []}
        nodes = list(topology.keys())
        self.network = Network(topology=topology, force=True)
        self.assertEqual(self.network.nodes, nodes)
        self.assertEqual(self.network.topology, topology)

    def test_init_node_and_topology_argument(self):
        nodes = ["Test5", "Test6"]
        topology = {"Test5": ["Test6"], "Test6": ["Test5"]}
        self.network = Network(nodes=nodes, topology=topology, force=True)
        self.assertEqual(self.network.nodes, nodes)
        self.assertEqual(self.network.topology, topology)


class TestStartStopNetwork(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = ["Test1", "Test2", "Test3"]

    def test_start(self):
        network = Network(nodes=self.nodes, force=True)
        self.assertEqual(len(network.processes), 2 * len(self.nodes))
        for p in network.processes:
            self.assertFalse(p.is_alive())
        network.start()
        self.assertTrue(network.running)
        for p in network.processes:
            self.assertTrue(p.is_alive())

    def test_stop(self):
        network = Network(force=True)
        network.stop()
        for p in network.processes:
            self.assertFalse(p.is_alive())

    def test_start_stop(self):
        network = Network(force=True)
        network.start()
        for p in network.processes:
            self.assertTrue(p.is_alive())
        network.stop()
        for p in network.processes:
            self.assertFalse(p.is_alive())

    def test_no_wait(self):
        network = Network(nodes=self.nodes, force=True)
        network.start(wait_until_running=False)
        self.assertFalse(network.running)

        # Check that network starts running eventually
        max_time = 10  # s
        t_start = timer()
        while timer() < t_start + max_time:
            if network.running:
                break
            else:
                time.sleep(0.1)

        self.assertTrue(network.running)

    def test_del(self):
        network = Network(force=True)
        network.start()
        del network


if __name__ == '__main__':
    unittest.main()

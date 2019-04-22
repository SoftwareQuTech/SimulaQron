import os
import json
import time
import unittest
from timeit import default_timer as timer

from simulaqron.toolbox import get_simulaqron_path
from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor
from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network
from simulaqron.general.hostConfig import load_node_names


class TestInitNetwork(unittest.TestCase):
    def setUp(self):
        self.network = None

        # Set config files
        simulaqron_path = get_simulaqron_path.main()
        nodes_config_file = os.path.join(simulaqron_path, "config", "Nodes.cfg")
        with open(nodes_config_file, 'w') as f:
            self.nodes = ["Test1", "Test2", "Test3"]
            f.writelines([node + "\n" for node in self.nodes])
        topology_config_file = os.path.join(simulaqron_path, "config", "topology.json")
        with open(topology_config_file, 'w') as f:
            self.topology = {"Test1": ["Test2"], "Test2": ["Test3"], "Test3": []}
            json.dump(self.topology, f)
        simulaqron_settings.topology_file = os.path.join("config", "topology.json")
        # Settings.set_setting("BACKEND", "topology_file", "config/topology.json")

    def tearDown(self):
        self.check_nodes(self.network.nodes)
        self.check_topology(self.network.topology)

    @classmethod
    def tearDownClass(cls):
        # Set config files back to default
        for file in ["Nodes.cfg", "topology.json"]:
            simulaqron_path = get_simulaqron_path.main()
            file_path = os.path.join(simulaqron_path, "config", file)
            os.remove(file_path)

        default_network_config_file = simulaqron_settings._default_config["network_config_file"]
        network_config = NetworksConfigConstructor(default_network_config_file)
        network_config.reset()
        network_config.write_to_file()
        simulaqron_settings.default_settings()

    def check_nodes(self, nodes):
        simulaqron_path = get_simulaqron_path.main()
        nodes_config_file = os.path.join(simulaqron_path, "config", "Nodes.cfg")
        nodes_in_file = load_node_names(nodes_config_file)
        self.assertEqual(nodes_in_file, nodes)

    def check_topology(self, topology):
        simulaqron_path = get_simulaqron_path.main()
        topology_config_file = os.path.join(simulaqron_path, "config", "topology.json")
        with open(topology_config_file, 'r') as f:
            topology_in_file = json.load(f)
        self.assertEqual(topology_in_file, topology)

    def test_init_no_argument(self):
        self.network = Network()
        self.assertEqual(self.network.nodes, self.nodes)
        self.assertEqual(self.network.topology, self.topology)

    def test_init_node_argument(self):
        nodes = ["Test3", "Test4"]
        self.network = Network(nodes=nodes)
        self.assertEqual(self.network.nodes, nodes)
        self.assertEqual(self.network.topology, self.topology)

    def test_init_topology_argument(self):
        topology = {"Test1": [], "Test2": [], "Test3": []}
        self.network = Network(topology=topology)
        self.assertEqual(self.network.nodes, self.nodes)
        self.assertEqual(self.network.topology, topology)

    def test_init_node_and_topology_argument(self):
        nodes = ["Test5", "Test6"]
        topology = {"Test5": ["Test6"], "Test6": ["Test5"]}
        self.network = Network(nodes=nodes, topology=topology)
        self.assertEqual(self.network.nodes, nodes)
        self.assertEqual(self.network.topology, topology)


class TestStartStopNetwork(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = ["Test1", "Test2", "Test3"]

    def test_start(self):
        network = Network(nodes=self.nodes)
        self.assertEqual(len(network.processes), 2 * len(self.nodes))
        for p in network.processes:
            self.assertFalse(p.is_alive())
        network.start()
        self.assertTrue(network.running)
        for p in network.processes:
            self.assertTrue(p.is_alive())

    def test_stop(self):
        network = Network()
        network.stop()
        for p in network.processes:
            self.assertFalse(p.is_alive())

    def test_start_stop(self):
        network = Network()
        network.start()
        for p in network.processes:
            self.assertTrue(p.is_alive())
        network.stop()
        for p in network.processes:
            self.assertFalse(p.is_alive())

    def test_no_wait(self):
        network = Network(nodes=self.nodes)
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
        network = Network()
        network.start()
        del network


if __name__ == '__main__':
    unittest.main()

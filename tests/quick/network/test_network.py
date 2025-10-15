import json
import time
from tempfile import NamedTemporaryFile
from typing import List

import pytest
from timeit import default_timer as timer

from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network


class TestInitNetwork:
    def _assert_nodes(self, nodes1: List[str], nodes2: List[str]):
        assert set(nodes1) == set(nodes2)

    def _assert_topology(self, topology1, topology2):
        if topology1 is None:
            assert topology2 is None
            return
        assert len(topology1) == len(topology2)
        for key, neigh1 in topology1.items():
            assert key in topology2
            neigh2 = topology2[key]
            self._assert_nodes(neigh1, neigh2)

    def _check_nodes_and_topology_in_file(self, network: Network):
        network_config_file = simulaqron_settings.network_config_file
        with open(network_config_file, 'r') as f:
            network_config = json.load(f)
        nodes_in_file = list(network_config[network.name]["nodes"].keys())
        self._assert_nodes(nodes_in_file, network.nodes)

        topology_in_file = network_config[network.name]["topology"]
        self._assert_topology(topology_in_file, network.topology)

    @pytest.fixture(autouse=True)
    def network_file(self):
        with NamedTemporaryFile() as net_config_file:
            self.network = None
            self.default_nodes = ["Alice", "Bob", "Charlie", "David", "Eve"]
            self.default_topology = None
            yield net_config_file.name
            self._check_nodes_and_topology_in_file(self.network)

    def test_init_no_argument(self, network_file: str):
        self.network = Network(force=True, network_config_file=network_file)
        self._assert_nodes(self.network.nodes, self.default_nodes)
        self._assert_topology(self.network.topology, self.default_topology)

    def test_init_node_argument(self, network_file: str):
        nodes = ["Test3", "Test4"]
        self.network = Network(nodes=nodes, force=True, network_config_file=network_file)
        self._assert_nodes(self.network.nodes, nodes)
        self._assert_topology(self.network.topology, self.default_topology)

    def test_init_topology_argument(self, network_file: str):
        topology = {"Test1": [], "Test2": [], "Test3": []}
        nodes = list(topology.keys())
        self.network = Network(topology=topology, force=True, network_config_file=network_file)
        self._assert_nodes(self.network.nodes, nodes)
        self._assert_topology(self.network.topology, topology)

    def test_init_node_and_topology_argument(self, network_file: str):
        nodes = ["Test5", "Test6"]
        topology = {"Test5": ["Test6"], "Test6": ["Test5"]}
        self.network = Network(nodes=nodes, topology=topology, force=True, network_config_file=network_file)
        self._assert_nodes(self.network.nodes, nodes)
        self._assert_topology(self.network.topology, topology)


class TestStartStopNetwork:
    nodes = ["Test1", "Test2", "Test3"]

    def test_start(self):
        network = Network(nodes=self.nodes, force=True)
        assert len(network.processes) == 2 * len(self.nodes)
        for p in network.processes:
            assert p.is_alive() is False
        network.start(wait_until_running=True)
        assert network.running is True
        for p in network.processes:
            assert p.is_alive() is True

    def test_stop(self):
        network = Network(force=True)
        network.stop()
        for p in network.processes:
            assert p.is_alive() is False

    def test_start_stop(self):
        network = Network(force=True)
        network.start(wait_until_running=True)
        for p in network.processes:
            assert p.is_alive() is True
        network.stop()
        for p in network.processes:
            assert p.is_alive() is False

    def test_no_wait(self):
        network = Network(nodes=self.nodes, force=True)
        network.start(wait_until_running=False)
        assert network.running is False

        # Check that network starts running eventually
        max_time = 10  # s
        t_start = timer()
        while timer() < t_start + max_time:
            if network.running:
                break
            else:
                time.sleep(0.1)

        assert network.running is True

    def test_del(self):
        network = Network(force=True)
        network.start(wait_until_running=True)
        del network

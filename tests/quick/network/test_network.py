import time

import pytest
from timeit import default_timer as timer

from simulaqron.settings import simulaqron_settings, network_config, get_default_network_config_file
from simulaqron.network import Network


class TestStartStopNetwork:
    nodes = ["Alice", "Bob", "Charlie"]

    @pytest.fixture(autouse=True)
    def network_file(self):
        simulaqron_settings.default_settings()
        network_config.using_default_network()

    def test_start(self, network_file: str):
        network = Network(nodes=self.nodes, network_config_file=get_default_network_config_file(use_embedded=True))
        assert len(network.processes) == 2 * len(self.nodes)
        for p in network.processes:
            assert p.is_alive() is False
        network.start(wait_until_running=True)
        assert network.running is True
        for p in network.processes:
            assert p.is_alive() is True

    def test_stop(self):
        network = Network(nodes=self.nodes, network_config_file=get_default_network_config_file(use_embedded=True))
        network.stop()
        for p in network.processes:
            assert p.is_alive() is False

    def test_start_stop(self):
        network = Network(nodes=self.nodes, network_config_file=get_default_network_config_file(use_embedded=True))
        network.start(wait_until_running=True)
        for p in network.processes:
            assert p.is_alive() is True
        network.stop()
        for p in network.processes:
            assert p.is_alive() is False

    def test_no_wait(self):
        network = Network(nodes=self.nodes, network_config_file=get_default_network_config_file(use_embedded=True))
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
        network = Network(nodes=self.nodes, network_config_file=get_default_network_config_file(use_embedded=True))
        network.start(wait_until_running=True)
        del network

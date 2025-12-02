import time
from tempfile import NamedTemporaryFile

import pytest
from timeit import default_timer as timer

from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network
from simulaqron.settings.network_config import NetworkConfigBuilder


class TestStartStopNetwork:
    nodes = ["Alice", "Bob", "Charlie"]

    @pytest.fixture(autouse=True)
    def network_file(self):
        simulaqron_settings.default_settings()
        # We initialize a temporary file with the default network config
        network_builder = NetworkConfigBuilder()
        network_builder.using_default_network()
        with NamedTemporaryFile(mode="w", suffix=".json", delete_on_close=False) as net_config_file:
            # We also need to specify the location of the temporal file as the network config file
            network_builder.write_to_file(net_config_file.name)
            net_config_file.close()
            yield net_config_file.name

    def test_start(self, network_file: str):
        network = Network(nodes=self.nodes)
        assert len(network.processes) == 2 * len(self.nodes)
        for p in network.processes:
            assert p.is_alive() is False
        network.start(wait_until_running=True)
        assert network.running is True
        for p in network.processes:
            assert p.is_alive() is True

    def test_stop(self):
        network = Network(nodes=self.nodes)
        network.stop()
        for p in network.processes:
            assert p.is_alive() is False

    def test_start_stop(self):
        network = Network(nodes=self.nodes)
        network.start(wait_until_running=True)
        for p in network.processes:
            assert p.is_alive() is True
        network.stop()
        for p in network.processes:
            assert p.is_alive() is False

    def test_no_wait(self):
        network = Network(nodes=self.nodes)
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
        network = Network(nodes=self.nodes)
        network.start(wait_until_running=True)
        del network

import json
from typing import Tuple

import pytest
import shutil
from importlib import resources
from pathlib import Path
from tempfile import NamedTemporaryFile
from dataclasses_serialization.json import JSONSerializer

import simulaqron._default_config
from simulaqron.settings import network_config, NetworkConfigBuilder
from simulaqron.settings.network_config import DEFAULT_SIMULAQRON_NETWORK_FILENAME, NodeConfig

cwd_network = (Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()
home_network = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()

class TestNetworksSettings:
    @pytest.fixture
    def clean_settings(self):
        # Load the setting files in cwd and home, saved them in a temp file
        if cwd_network.is_file() and cwd_network.is_file():
            orig_cwd_network = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(cwd_network, orig_cwd_network.name)
            cwd_network.unlink()
        else:
            orig_cwd_network = None
        if home_network.is_file() and home_network.is_file():
            orig_home_network = NamedTemporaryFile(suffix=".json", mode="w", delete_on_close=False).__enter__()
            shutil.copyfile(home_network, orig_home_network.name)
            home_network.unlink()
        else:
            orig_home_network = None
        # Proceed with the test case
        yield
        # Restore the loaded files in the original locations
        if orig_cwd_network is not None:
            cwd_network.touch()
            shutil.copyfile(orig_cwd_network.name, cwd_network)
            orig_cwd_network.__exit__(None, None, None)
        if orig_home_network is not None:
            home_network.touch()
            shutil.copyfile(orig_home_network.name, home_network)
            orig_home_network.__exit__(None, None, None)

        files_to_check = [cwd_network, home_network]
        for file in files_to_check:
            if file.exists() and file.is_file():
                file.unlink()

    @pytest.fixture
    def reset_net_cfg(self):
        network_config.load_from_known_sources()

    @staticmethod
    def _check_node_config(node: NodeConfig) -> Tuple[bool, ...]:
        return (node.app_hostname == "localhost", 8000 <= node.app_port <= 9000,
                node.qnodeos_hostname == "localhost", 8000 <= node.qnodeos_port <= 9000,
                node.vnode_hostname == "localhost", 8000 <= node.vnode_port <= 9000,)

    def test_create_default_settings(self, clean_settings):
        # Load the "raw" default network
        default_network_path = Path(str(resources.files(simulaqron._default_config).joinpath("default_network.json")))

        expected_net_cfg_dict = json.loads(default_network_path.read_text())
        expected_net_cfg = JSONSerializer.deserialize(NetworkConfigBuilder, expected_net_cfg_dict)

        assert network_config == expected_net_cfg


    def test_add_node(self, reset_net_cfg):
        network_config.remove_all_networks()

        network_config.add_node("Alice")
        network_config.add_node("Bob")
        network_config.add_node("Charlie", network_name="test")

        # We expect 2 nodes, since Charlie belongs to network "test" and not "default"
        assert len(network_config.nodes) == 2
        assert len(network_config.get_nodes("test")) == 1

        assert network_config.nodes[0].name == "Alice"
        assert network_config.nodes[1].name == "Bob"
        assert network_config.get_nodes("test")[0].name == "Charlie"

        assert TestNetworksSettings._check_node_config(network_config.nodes[0])
        assert TestNetworksSettings._check_node_config(network_config.nodes[1])
        assert TestNetworksSettings._check_node_config(network_config.get_nodes("test")[0])

    def test_remove_node(self):
        network_config.remove_all_networks()

        network_config.add_node("Alice")
        network_config.add_node("Bob")
        network_config.add_node("Charlie", network_name="test")

        network_config.remove_node("Alice")

        # We expect 1 node, since Charlie belongs to network "test" and not "default"
        assert len(network_config.nodes) == 1
        assert len(network_config.get_nodes("test")) == 1

        assert network_config.nodes[0].name == "Bob"
        assert network_config.get_nodes("test")[0].name == "Charlie"

        assert TestNetworksSettings._check_node_config(network_config.nodes[0])
        assert TestNetworksSettings._check_node_config(network_config.get_nodes("test")[0])

        network_config.remove_node("Charlie", network_name="test")

        # We expect only 1 node, and 1 network, since network "test" is now empty
        assert len(network_config.nodes) == 1
        assert len(network_config.networks) == 1

        assert network_config.nodes[0].name == "Bob"

        assert TestNetworksSettings._check_node_config(network_config.nodes[0])

    def test_add_network(self):
        network_config.remove_all_networks()

        network_config.add_network("Alice", network_name="test")
        network_config.add_network(["Bob"], network_name="test-b")

        # We expect 1 node in each network since Charlie belongs to network "test" and not "default"
        with pytest.raises(ValueError) as err:
            len(network_config.nodes)
        assert str(err.value) == "default is not a network in this config"
        assert len(network_config.get_nodes("test")) == 1
        assert len(network_config.get_nodes("test-b")) == 1

        assert network_config.get_nodes("test")[0].name == "Alice"
        assert network_config.get_nodes("test-b")[0].name == "Bob"

        assert TestNetworksSettings._check_node_config(network_config.get_nodes("test")[0])
        assert TestNetworksSettings._check_node_config(network_config.get_nodes("test-b")[0])



    @pytest.mark.skip(reason="TODO - Implement this test")
    def test_remove_network(self):
        network_config.remove_all_networks()

        network_config.add_node("Alice")
        network_config.add_node("Bob")
        network_config.add_node("Charlie", network_name="test")

        network_config
        # TODO - Finish this test

    @pytest.mark.skip(reason="TODO - Implement this test")
    def test_serialize_network_config(self):
        network_config.remove_all_networks()

        network_config.add_node("Alice")
        network_config.add_node("Bob")

        with NamedTemporaryFile(mode="w", delete_on_close=False) as temp_file:
            network_config.write_to_file(temp_file.name)
            temp_file.close()

            network_config2 = NetworkConfigBuilder()
            network_config2.read_from_file(temp_file.name)
            dct2 = network_config2.to_dict()

            assert dct1 == dct2
            assert "Alice" in dct1["default"]["nodes"]
            assert "Bob" in dct1["default"]["nodes"]
            assert "Charlie" in dct1["test"]["nodes"]
        # TODO - Finish this test

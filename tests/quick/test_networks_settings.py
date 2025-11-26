import json
from typing import Tuple, List

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

        # Each node uses 3 sockets, so we expect 15 used socket pairs
        assert len(network_config.used_sockets) == 15

        assert network_config.nodes[0].name == "Alice"
        assert network_config.nodes[1].name == "Bob"
        assert network_config.nodes[2].name == "Charlie"
        assert network_config.nodes[3].name == "David"
        assert network_config.nodes[4].name == "Eve"

        for node in network_config.nodes:
            assert all(TestNetworksSettings._check_node_config(node))


    def test_add_node(self, reset_net_cfg):
        network_config.remove_all_networks()

        network_config.add_node("Alice")
        network_config.add_node("Bob")
        network_config.add_node("Charlie", network_name="test")

        # We expect 2 nodes, since Charlie belongs to network "test" and not "default"
        assert len(network_config.nodes) == 2
        assert len(network_config.get_nodes("test")) == 1

        # Each node uses 3 sockets, so we expect 9 used socket pairs
        assert len(network_config.used_sockets) == 9

        assert network_config.nodes[0].name == "Alice"
        assert network_config.nodes[1].name == "Bob"
        assert network_config.get_nodes("test")[0].name == "Charlie"

        for node in network_config.nodes:
            assert all(TestNetworksSettings._check_node_config(node))
        assert all(TestNetworksSettings._check_node_config(network_config.get_nodes("test")[0]))

    def test_remove_node(self, reset_net_cfg):
        network_config.remove_all_networks()

        network_config.add_node("Alice")
        network_config.add_node("Bob")
        network_config.add_node("Charlie", network_name="test")

        network_config.remove_node("Alice")

        # We expect 1 node, since Charlie belongs to network "test" and not "default"
        assert len(network_config.nodes) == 1
        assert len(network_config.get_nodes("test")) == 1

        # Each node uses 3 sockets, so we expect 6 used socket pairs
        assert len(network_config.used_sockets) == 6

        assert network_config.nodes[0].name == "Bob"
        assert network_config.get_nodes("test")[0].name == "Charlie"

        assert all(TestNetworksSettings._check_node_config(network_config.nodes[0]))
        assert all(TestNetworksSettings._check_node_config(network_config.get_nodes("test")[0]))

        network_config.remove_node("Charlie", network_name="test")

        # We expect only 1 node, and 1 network, since network "test" is now empty
        assert len(network_config.nodes) == 1
        assert len(network_config.networks) == 1

        assert network_config.nodes[0].name == "Bob"

        assert all(TestNetworksSettings._check_node_config(network_config.nodes[0]))

    def test_add_network(self, reset_net_cfg):
        network_config.remove_all_networks()

        network_config.add_network("Alice", network_name="test")
        network_config.add_network(["Bob"], network_name="test-b")

        # We expect that network "default" will not exist
        with pytest.raises(ValueError) as err:
            len(network_config.nodes)
        assert str(err.value) == "default is not a network in this config"

        # We expect 1 node in each network since Alice belongs to network "test" and Bob to "test-b"
        assert len(network_config.get_nodes("test")) == 1
        assert len(network_config.get_nodes("test-b")) == 1

        # Each node uses 3 sockets, so we expect 6 used socket pairs
        assert len(network_config.used_sockets) == 6

        assert network_config.get_nodes("test")[0].name == "Alice"
        assert network_config.get_nodes("test-b")[0].name == "Bob"

        assert all(TestNetworksSettings._check_node_config(network_config.get_nodes("test")[0]))
        assert all(TestNetworksSettings._check_node_config(network_config.get_nodes("test-b")[0]))

    def test_remove_network(self, reset_net_cfg):
        network_config.remove_all_networks()

        network_config.add_node("Alice")
        network_config.add_node("Bob")
        network_config.add_node("Charlie", network_name="test")

        network_config.remove_network("default")
        # We expect 1 node in each network since Alice belongs to network "test" and Bob to "test-b"
        assert len(network_config.get_nodes("test")) == 1

        # Each node uses 3 sockets, so we expect 3 used socket pairs
        assert len(network_config.used_sockets) == 3
        assert network_config.get_nodes("test")[0].name == "Charlie"
        assert all(TestNetworksSettings._check_node_config(network_config.get_nodes("test")[0]))

    @staticmethod
    def _build_expected_config(alice_ports: List[int], bob_ports: List[int]):
        return ("[\n"
                "    {\n"
                "        \"name\": \"default\"\n"
                "        \"nodes\": [\n"
                "            {\n"
                "                \"Alice\": {\n"
                "                    \"app_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {alice_ports[0]},\n"
                "                    ],\n"
                "                    \"qnodeos_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {alice_ports[1]},\n"
                "                    ],\n"
                "                    \"vnode_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {alice_ports[2]},\n"
                "                    ]\n"
                "            }\n"
                "        ],\n"
                "        \"topology\": null\n"
                "    },\n"
                "    {\n"
                "        \"name\": \"test\"\n"
                "        \"nodes\": [\n"
                "            {\n"
                "                \"Bob\": {\n"
                "                    \"app_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {bob_ports[0]},\n"
                "                    ],\n"
                "                    \"qnodeos_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {bob_ports[1]},\n"
                "                    ],\n"
                "                    \"vnode_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {bob_ports[2]},\n"
                "                    ]\n"
                "            }\n"
                "        ],\n"
                "        \"topology\": null\n"
                "    }\n"
                "]")

    def test_serialize_network_config(self, reset_net_cfg):
        network_config.remove_all_networks()

        network_config.add_node("Alice")
        network_config.add_node("Bob", network_name="test")

        alice_ports = [
            network_config.get_nodes(network_name="default")[0].app_port,
            network_config.get_nodes(network_name="default")[0].qnodeos_port,
            network_config.get_nodes(network_name="default")[0].vnode_port
        ]

        bob_ports = [
            network_config.get_nodes(network_name="test")[0].app_port,
            network_config.get_nodes(network_name="test")[0].qnodeos_port,
            network_config.get_nodes(network_name="test")[0].vnode_port
        ]

        expected_network_config = TestNetworksSettings._build_expected_config(alice_ports, bob_ports)

        with NamedTemporaryFile(mode="wt", delete_on_close=False) as temp_file:
            network_config.write_to_file(temp_file.name)
            temp_file.flush()

            serialized_content = Path(temp_file.name).read_text()
            assert serialized_content == expected_network_config

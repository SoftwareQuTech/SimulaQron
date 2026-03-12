import json
from typing import Tuple, List

import pytest
import shutil
from importlib import resources
from pathlib import Path
from tempfile import NamedTemporaryFile
from dataclasses_serialization.json import JSONSerializer

import simulaqron._default_config
from simulaqron.settings import network_config, NetworksConfiguration
from simulaqron.settings.network_config import DEFAULT_SIMULAQRON_NETWORK_FILENAME, NodeConfig

cwd_network = (Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()
home_network = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()


class TestNetworksSettings:
    @pytest.fixture
    def clean_settings(self):
        # Load the setting files in cwd and home, saved them in a temp file
        if cwd_network.is_file() and cwd_network.is_file():
            orig_cwd_network = NamedTemporaryFile(suffix=".json", mode="w", delete=False).__enter__()
            shutil.copyfile(cwd_network, orig_cwd_network.name)
            cwd_network.unlink()
        else:
            orig_cwd_network = None
        if home_network.is_file() and home_network.is_file():
            orig_home_network = NamedTemporaryFile(suffix=".json", mode="w", delete=False).__enter__()
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
            Path(orig_cwd_network.name).unlink()
        if orig_home_network is not None:
            home_network.touch()
            shutil.copyfile(orig_home_network.name, home_network)
            orig_home_network.__exit__(None, None, None)
            Path(orig_home_network.name).unlink()

        files_to_check = [cwd_network, home_network]
        for file in files_to_check:
            if file.exists() and file.is_file():
                file.unlink()

    @pytest.fixture
    def reset_net_cfg(self):
        network_config.read_from_known_sources()

    @staticmethod
    def _check_node_config(node: NodeConfig) -> Tuple[bool, ...]:
        return (node.app_hostname == "localhost", 8000 <= node.app_port <= 9000,
                node.qnodeos_hostname == "localhost", 8000 <= node.qnodeos_port <= 9000,
                node.vnode_hostname == "localhost", 8000 <= node.vnode_port <= 9000,)

    def test_create_default_settings(self, clean_settings):
        # Load the "raw" default network
        default_network_path = Path(str(resources.files(simulaqron._default_config).joinpath("default_network.json")))

        expected_net_cfg_dict = json.loads(default_network_path.read_text())
        expected_net_cfg = JSONSerializer.deserialize(NetworksConfiguration, expected_net_cfg_dict)

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
                "        \"name\": \"default\",\n"
                "        \"nodes\": [\n"
                "            {\n"
                "                \"Alice\": {\n"
                "                    \"app_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {alice_ports[0]}\n"
                "                    ],\n"
                "                    \"qnodeos_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {alice_ports[1]}\n"
                "                    ],\n"
                "                    \"vnode_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {alice_ports[2]}\n"
                "                    ]\n"
                "                }\n"
                "            }\n"
                "        ],\n"
                "        \"topology\": null\n"
                "    },\n"
                "    {\n"
                "        \"name\": \"test\",\n"
                "        \"nodes\": [\n"
                "            {\n"
                "                \"Bob\": {\n"
                "                    \"app_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {bob_ports[0]}\n"
                "                    ],\n"
                "                    \"qnodeos_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {bob_ports[1]}\n"
                "                    ],\n"
                "                    \"vnode_socket\": [\n"
                "                        \"localhost\",\n"
                f"                        {bob_ports[2]}\n"
                "                    ]\n"
                "                }\n"
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

        with NamedTemporaryFile(mode="wt", delete=False) as temp_file:
            network_config.write_to_file(temp_file.name)
            temp_file.flush()

            serialized_content = Path(temp_file.name).read_text()
            assert serialized_content == expected_network_config
            Path(temp_file.name).unlink()

    def test_deserialize_network_config(self, reset_net_cfg):
        raw_config = TestNetworksSettings._build_expected_config([8020, 8021, 8022], [8050, 8051, 8052])
        with NamedTemporaryFile(mode="wt", delete=False) as temp_file:
            temp_file.write(raw_config)
            temp_file.flush()

            network_config.read_from_file(temp_file.name)
            assert json.dumps(JSONSerializer.serialize(network_config), indent=4) == raw_config
            Path(temp_file.name).unlink()

    def test_load_old_json_format(self):
        this_file_folder = Path(__file__).parent
        old_json_config_path = this_file_folder / "resources" / "old_format.json"

        with NamedTemporaryFile(mode="wt", delete=False) as temp_file:
            # We copy the content of the resource into a temp file, so we don't
            # overwrite the resource for future test sessions
            shutil.copy(old_json_config_path, temp_file.name)

            # Read the file containing the old format
            network_config.read_from_file(temp_file.name)

            # Check that the file content was updated
            raw_converted = json.load(Path(temp_file.name).open())
            assert isinstance(raw_converted, list)

            assert len(network_config.networks) == 1
            assert "default" in network_config.networks
            assert len(network_config.nodes) == 2

            assert network_config.nodes[0].name == "Alice"
            assert network_config.nodes[0].app_hostname == "localhost"
            assert network_config.nodes[0].app_port == 8821
            assert network_config.nodes[0].qnodeos_hostname == "localhost"
            assert network_config.nodes[0].qnodeos_port == 8822
            assert network_config.nodes[0].vnode_hostname == "localhost"
            assert network_config.nodes[0].vnode_port == 8823

            assert network_config.nodes[1].name == "Bob"
            assert network_config.nodes[1].app_hostname == "localhost"
            assert network_config.nodes[1].app_port == 8831
            assert network_config.nodes[1].qnodeos_hostname == "localhost"
            assert network_config.nodes[1].qnodeos_port == 8832
            assert network_config.nodes[1].vnode_hostname == "localhost"
            assert network_config.nodes[1].vnode_port == 8833
            Path(temp_file.name).unlink()

from pathlib import Path
from tempfile import NamedTemporaryFile

from simulaqron.general.host_config import NetworksConfigConstructor, SocketsConfig


class TestNetworkConfig:
    def test_read_write(self):
        network_config = NetworksConfigConstructor(file_path=None)

        network_config.add_node("Alice")
        network_config.add_node("Bob")
        network_config.add_node("Charlie", network_name="test")

        dct1 = network_config.to_dict()
        with NamedTemporaryFile(mode="w", delete_on_close=False) as temp_file:
            network_config.write_to_file(temp_file.name)
            temp_file.close()

            network_config2 = NetworksConfigConstructor(file_path=temp_file.name)
            dct2 = network_config2.to_dict()

            assert dct1 == dct2
            assert "Alice" in dct1["default"]["nodes"]
            assert "Bob" in dct1["default"]["nodes"]
            assert "Charlie" in dct1["test"]["nodes"]


class TestSocketsConfig:
    def test_load_file(self):
        this_file_folder = Path(__file__).parent
        sockets_config_path = this_file_folder / "resources" /  "sockets.cfg"
        conf1 = SocketsConfig(str(sockets_config_path.resolve()))

        network_config_path = this_file_folder / "resources" / "network.json"
        conf2 = SocketsConfig(str(network_config_path.resolve()), config_type="qnodeos")

        for node_name, host in conf1.hostDict.items():
            assert host.port == conf2.hostDict[node_name].port
            assert host.hostname == conf2.hostDict[node_name].hostname

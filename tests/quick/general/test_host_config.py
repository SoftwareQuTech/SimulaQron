from pathlib import Path
from tempfile import NamedTemporaryFile

from simulaqron.general.host_config import NetworkConfigBuilder, SocketsConfig


# TODO - Move these test to the new test class
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

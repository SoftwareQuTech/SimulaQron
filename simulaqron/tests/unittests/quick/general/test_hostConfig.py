import unittest
import os

from simulaqron.general.hostConfig import NetworksConfigConstructor, socketsConfig

PATH_TO_HERE = os.path.abspath(os.path.dirname(__file__))


class TestNetworkConfig(unittest.TestCase):
    def test_read_write(self):
        network_config = NetworksConfigConstructor()

        network_config.add_node("Alice")
        network_config.add_node("Bob")
        network_config.add_node("Charlie", network_name="test")

        dct1 = network_config.to_dict()
        file_path = os.path.join(PATH_TO_HERE, "resources", "test.json")
        network_config.write_to_file(file_path)

        network_config2 = NetworksConfigConstructor(file_path=file_path)
        dct2 = network_config2.to_dict()

        self.assertEqual(dct1, dct2)
        self.assertIn("Alice", dct1["default"]["nodes"])
        self.assertIn("Bob", dct1["default"]["nodes"])
        self.assertIn("Charlie", dct1["test"]["nodes"])


class TestSocketsConfig(unittest.TestCase):
    def test_load_file(self):
        file_path1 = os.path.join(PATH_TO_HERE, "resources", "sockets.cfg")
        conf1 = socketsConfig(file_path1)

        file_path2 = os.path.join(PATH_TO_HERE, "resources", "network.json")
        conf2 = socketsConfig(file_path2, config_type="cqc")

        for node_name, host in conf1.hostDict.items():
            self.assertEqual(host.port, conf2.hostDict[node_name].port)
            self.assertEqual(host.hostname, conf2.hostDict[node_name].hostname)


if __name__ == '__main__':
    unittest.main()

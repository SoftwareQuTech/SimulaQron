import os
import json
from contextlib import closing
from socket import AF_INET, SOCK_STREAM, socket

from simulaqron.toolbox import get_simulaqron_path
from simulaqron.settings import simulaqron_settings


config_files = [simulaqron_settings.app_file, simulaqron_settings.cqc_file, simulaqron_settings.vnode_file]
node_config_file = simulaqron_settings.nodes_file
simulaqron_path = get_simulaqron_path.main()
config_folder = "config"
default_topology_file = os.path.join(simulaqron_path, config_folder, "topology.json")


class NetworksConfigConstructor:
    def __init__(self, file_path=None):
        self.networks = {}
        self.used_sockets = []
        self.file_path = file_path
        if self.file_path is not None:
            self.read_from_file()

    def add_node(self, node_name, network_name="default", app_hostname=None, cqc_hostname=None, vnode_hostname=None,
                 app_port=None, cqc_port=None, vnode_port=None, neighbors=None):
        if network_name is None:
            network_name = "default"
        socket_addresses = [(app_hostname, app_port), (cqc_hostname, cqc_port), (vnode_hostname, vnode_port)]
        for i, socket_address in enumerate(socket_addresses):
            hostname, port = socket_address
            if hostname is None:
                hostname = "localhost"
            if port is None:
                port = self._get_unused_port(hostname)
            else:
                free = self._check_port_available(hostname, port)
                if not free:
                    raise ValueError("Cannot add node {}, since socket address ({}, {}) is already in use."
                                     .format(node_name, hostname, port))
            socket_address = (hostname, port)
            self.used_sockets.append(socket_address)
            socket_addresses[i] = socket_address

        app_hostname, app_port = socket_addresses[0]
        cqc_hostname, cqc_port = socket_addresses[1]
        vnode_hostname, vnode_port = socket_addresses[2]
        if network_name in self.networks:
            self.networks[network_name].add_node(name=node_name, app_hostname=app_hostname, cqc_hostname=cqc_hostname,
                                                 vnode_hostname=vnode_hostname, app_port=app_port, cqc_port=cqc_port,
                                                 vnode_port=vnode_port, neighbors=neighbors)
        else:
            network = _NetworkConfig()
            network.add_node(name=node_name, app_hostname=app_hostname, cqc_hostname=cqc_hostname,
                             vnode_hostname=vnode_hostname, app_port=app_port, cqc_port=cqc_port,
                             vnode_port=vnode_port, neighbors=neighbors)
            self.networks[network_name] = network

    def remove_node(self, node_name, network_name="default"):
        if network_name is None:
            network_name = "default"
        if network_name in self.networks:
            nodes = self.networks[network_name].nodes
            nodes.pop(node_name, None)

    def reset(self):
        """
        Resets the current config (simulaqron_settings.network_config_file) to a single network ("default")
        with the nodes Alice, Bob, Charlie, David and Eve
        :return:
        """
        for network_name in list(self.networks.keys()):
            self.remove_network(network_name=network_name)
        node_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
        self.add_network(node_names=node_names)

    def add_network(self, node_names, network_name="default", topology=None):
        if network_name is None:
            network_name = "default"
        self.remove_network(network_name=network_name)
        for node_name in node_names:
            if topology is not None:
                neighbors = topology[node_name]
            else:
                neighbors = None
            self.add_node(node_name, network_name=network_name, neighbors=neighbors)

    def remove_network(self, network_name="default"):
        if network_name is None:
            network_name = "default"
        self.networks.pop(network_name, None)

    def get_nodes(self, network_name="default"):
        if network_name is None:
            network_name = "default"
        if network_name in self.networks:
            nodes = self.networks[network_name].nodes
            return list(nodes.values())
        else:
            raise ValueError("{} is not a network in this config".format(network_name))

    def get_node_names(self, network_name="default"):
        if network_name is None:
            network_name = "default"
        if network_name in self.networks:
            nodes = self.networks[network_name].nodes
            return list(nodes.keys())
        else:
            raise ValueError("{} is not a network in this config".format(network_name))

    def to_dict(self):
        """
        Constructs a dictionary with all the content that can be written to a json file
        :return:
        """
        return {network_name: network.to_dict() for network_name, network in self.networks.items()}

    def write_to_file(self, file_path=None):
        if file_path is None:
            file_path = self.file_path
        if file_path is None:
            raise ValueError("Since this networks config was not initialized with a file_path you need to specify one")

        dict = self.to_dict()
        with open(file_path, 'w') as f:
            json.dump(dict, f, indent=4)

    def read_from_file(self, file_path=None):
        if file_path is None:
            file_path = self.file_path
        if file_path is None:
            raise ValueError("Since this networks config was not initialized with a file_path you need to specify one")

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                dict = json.load(f)
        else:
            raise ValueError("No such file {}".format(file_path))

        for network_name, network_dict in dict.items():
            nodes_dict = network_dict["nodes"]
            topology = network_dict["topology"]
            network = _NetworkConfig()
            network.topology = topology

            for node_name, node_dict in nodes_dict.items():
                app_hostname, app_port = node_dict["app_socket"]
                cqc_hostname, cqc_port = node_dict["cqc_socket"]
                vnode_hostname, vnode_port = node_dict["vnode_socket"]
                for socket_address in [node_dict.values()]:
                    if socket_address not in self.used_sockets:
                        self.used_sockets.append(socket_address)
                node = _NodeConfig(name=node_name, app_hostname=app_hostname, cqc_hostname=cqc_hostname,
                                   vnode_hostname=vnode_hostname, app_port=app_port, cqc_port=cqc_port,
                                   vnode_port=vnode_port)
                network.nodes[node_name] = node
            self.networks[network_name] = network

    def _get_unused_port(self, hostname):
        """
        Returns an unused port in the interval 8000 to 9000, if such exists, otherwise returns None.
        :param hostname: str
            Hostname, e.g. localhost or 192.168.0.1
        :return: int or None
        """
        for port in range(8000, 9001):
            if self._check_port_available(hostname, port):
                return port

    def _check_port_available(self, hostname, port):
        """
        Checks if the given port is not already set in the config files or used by some other process.
        :param hostname: str
            Hostname, e.g. localhost or 192.168.0.1
        :param port: int
            The port number
        :return: bool
        """
        if (hostname, port) in self.used_sockets:
            return False

        return self._check_socket_is_free(hostname, port)

    @staticmethod
    def _check_socket_is_free(hostname, port):
        with closing(socket(AF_INET, SOCK_STREAM)) as sock:
            if sock.connect_ex((hostname, port)) == 0:
                return False  # Open

        return True  # Closed (available)


class _NetworkConfig:
    def __init__(self):
        self.topology = None
        self.nodes = {}

    def add_node(self, name, app_hostname, cqc_hostname, vnode_hostname, app_port, cqc_port, vnode_port, neighbors):
        if neighbors is not None:
            if self.topology is None:
                # Assume that whatever nodes were there before are fully connnected
                self.topology = {}
                node_names = self.nodes.keys()
                for node_name in node_names:
                    self.topology[node_name] = [neigh for neigh in node_names if not neigh == node_name]

            self.topology[name] = neighbors

        self.nodes[name] = _NodeConfig(name=name, app_hostname=app_hostname, cqc_hostname=cqc_hostname,
                                       vnode_hostname=vnode_hostname, app_port=app_port, cqc_port=cqc_port,
                                       vnode_port=vnode_port)

    def to_dict(self):
        nodes = {node_name: node.to_dict() for node_name, node in self.nodes.items()}
        return {"nodes": nodes, "topology": self.topology}


class _NodeConfig:
    def __init__(self, name, app_hostname, cqc_hostname, vnode_hostname, app_port, cqc_port, vnode_port):
        self.name = name
        self.app_hostname = app_hostname
        self.cqc_hostname = cqc_hostname
        self.vnode_hostname = vnode_hostname
        self.app_port = app_port
        self.cqc_port = cqc_port
        self.vnode_port = vnode_port

    def to_dict(self):
        return {
            "app_socket": [self.app_hostname, self.app_port],
            "cqc_socket": [self.cqc_hostname, self.cqc_port],
            "vnode_socket": [self.vnode_hostname, self.vnode_port]
        }

import json
import socket
from contextlib import closing
import socket
from importlib import resources
from os import PathLike
from pathlib import Path
from typing import Optional, Self, Dict, List, Tuple, Any

import simulaqron._default_config


class NodeConfig:
    def __init__(self, name: str, app_hostname: Optional[str], qnodeos_hostname: Optional[str],
                 vnode_hostname: Optional[str], app_port: Optional[int], qnodeos_port: Optional[int],
                 vnode_port: Optional[int]):
        """
        Used by _NetworkConfig to keep track of the config of a single node.
        """
        self.name = name
        self.app_hostname = app_hostname
        self.qnodeos_hostname = qnodeos_hostname
        self.vnode_hostname = vnode_hostname
        self.app_port = app_port
        self.qnodeos_port = qnodeos_port
        self.vnode_port = vnode_port

    def to_dict(self) -> Dict[str, List[str | int | None]]:
        """
        Constructs a dictionary with all the config of this node.
        :return: dict
        """
        return {
            "app_socket": [self.app_hostname, self.app_port],
            "qnodeos_socket": [self.qnodeos_hostname, self.qnodeos_port],
            "vnode_socket": [self.vnode_hostname, self.vnode_port]
        }


class NetworkConfig:
    def __init__(self):
        """
        Used by NetworksConfigConstructor to keep track of the config of a single network.
        """
        self.topology: Optional[Dict[str, List[str]]] = None
        self.nodes: Dict[str, NodeConfig] = {}

    def add_node(
        self, name: str, app_hostname: Optional[str] = None, qnodeos_hostname: Optional[str] = None,
        vnode_hostname: Optional[str] = None, app_port: Optional[int] = None, qnodeos_port: Optional[int] = None,
        vnode_port: Optional[int] = None, neighbors: Optional[List[str]] = None,
    ):
        """
        Adds a node with the given name to a network (default: "default").
        If hostnames are None they will default to 'localhost'.
        If the port numbers None, unused ones will be chosen between 8000 and 9000.
        If neighbors are specified a restricted topology can be constructed (default is fully connected).

        :param name: str
            Name of the node, e.g. Alice
        :param app_hostname: str or None
            Hostname, e.g. localhost (default) or 192.168.0.1
        :param qnodeos_hostname: str or None
            Hostname, e.g. localhost (default) or 192.168.0.1
        :param vnode_hostname: str or None
            Hostname, e.g. localhost (default) or 192.168.0.1
        :param app_port: int or None
            Port number for the application
        :param qnodeos_port: int or None
            Port number for the qnodeos server
        :param vnode_port: int or None
            Port number for the virtual node
        :param neighbors: (list of str) or None
            A list of neighbors, of this node.
            If None all current nodes in the network will be adjacent to the added node.
        :return: None
        """
        if neighbors is not None:
            if self.topology is None:
                # Assume that whatever nodes were there before are fully connected
                self.topology = {}
                node_names = self.nodes.keys()
                for node_name in node_names:
                    self.topology[node_name] = [neigh for neigh in node_names if not neigh == node_name]

            self.topology[name] = neighbors

        self.nodes[name] = NodeConfig(
            name=name,
            app_hostname=app_hostname,
            qnodeos_hostname=qnodeos_hostname,
            vnode_hostname=vnode_hostname,
            app_port=app_port,
            qnodeos_port=qnodeos_port,
            vnode_port=vnode_port,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Constructs a dictionary with all the config of this network.
        :return: dict
        """
        nodes = {node_name: node.to_dict() for node_name, node in self.nodes.items()}
        return {"nodes": nodes, "topology": self.topology}


class NetworkConfigBuilder:
    def __init__(self):
        """
        Used to construct the config file of networks.
        """
        self.networks: Dict[str, NetworkConfig] = {}
        self.used_sockets: List[Tuple[str, int]] = []

    @classmethod
    def using_default_network(cls) -> Self:
        default_network_path = resources.files(simulaqron._default_config).joinpath("default_network.json")
        new_builder = cls()
        new_builder.read_from_file(Path(str(default_network_path)))
        return new_builder

    def add_node(self, node_name: str , network_name: str ="default", app_hostname: Optional[str] = None,
                 qnodeos_hostname: Optional[str] = None, vnode_hostname: Optional[str] = None,
                 app_port: Optional[int] = None, qnodeos_port: Optional[int] = None,
                 vnode_port: Optional[int] = None, neighbors: List[str] = None):
        """
        Adds a node with the given name to a network (default: "default").
        If hostnames are None they will default to 'localhost'.
        If the port numbers None, unused ones will be chosen between 8000 and 9000.
        If neighbors are specified a restricted topology can be constructed (default is fully connected).

        :param node_name: str
            Name of the node, e.g. Alice
        :param network_name: str
            Name of the network (default: "default")
        :param app_hostname: str or None
            Hostname, e.g. localhost (default) or 192.168.0.1
        :param qnodeos_hostname: str or None
            Hostname, e.g. localhost (default) or 192.168.0.1
        :param vnode_hostname: str or None
            Hostname, e.g. localhost (default) or 192.168.0.1
        :param app_port: int or None
            Port number for the application
        :param qnodeos_port: int or None
            Port number for the qnodeos server
        :param vnode_port: int or None
            Port number for the virtual node
        :param neighbors: (list of str) or None
            A list of neighbors, of this node.
            If None all current nodes in the network will be adjacent to the added node.
        :return: None
        """
        socket_addresses = [(app_hostname, app_port), (qnodeos_hostname, qnodeos_port), (vnode_hostname, vnode_port)]
        for i, socket_address in enumerate(socket_addresses):
            hostname, port = socket_address
            if hostname is None:
                hostname = "localhost"
            if port is None:
                port = self._get_unused_port(hostname)
            else:
                free = self._check_port_available(hostname, port)
                if not free:
                    raise ValueError(f"Cannot add node {node_name}, since socket address "
                                     f"({hostname}, {port}) is already in use.")
            socket_address = (hostname, port)
            self.used_sockets.append(socket_address)
            socket_addresses[i] = socket_address

        app_hostname, app_port = socket_addresses[0]
        qnodeos_hostname, qnodeos_port = socket_addresses[1]
        vnode_hostname, vnode_port = socket_addresses[2]
        if network_name in self.networks:
            self.networks[network_name].add_node(
                name=node_name,
                app_hostname=app_hostname,
                qnodeos_hostname=qnodeos_hostname,
                vnode_hostname=vnode_hostname,
                app_port=app_port,
                qnodeos_port=qnodeos_port,
                vnode_port=vnode_port,
                neighbors=neighbors,
            )
        else:
            network = NetworkConfig()
            network.add_node(name=node_name, app_hostname=app_hostname, qnodeos_hostname=qnodeos_hostname,
                             vnode_hostname=vnode_hostname, app_port=app_port, qnodeos_port=qnodeos_port,
                             vnode_port=vnode_port, neighbors=neighbors)
            self.networks[network_name] = network

    def remove_node(self, node_name: str, network_name: str = "default"):
        """
        Removes a node from the network.

        :param node_name: str
            Name of the node, e.g. Alice
        :param network_name: str
            Name of the network (default: "default")
        """
        if network_name in self.networks:
            nodes = self.networks[network_name].nodes
            nodes.pop(node_name, None)

    def reset(self):
        """
        Resets the current object to a single network ("default")
        with the nodes Alice, Bob, Charlie, David and Eve.
        Note that this does not overwrite any config file but can be done
        by calling 'write_to_file'.
        :return:
        """
        for network_name in list(self.networks.keys()):
            self.remove_network(network_name=network_name)
        node_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
        self.add_network(node_names=node_names)

    def add_network(self, node_names: List[str], network_name: str = "default",
                    topology: Optional[Dict[str, List[str]]] = None):
        """
        Adds a new network to the config, with some specified nodes.

        :param node_names: list of str
            Name of the nodes, e.g. [Alice, Bob]
        :param network_name: str
            Name of the network (default: "default")
        :param topology: None or dict
            The topology of the network (optional) (default is fully connected)
        """
        self.remove_network(network_name=network_name)
        for node_name in node_names:
            if topology is not None:
                neighbors = topology[node_name]
            else:
                neighbors = None
            self.add_node(node_name, network_name=network_name, neighbors=neighbors)

    def remove_network(self, network_name: str = "default"):
        """
        Removes a network from the config.

        :param network_name: str
            Name of the network (default: "default")
        """
        self.networks.pop(network_name, None)

    def get_nodes(self, network_name: str = "default") -> List[NodeConfig]:
        """
        Returns the node-config objects (_NodeConfig) in a network.

        :param network_name: str
            Name of the network (default: "default")
        :return: list of _NodeConfig
        """
        if network_name in self.networks:
            nodes = self.networks[network_name].nodes
            return list(nodes.values())
        else:
            raise ValueError(f"{network_name} is not a network in this config")

    def get_node_names(self, network_name: str = "default"):
        """
        Returns the names of the nodes in a network.

        :param network_name: str
            Name of the network (default: "default")
        :return: list of str
        """
        if network_name in self.networks:
            nodes = self.networks[network_name].nodes
            return list(nodes.keys())
        else:
            raise ValueError(f"{network_name} is not a network in this config")

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Constructs a dictionary with all the content that can be written to a json file
        :return: dict
        """
        return {network_name: network.to_dict() for network_name, network in self.networks.items()}

    def write_to_file(self, file_path: PathLike | str):
        """
        Writes the content of this config to a file.

        :param file_path: str
            The path of the file to write the content to.
        """
        if file_path is None:
            raise ValueError("Since this networks config was not initialized with a file_path you need to specify one")

        dictionary = self.to_dict()
        with open(file_path, 'w') as f:
            json.dump(dictionary, f, indent=4)

    def read_from_file(self, file_path: PathLike | str):
        """
        Reads config from a file.

        :param file_path: None or str
            If a file_path was specified upon __init__ this will be used if file_path is None.
        """
        if file_path is None:
            raise ValueError("No path specified to read the network configuration")

        if Path(str(file_path)).exists():
            with open(file_path, 'r') as f:
                dictionary = json.load(f)
        else:
            raise ValueError(f"No such file {file_path}")

        for network_name, network_dict in dictionary.items():
            nodes_dict = network_dict["nodes"]
            topology = network_dict["topology"]
            network = NetworkConfig()
            network.topology = topology

            for node_name, node_dict in nodes_dict.items():
                app_hostname, app_port = node_dict["app_socket"]
                qnodeos_hostname, qnodeos_port = node_dict["qnodeos_socket"]
                vnode_hostname, vnode_port = node_dict["vnode_socket"]
                socket_addresses = [
                    (app_hostname, app_port),
                    (qnodeos_hostname, qnodeos_port),
                    (vnode_hostname, vnode_port),
                ]
                for socket_address in socket_addresses:
                    if socket_address not in self.used_sockets:
                        self.used_sockets.append(socket_address)
                node = NodeConfig(name=node_name, app_hostname=app_hostname, qnodeos_hostname=qnodeos_hostname,
                                  vnode_hostname=vnode_hostname, app_port=app_port, qnodeos_port=qnodeos_port,
                                  vnode_port=vnode_port)
                network.nodes[node_name] = node
            self.networks[network_name] = network

    def _get_unused_port(self, hostname: str) -> int:
        """
        Returns an unused port in the interval 8000 to 9000, if such exists, otherwise returns None.
        :param hostname: str
            Hostname, e.g. localhost or 192.168.0.1
        :return: int or None
        """
        for port in range(8000, 9001):
            if self._check_port_available(hostname, port):
                return port
        raise RuntimeError(f"No unused port in {hostname}")

    def _check_port_available(self, hostname: str, port: int) -> bool:
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

        return self._check_socket_is_free(port)

    @staticmethod
    def _check_socket_is_free(port: int) -> bool:
        """
        Checks if a given socket on localhost is in use.
        This is done by trying to open the port and check if it succeeds.
        :param port: int
            The port number
        """
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            address = ('localhost', port)
            try:
                sock.bind(address)
            except socket.error:
                return False
        return True

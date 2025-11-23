import json
import socket
from contextlib import closing
from dataclasses import dataclass, field
from importlib import resources
from os import PathLike
from pathlib import Path
from typing import Optional, Self, Dict, List, Tuple, Any
from dataclasses_serialization.json import JSONSerializer

import simulaqron._default_config


@dataclass
class NodeConfig:
    """
    Used by NetworkConfig to keep track of the config of a single node.
    """
    name: str
    app_port: int
    qnodeos_port: int
    vnode_port: int
    app_hostname: str = "localhost"
    qnodeos_hostname: str = "localhost"
    vnode_hostname: str = "localhost"


@dataclass
class NetworkConfig:
    """
    Used by NetworksConfigConstructor to keep track of the config of a single network.
    """

    name: str
    topology: Optional[Dict[str, List[str]]] = None
    nodes: Dict[str, NodeConfig] = field(default_factory=dict)

    def add_node(
            self, name: str,
            app_hostname: str, qnodeos_hostname: str, vnode_hostname: str,
            app_port: int, qnodeos_port: int, vnode_port: int,
            neighbors: Optional[List[str]] = None,
    ):
        """
        Adds a node with the given name to the network
        If hostnames are not given they will default to 'localhost'.
        If the port numbers None, unused ones will be chosen between 8000 and 9000.
        If neighbors are specified a restricted topology can be constructed (default is fully connected).

        :param name: str
            Name of the node, e.g. Alice
        :param app_hostname: str
            Hostname (e.g. localhost) or IP address (e.g. 192.168.0.1)
        :param qnodeos_hostname: str
            Hostname (e.g. localhost) or IP address (e.g. 192.168.0.1)
        :param vnode_hostname: str
            Hostname (e.g. localhost) or IP address (e.g. 192.168.0.1)
        :param app_port: int
            Port number for the application
        :param qnodeos_port: int
            Port number for the qnodeos server
        :param vnode_port: int
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

    def remove_node(self, node_name: str):
        self.nodes.pop(node_name, None)

@dataclass
class NetworkConfigBuilder:
    """
    Used to construct the config file of networks.
    """

    networks: Dict[str, NetworkConfig] = field(default_factory=dict)
    used_sockets: List[Tuple[str, int]] = field(default_factory=list)

    @classmethod
    def using_default_network(cls) -> Self:
        # We use the embedded default network here
        default_network_path = resources.files(simulaqron._default_config).joinpath("default_network.json")
        new_builder = cls()
        new_builder.read_from_file(Path(str(default_network_path)))
        return new_builder

    def _correct_network_port_if_needed(self, hostname: str, port: int) -> int:
        """
        Checks if the given port is valid (>0) and if it is free. If not, it will
        allocate a new port in the range 8000-9000 which is free, and hence can be used
        to listen to new connections
        Args:
            hostname: str
                The hostname to test the port on.
            port: int
                The port number to test if it is usable
        Returns:
            A port number which is guaranteed to be valid, and ready to be used
            to listen to connections on.
        """
        if port < -1:
            port = self._get_unused_port(hostname)
        if not self._check_port_available(hostname, port):
            raise ValueError(f"Socket address combination ({hostname}, {port}) is already in use.")
        return port

    def add_node(self, node_name: str, network_name: str = "default", app_hostname: str = "localhost",
                 qnodeos_hostname: str = "localhost", vnode_hostname: str = "localhost",
                 app_port: int = -1, qnodeos_port: int = -1,
                 vnode_port: int = -1, neighbors: Optional[List[str]] = None):
        """
        Adds a node with the given name to a network (default: "default").
        If hostnames are None they will default to 'localhost'.
        If the port numbers None, unused ones will be chosen between 8000 and 9000.
        If neighbors are specified a restricted topology can be constructed (default is fully connected).

        :param node_name: str
            Name of the node, e.g. Alice
        :param network_name: str
            Name of the network (default: "default")
        :param app_hostname: str
            Hostname, e.g. localhost (the default if not given) or 192.168.0.1
        :param qnodeos_hostname: str
            Hostname, e.g. localhost (the default if not given) or 192.168.0.1
        :param vnode_hostname: str
            Hostname, e.g. localhost (the default if not given) or 192.168.0.1
        :param app_port: int
            Port number for the application. A free port in the range 8000-9000 will be allocated if not given
        :param qnodeos_port: int
            Port number for the application. A free port in the range 8000-9000 will be allocated if not given
        :param vnode_port: int
            Port number for the application. A free port in the range 8000-9000 will be allocated if not given
        :param neighbors: (list of str) or None
            A list of neighbors, of this node.
            If None all current nodes in the network will be adjacent to the added node.
        :return: None
        """

        try:
            # Process app hostname/port
            app_port = self._correct_network_port_if_needed(app_hostname, app_port)
            self.used_sockets.append((app_hostname, app_port))

            # Process qnodeos hostname/port
            qnodeos_port = self._correct_network_port_if_needed(qnodeos_hostname, qnodeos_port)
            self.used_sockets.append((qnodeos_hostname, qnodeos_port))

            # Process qnodeos hostname/port
            vnode_port = self._correct_network_port_if_needed(vnode_hostname, vnode_port)
            self.used_sockets.append((vnode_hostname, vnode_port))
        except ValueError as e:
            raise ValueError(f"Cannot add node {node_name}", e)

        if network_name not in self.networks:
            # network doesn't exist, create a new one
            network = NetworkConfig(network_name)

        # At this point, we are sure that the network exists in self.networks
        network = self.networks[network_name]
        network.add_node(name=node_name,
                         app_hostname=app_hostname,
                         qnodeos_hostname=qnodeos_hostname,
                         vnode_hostname=vnode_hostname,
                         app_port=app_port,
                         qnodeos_port=qnodeos_port,
                         vnode_port=vnode_port,
                         neighbors=neighbors)

    def remove_node(self, node_name: str, network_name: str = "default"):
        """
        Removes a node from the network.

        :param node_name: str
            Name of the node to remove, e.g. Alice
        :param network_name: str
            Name of the network to delete the node from (default: "default")
        """
        if network_name in self.networks:
            self.networks[network_name].remove_node(node_name)
        else:
            raise ValueError(f"Unknown network name {network_name}")

    def reset(self):
        """
        Resets the current object to a single network ("default")
        with the nodes "Alice", "Bob", "Charlie", "David" and "Eve".
        """
        for network_name in self.networks.keys():
            self.remove_network(network_name=network_name)
        node_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
        self.add_network(node_names=node_names, network_name="default")

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

    def write_to_file(self, file_path: PathLike | str):
        """
        Writes the content of this config to a file.

        :param file_path: str
            The path of the file to write the content to.
        """
        if file_path is None:
            raise ValueError("Since this networks config was not initialized with a file_path you need to specify one")

        # Create the Path object
        file_path = Path(str(file_path)).resolve()

        # Create all the parent folder if they not exists
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)

        # Poke the file, so it exists before opening
        file_path.touch(exist_ok=True)

        with file_path.open('wt') as f:
            f.write(JSONSerializer.serialize(self))

    def read_from_file(self, file_path: PathLike | str):
        """
        Reads config from a file.

        :param file_path: None or str
            If a file_path was specified upon __init__ this will be used if file_path is None.
        """
        if file_path is None:
            raise ValueError("No path specified to read the network configuration")

        file_path = Path(str(file_path))

        if file_path.exists():
            with file_path.open('r') as f:
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

    # Helper properties and pythonic accessors
    @property
    def nodes(self) -> List[NodeConfig]:
        """
        Access the nodes of the default network held by this configuration.
        Returns:
            A list of NodeConfig objects.
        """
        return self.get_nodes(network_name="default")

    def __getattr__(self, item: str) -> NetworkConfig:
        if isinstance(item, str):
            return self.networks[item]
        else:
            raise ValueError(f"Item '{item}' cannot be matched to a network in this config.")

    # Helper functions
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

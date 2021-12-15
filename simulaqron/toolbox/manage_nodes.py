import os
import json
from contextlib import closing
import socket


class NetworksConfigConstructor:
    def __init__(self, file_path=None):
        """
        Used to construct the config file of networks.abs
        When all nodes and networks are added the content of this object can
        be written to a file by calling the method 'write_to_file'.

        :param file_path: None or str
            Path to the network config_file. If None an empty networkconfig constructor is initalized.
            Otherwise the content of the file is loaded.
        """
        self.networks = {}
        self.used_sockets = []
        self.file_path = file_path
        if self.file_path is not None:
            if os.path.exists(self.file_path):
                self.read_from_file()

    def add_node(self, node_name, network_name="default", app_hostname=None, qnodeos_hostname=None, vnode_hostname=None,
                 app_port=None, qnodeos_port=None, vnode_port=None, neighbors=None):
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
        if network_name is None:
            network_name = "default"
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
                    raise ValueError("Cannot add node {}, since socket address ({}, {}) is already in use."
                                     .format(node_name, hostname, port))
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
            network = _NetworkConfig()
            network.add_node(name=node_name, app_hostname=app_hostname, qnodeos_hostname=qnodeos_hostname,
                             vnode_hostname=vnode_hostname, app_port=app_port, qnodeos_port=qnodeos_port,
                             vnode_port=vnode_port, neighbors=neighbors)
            self.networks[network_name] = network

    def remove_node(self, node_name, network_name="default"):
        """
        Removes a node from the network.

        :param node_name: str
            Name of the node, e.g. Alice
        :param network_name: str
            Name of the network (default: "default")
        """
        if network_name is None:
            network_name = "default"
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

    def add_network(self, node_names, network_name="default", topology=None):
        """
        Adds a new network to the config, with some specified nodes.

        :param node_names: list of str
            Name of the nodes, e.g. [Alice, Bob]
        :param network_name: str
            Name of the network (default: "default")
        :param topology: None or dict
            The topology of the network (optional) (default is fully connected)
        """
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
        """
        Removes a network from the config.

        :param network_name: str
            Name of the network (default: "default")
        """
        if network_name is None:
            network_name = "default"
        self.networks.pop(network_name, None)

    def get_nodes(self, network_name="default"):
        """
        Returns the node-config objects (_NodeConfig) in a network.

        :param network_name: str
            Name of the network (default: "default")
        :return: list of _NodeConfig
        """
        if network_name is None:
            network_name = "default"
        if network_name in self.networks:
            nodes = self.networks[network_name].nodes
            return list(nodes.values())
        else:
            raise ValueError("{} is not a network in this config".format(network_name))

    def get_node_names(self, network_name="default"):
        """
        Returns the names of the nodes in a network.

        :param network_name: str
            Name of the network (default: "default")
        :return: list of str
        """
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
        :return: dict
        """
        return {network_name: network.to_dict() for network_name, network in self.networks.items()}

    def write_to_file(self, file_path=None):
        """
        Writes the content of this config to a file.

        :param file_path: None or str
            If a file_path was specified upon __init__ this will be used if file_path is None.
        """
        if file_path is None:
            file_path = self.file_path
        if file_path is None:
            raise ValueError("Since this networks config was not initialized with a file_path you need to specify one")

        dict = self.to_dict()
        with open(file_path, 'w') as f:
            json.dump(dict, f, indent=4)

    def read_from_file(self, file_path=None):
        """
        Reads config from a file.

        :param file_path: None or str
            If a file_path was specified upon __init__ this will be used if file_path is None.
        """
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
                node = _NodeConfig(name=node_name, app_hostname=app_hostname, qnodeos_hostname=qnodeos_hostname,
                                   vnode_hostname=vnode_hostname, app_port=app_port, qnodeos_port=qnodeos_port,
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

        return self._check_socket_is_free(port)

    @staticmethod
    def _check_socket_is_free(port):
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


class _NetworkConfig:
    def __init__(self):
        """
        Used by NetworksConfigConstructor to keep track of the config of a single network.
        """
        self.topology = None
        self.nodes = {}

    def add_node(
        self,
        name,
        app_hostname,
        qnodeos_hostname,
        vnode_hostname,
        app_port,
        qnodeos_port,
        vnode_port,
        neighbors,
    ):
        """
        Adds a node with the given name to a network (default: "default").
        If hostnames are None they will default to 'localhost'.
        If the port numbers None, unused ones will be chosen between 8000 and 9000.
        If neighbors are specified a restricted topology can be constructed (default is fully connected).

        :param node_name: str
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
                # Assume that whatever nodes were there before are fully connnected
                self.topology = {}
                node_names = self.nodes.keys()
                for node_name in node_names:
                    self.topology[node_name] = [neigh for neigh in node_names if not neigh == node_name]

            self.topology[name] = neighbors

        self.nodes[name] = _NodeConfig(
            name=name,
            app_hostname=app_hostname,
            qnodeos_hostname=qnodeos_hostname,
            vnode_hostname=vnode_hostname,
            app_port=app_port,
            qnodeos_port=qnodeos_port,
            vnode_port=vnode_port,
        )

    def to_dict(self):
        """
        Constructs a dictionary with all the config of this network.
        :return: dict
        """
        nodes = {node_name: node.to_dict() for node_name, node in self.nodes.items()}
        return {"nodes": nodes, "topology": self.topology}


class _NodeConfig:
    def __init__(self, name, app_hostname, qnodeos_hostname, vnode_hostname, app_port, qnodeos_port, vnode_port):
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

    def to_dict(self):
        """
        Constructs a dictionary with all the config of this node.
        :return: dict
        """
        return {
            "app_socket": [self.app_hostname, self.app_port],
            "qnodeos_socket": [self.qnodeos_hostname, self.qnodeos_port],
            "vnode_socket": [self.vnode_hostname, self.vnode_port]
        }

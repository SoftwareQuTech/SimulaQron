import os
import json
from contextlib import closing
from socket import AF_INET, SOCK_STREAM, socket
from configparser import ConfigParser
from cqc.settings import get_config, set_config

from simulaqron.toolbox import get_simulaqron_path
from simulaqron.general.hostConfig import load_node_names, networkConfig
from simulaqron.settings import Settings


config_files = [Settings.CONF_APP_FILE, Settings.CONF_CQC_FILE, Settings.CONF_VNODE_FILE]
node_config_file = Settings.CONF_NODES_FILE
simulaqron_path = get_simulaqron_path.main()
config_folder = "config"
default_topology_file = os.path.join(simulaqron_path, config_folder, "topology.json")


def add_node(name, hostname=None, app_port=None, cqc_port=None, vnode_port=None, neighbors=None):
    """
    Adds a node with the given name from the config files.
    If the port numbers a not specified, unused ones will be chosen between 8000 and 9000.

    :param name: str
        Name of the node, e.g. Alice
    :param hostname: str or None
        Hostname, e.g. localhost (default) or 192.168.0.1
    :param app_port: int or None
        Port number for the application
    :param cqc_port: int or None
        Port number for the cqc server
    :param vnode_port: int or None
        Port number for the virtual node
    :param neighbors: (list of str) or None
        A list of neighbors, of this node, if None all current nodes in the network will be adjacent to the added node.
    :return: None
    """
    if name in get_nodes():
        raise ValueError("Cannot add node {}, already in the network.".format(name))

    if hostname is None:
        hostname = "localhost"

    ports = [app_port, cqc_port, vnode_port]
    for config_file, port in zip(config_files, ports):
        if port is None:
            port = _get_unused_port(hostname)
        else:
            avail = _check_port_available(hostname, port)
            if not avail:
                raise ValueError("Cannot add node, since port {} is already in use.".format(port))

        with open(config_file, 'a') as f:
            f.write("{}, {}, {}\n".format(name, hostname, port))

    node_config_path = Settings.CONF_NODES_FILE
    with open(node_config_path, 'a') as f:
        f.write(name + "\n")

    # Update topology
    if Settings.CONF_TOPOLOGY_FILE == "":
        topology_file = default_topology_file
    else:
        topology_file = os.path.join(simulaqron_path, Settings.CONF_TOPOLOGY_FILE)
    with open(topology_file, 'r') as f:
        topology = json.load(f)

    if neighbors is None:
        neighbors = [node for node in get_nodes() if node != name]
    for node, node_neighbors in topology.items():
        if (node in neighbors) and (name not in node_neighbors):
            node_neighbors.append(name)
        if (node not in neighbors) and (name in node_neighbors):
            node_neighbors.remove(name)

    topology[name] = neighbors

    with open(topology_file, 'w') as f:
        json.dump(topology, f)


def _get_unused_port(hostname):
    """
    Returns an unused port in the interval 8000 to 9000, if such exists, otherwise returns None.
    :param hostname: str
        Hostname, e.g. localhost or 192.168.0.1
    :return: int or None
    """
    for port in range(8000, 9001):
        if _check_port_available(hostname, port):
            return port


def _check_port_available(hostname, port):
    """
    Checks if the given port is not already set in the config files or used by some other process.
    :param hostname: str
        Hostname, e.g. localhost or 192.168.0.1
    :param port: int
        The port number
    :return: bool
    """
    for config_file in config_files:
        network_config = networkConfig(config_file)
        for name, host in network_config.hostDict.items():
            if port == host.port:
                return False

    return _check_socket_is_free(hostname, port)


def _check_socket_is_free(hostname, port):
    with closing(socket(AF_INET, SOCK_STREAM)) as sock:
        if sock.connect_ex((hostname, port)) == 0:
            return False  # Open

    return True  # Closed (available)


def remove_node(name):
    """
    Removes the node with the given name from the config files.
    :param name: str
    :return: None
    """
    for file_path in config_files + [node_config_file]:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if name not in line:
                new_lines.append(line)

        with open(file_path, 'w') as f:
            f.writelines(new_lines)

    topology_file = Settings.CONF_TOPOLOGY_FILE
    if topology_file != "":
        topology_file_path = os.path.join(simulaqron_path, topology_file)
    else:
        topology_file_path = default_topology_file

    with open(topology_file_path, 'r') as f:
        topology = json.load(f)

    if name in topology:
        topology.pop(name)

    for node, neighbors in topology.items():
        if name in neighbors:
            neighbors.remove(name)

    with open(topology_file_path, 'w') as f:
        json.dump(topology, f)


def get_nodes():
    """
    Returns a list of the current nodes set in the config files.
    :return: list of str
    """
    nodes_config_file = Settings.CONF_NODES_FILE
    current_nodes = load_node_names(nodes_config_file)

    return current_nodes


def set_default_nodes():
    current_nodes = get_nodes()
    for node in current_nodes:
        remove_node(node)

    nodes = ["Alice", "Bob", "Charlie", "David", "Eve"]
    for node, hostname in zip(nodes, ["localhost"] * 5):
        add_node(node, hostname)

    topology = {}
    for node in nodes:
        topology[node] = [neighbor for neighbor in nodes if neighbor != node]

    with open(default_topology_file, 'w') as f:
        json.dump(topology, f)


def setup_cqc_files():
    """
    Sets up the settings of the cqc packages such that the python-library can find the paths to the files
    specifying the addresses and ports of the cqc nodes running.
    :return: None
    """
    config = get_config()
    changed = False
    if config['FILEPATHS']['cqc_file'] != Settings.CONF_CQC_FILE:
        config['FILEPATHS']['cqc_file'] = Settings.CONF_CQC_FILE
        changed = True
    if config['FILEPATHS']['app_file'] != Settings.CONF_APP_FILE:
        config['FILEPATHS']['app_file'] = Settings.CONF_APP_FILE
        changed = True
    if changed:
        set_config(config)

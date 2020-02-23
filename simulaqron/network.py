#
# Copyright (c) 2017, Stephanie Wehner and Axel Dahlberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import time
import random
import logging
import multiprocessing as mp
import networkx as nx
from timeit import default_timer as timer

from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor
from simulaqron.settings import simulaqron_settings
from simulaqron.run.startNode import main as start_node
from simulaqron.run.startCQC import main as start_cqc
from cqc.pythonLib import CQCConnection

#########################################################################################
# Network class, sets up (part of) a simulated network.                                 #
# The processes consisting of the network are killed when the object goes out of scope. #
#########################################################################################


class Network:
    def __init__(self, name=None, nodes=None, topology=None, network_config_file=None, force=False, new=True):
        """
        Used to spin up a simulated network.

        If new=True then a fresh network with only the specified nodes
        (or the default Alice, Bob, Charlie, David and Eve) are created and overwriting the current network with
        the same name in the network config file. Otherwise only the specified nodes are started without changing
        the config file. Note that if the nodes does not currently exists and new=False, an ValueError is raised.

        If force=False an input to confirm the overwriting is issued.

        :param name: None or str (defualts to "default")
        :param nodes: None or list of str
        :param topology: None or dict
        :param network_config_file: None or str (defaults to simulaqron_settings.network_config_file
        :param force: bool
        :param new: bool
        """
        self._running = False

        if name is None:
            self.name = "default"
        else:
            self.name = name

        if network_config_file is None:
            self._network_config_file = simulaqron_settings.network_config_file
        else:
            self._network_config_file = network_config_file

        networks_config = NetworksConfigConstructor(file_path=self._network_config_file)

        if new:
            if nodes is None:
                if isinstance(topology, dict):
                    self.nodes = list(topology.keys())
                else:
                    self.nodes = ["Alice", "Bob", "Charlie", "David", "Eve"]
            else:
                self.nodes = nodes
            self.topology = construct_topology_config(topology, self.nodes)
            if not force:
                answer = input("Do you want to add/replace the network {} in the file {}"
                               "with a network constisting of the nodes {}? (yes/no)"
                               .format(self.name, self._network_config_file, self.nodes))
                if answer not in ["yes", "y"]:
                    raise RuntimeError("User did not want to replace network in file")
            networks_config.add_network(node_names=self.nodes, network_name=self.name, topology=self.topology)
            networks_config.write_to_file(self._network_config_file)
        else:
            if topology is not None:
                raise ValueError("If new is False a topology cannot be used.")
            if self.name in networks_config.networks:
                node_names = networks_config.get_node_names(self.name)
                self.topology = networks_config.networks[self.name].topology
            else:
                raise ValueError("Network {} is not in the file {}\n"
                                 "If you wish to add this network to the file, use the"
                                 "--new flag.".format(self.name, self._network_config_file))
            if nodes is None:
                self.nodes = node_names
            else:
                self.nodes = nodes
                for node_name in self.nodes:
                    if node_name not in node_names:
                        raise ValueError("Node {} is not in the current network {} in the file {}\n"
                                         "If you wish to overwrite the current network in the file, use the"
                                         "--new flag.".format(node_name, self.name, self._network_config_file))

        self.processes = []
        self._setup_processes()

    @property
    def running(self):
        """
        Is the network up and running?
        """
        if self._running:
            return True
        for node in self.nodes:
            try:
                cqc = CQCConnection(node, retry_connection=False, network_name=self.name)
            except ConnectionRefusedError:
                self._running = False
                break
            except Exception as err:
                logging.exception("Got unexpected exception when trying to connect: {}".format(err))
                raise err
            else:
                cqc.close()
        else:
            self._running = True

        return self._running

    def __del__(self):
        self.stop()

    def _setup_processes(self):
        """
        Setup the processes forming the network, however they are not started yet.
        """
        mp.set_start_method("spawn", force=True)
        for node in self.nodes:
            process_virtual = mp.Process(
                target=start_node, args=(node, self.name), name="VirtNode {}".format(node)
            )
            process_cqc = mp.Process(
                target=start_cqc, args=(node, self.name), name="CQCNode {}".format(node)
            )
            self.processes += [process_virtual, process_cqc]

    def start(self, wait_until_running=True):
        """
        Starts the network.
        The boolean flag 'wait_until_running' can be used whether the call to this method should
        blog until the all processes are running and are connected or not.
        :param wait_until_running: bool
        """
        logging.info("Starting network with name {}".format(self.name))
        for p in self.processes:
            if not p.is_alive():
                logging.debug("Starting process {}".format(p.name))
                p.deamon = True
                p.start()

        if wait_until_running:
            max_time = 10  # s
            t_start = timer()
            while timer() < t_start + max_time:
                if self.running:
                    break
                else:
                    time.sleep(0.1)

    def stop(self):
        """
        Stops the network.
        """
        if not self._running:
            return

        self._running = False
        logging.info("Stopping network with name {}".format(self.name))
        for p in self.processes:
            while p.is_alive():
                time.sleep(0.1)
                try:
                    p.terminate()
                except Exception as err:
                    print("Could not terminate one of the processes in the network due to error: {}".format(err))


def construct_topology_config(topology, nodes):
    """
    Constructs a json file at config/topology.json, used to define the topology of the network.

    :param topology: str
        Should be one of the following: None, 'complete', 'ring', 'random_tree'.
    :param nodes: list of str
        List of the names of the nodes.
    :return: None
    """
    if topology is not None:
        if isinstance(topology, dict):
            return topology
        elif topology == "complete":
            adjacency_dct = {}
            for i, node in enumerate(nodes):
                adjacency_dct[node] = nodes[:i] + nodes[i + 1 :]

        elif topology == "ring":
            adjacency_dct = {}
            nn = len(nodes)
            for i, node in enumerate(nodes):
                adjacency_dct[node] = [nodes[(i - 1) % nn], nodes[(i + 1) % nn]]

        elif topology == "path":
            adjacency_dct = {}
            nn = len(nodes)
            for i, node in enumerate(nodes):
                if i == 0:
                    adjacency_dct[node] = [nodes[i + 1]]
                elif i == (nn - 1):
                    adjacency_dct[node] = [nodes[i - 1]]
                else:
                    adjacency_dct[node] = [nodes[(i - 1) % nn], nodes[(i + 1) % nn]]

        elif topology == "random_tree":
            adjacency_dct = get_random_tree(nodes)

        elif topology[:16] == "random_connected":
            try:
                nr_edges = int(topology[17:])
            except ValueError:
                raise ValueError(
                    "When specifying a random connected graph use the format 'random_connected_{nr_edges}',"
                    "where 'nr_edges' is the number of edges of the graph."
                )
            except IndexError:
                raise ValueError(
                    "When specifying a random connected graph use the format 'random_connected_{nr_edges}',"
                    "where 'nr_edges' is the number of edges of the graph."
                )
            adjacency_dct = get_random_connected(nodes, nr_edges)

        else:
            raise ValueError("Unknown topology name")
        return adjacency_dct
    else:
        return None


def get_random_tree(nodes):
    """
    Constructs a dictionary describing a random tree, with the name of the vertices are taken from the 'nodes'

    :param nodes: list of str
        Name of the nodes to be used
    :return: dct
        keys are the names of the nodes and values their neighbors
    """
    tree = nx.random_tree(len(nodes))

    # Construct mapping to relabel nodes
    mapping = {i: nodes[i] for i in range(len(nodes))}
    nx.relabel_nodes(G=tree, mapping=mapping, copy=False)

    # Get the dictionary from the graph
    adjacency_dct = nx.to_dict_of_lists(tree)

    return adjacency_dct


def get_random_connected(nodes, nr_edges):
    """
    Constructs a dictionary describing a random connected graph with a specified number of edges,
    with the name of the vertices are taken from the 'nodes'

    :param nodes: list of str
        Name of the nodes to be used
    :param nr_edges: int
        The number of edges that the graph should have.
    :return: dct
        keys are the names of the nodes and values their neighbors
    """
    nn = len(nodes)
    min_edges = nn - 1
    max_edges = nn * (nn - 1) / 2
    if (nr_edges < min_edges) or (nr_edges > max_edges):
        raise ValueError("Number of edges cannot be less than #vertices-1 or greater then #vertices * (#vertices-1)/2")

    G = nx.random_tree(nn)

    non_edges = list(nx.non_edges(G))

    for _ in range(min_edges, nr_edges):
        random_edge = random.choice(non_edges)
        G.add_edge(random_edge[0], random_edge[1])
        non_edges.remove(random_edge)

    # Construct mapping to relabel nodes
    mapping = {i: nodes[i] for i in range(len(nodes))}
    nx.relabel_nodes(G=G, mapping=mapping, copy=False)

    # Get the dictionary from the graph
    adjacency_dct = nx.to_dict_of_lists(G)

    return adjacency_dct

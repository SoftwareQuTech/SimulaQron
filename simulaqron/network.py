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

import random
import time
from timeit import default_timer as timer
from typing import List, Dict

import networkx as nx
from multiprocess.context import ForkProcess as Process
import logging
from pathlib import Path

from simulaqron.settings import network_config
from simulaqron.settings.network_config import NodeConfig
from simulaqron.settings import simulaqron_settings
from simulaqron.start import start_vnode, start_qnodeos
# WARNING - this import *needs* to be after importing start_vnode and start_qnodeos
# Otherwise the code that patches some netqasm internal definitions will not work correctly!
from simulaqron.sdk import SimulaQronConnection


#########################################################################################
# Network class, sets up (part of) a simulated network.                                 #
# The processes consisting of the network are killed when the object goes out of scope. #
#########################################################################################


class Network:
    def __init__(self, nodes: List[str], network_config_file: Path, network_name: str = "default"):
        """
        Used to spin up a simulated network.
        This class uses the network configuration loaded in the global network_config object and
        starts the nodes mentioned in the constructor of this class.

        :param nodes: A list of strings with the node names to start.
        :type nodes: List[str]
        :param network_config_file: Path to network config file (required).
        :type network_config_file: str
        :param network_name: The name of network to start. Defaults to "default".
        :type network_name: str
        """

        self._network_config_file = network_config_file

        self._running = False
        self.name = network_name

        self.processes: List[Process] = []
        self._logger = logging.getLogger(f"{self.__class__.__name__}({self.name})")

        # Determine the nodes to start, using the in-memory network config
        self._nodes_to_start: List[NodeConfig] = []
        for node in network_config.get_nodes(network_name):
            if node.name in nodes:
                self._nodes_to_start.append(node)

        self._setup_processes()

    @property
    def running(self) -> bool:
        """
        Checks whether the network up and running.

        :return: True if the network up and running. False otherwise
        :rtype: bool
        """
        if self._running:
            return True
        for node in self._nodes_to_start:
            try:
                SimulaQronConnection.try_connection(
                    name=node.name,
                    network_name=self.name,
                )
            except ConnectionRefusedError:
                self._running = False
                break
            except Exception as err:
                self._logger.exception("Got unexpected exception when trying to connect: %s", err)
                raise err
        else:
            self._logger.debug("Network %s is now running", self.name)
            self._running = True

        return self._running

    def __del__(self):
        self.stop()

    def _setup_processes(self):
        """
        Setup the processes forming the network, however they are not started yet.

        This method creates the following *heavy processes* (either by forking or spawning):
        * One for SimulaQron's Virtual Node.
        * One for QNodeOS's (NetQASM interpreter) server.
        """
        for node in self._nodes_to_start:
            process_virtual = Process(
                target=start_vnode, 
                args=(node.name, self._network_config_file, self.name, simulaqron_settings.log_level),
                name=f"VirtNode {node.name}"
            )
            process_qnodeos = Process(
                target=start_qnodeos, 
                args=(node.name, self._network_config_file, self.name, simulaqron_settings.log_level),
                name=f"QnodeOSNode {node.name}"
            )
            self.processes += [process_virtual, process_qnodeos]

    def start(self, wait_until_running=False):
        """
        Starts the network.
        The boolean flag 'wait_until_running' can be used whether the call to this method should
        blog until the all processes are running and are connected or not.
        :param wait_until_running: bool
        """
        self._logger.info("Starting network with name %s", self.name)
        for p in self.processes:
            if not p.is_alive():
                self._logger.debug("Starting process %s", p.name)
                p.daemon = True
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
        self._running = False
        self._logger.info("Stopping network with name %s", self.name)
        for p in self.processes:
            if p.is_alive():
                try:
                    p.terminate()
                    p.join(timeout=5)
                    if p.is_alive():
                        # Process ignored SIGTERM — force-kill it so we never hang here
                        self._logger.warning("Process %s did not stop after SIGTERM, killing it", p.name)
                        p.kill()
                except Exception as err:
                    self._logger.warning("Could not terminate one of the processes in the"
                                         "network due to error: %s", err)

    def __str__(self):
        return f"Network '{self.name}', procs: {self.processes}"


# Helper functions to build topologies

def construct_topology_config(topology: str | Dict | None, nodes: List[str]) -> Dict[str, List[str]]:
    """
    Constructs a dictionary that maps the node names with their neighbours, representing a network topology.

    :param topology: The type of topology to generate. Should be one of the following: None, 'complete',
                     'ring', 'random_tree'.
    :type topology: str | Dict
    :param nodes: List of the names of the nodes.
    :type nodes: List[str]
    :return: A dictionary where keys are the names of the nodes and values are a list of strings of their neighbors
    :rtype: Dict[str, List[str]]
    """
    if isinstance(topology, str):
        # Trick to get the integer after "random_connected": split on that string
        topology = topology.split("random_connected")

    adjacency_dct = {}
    match topology:
        case dict() | None:
            return topology
        case ["complete"]:
            for i, node in enumerate(nodes):
                adjacency_dct[node] = nodes[:i] + nodes[i + 1:]
        case ["ring"]:
            nn = len(nodes)
            for i, node in enumerate(nodes):
                adjacency_dct[node] = [nodes[(i - 1) % nn], nodes[(i + 1) % nn]]
        case ["path"]:
            nn = len(nodes)
            for i, node in enumerate(nodes):
                if i == 0:
                    adjacency_dct[node] = [nodes[i + 1]]
                elif i == (nn - 1):
                    adjacency_dct[node] = [nodes[i - 1]]
                else:
                    adjacency_dct[node] = [nodes[(i - 1) % nn], nodes[(i + 1) % nn]]
        case ["random_tree"]:
            adjacency_dct = get_random_tree(nodes)
        case ["", raw_nr_edges]:
            # Here the "randon_connected" matches, and we also get the raw # of edges
            try:
                nr_edges = int(raw_nr_edges)
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
        case _:
            raise ValueError("Unknown topology name")
    return adjacency_dct


def get_random_tree(nodes: List[str]) -> Dict[str, List[str]]:
    """
    Constructs a dictionary describing a random tree, with the name of the vertices are taken from the 'nodes'

    :param nodes: Name of the nodes to be used
    :type nodes: List[str]
    :return: A dictionary where keys are the names of the nodes and values are a list of strings of their neighbors
    :rtype: Dict[str, List[str]]
    """
    tree = nx.random_tree(len(nodes))

    # Construct mapping to relabel nodes
    mapping = {i: nodes[i] for i in range(len(nodes))}
    nx.relabel_nodes(G=tree, mapping=mapping, copy=False)

    # Get the dictionary from the graph
    adjacency_dct = nx.to_dict_of_lists(tree)

    return adjacency_dct


def get_random_connected(nodes: List[str], nr_edges: int) -> Dict[str, List[str]]:
    """
    Constructs a dictionary describing a random connected graph with a specified number of edges,
    with the name of the vertices are taken from the 'nodes'

    :param nodes: Name of the nodes to be used
    :type nodes: List[str]
    :param nr_edges: The number of edges that the graph should have.
    :type nr_edges: int
    :return: A dictionary where keys are the names of the nodes and values are a list of strings of their neighbors
    :rtype: Dict[str, List[str]]
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

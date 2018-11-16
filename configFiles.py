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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# INFO:
# This file can be used to configure the nodes used in the simulation of SimulaQron.
# To setup a network with the nodes Alice, Bob and Charlie, simply type:
# 	'python configFiles.py --nodes "Alice Bob Charlie"'
# If you simply want a network with 10 nodes you can type:
# 'python configFiles.py --nrnodes 10
# Node names will then be 'Node0' until 'Node9'.
# If you want a specific topology you can also add:
# 'python configFiles.py --nrnodes 10 --topology "ring".
# This will make changes to the files 'config/{virtual,cqc,app}Nodes.cfg' and 'config/topology.json'.
# Port numbers will start at 8801 and depend on the number of nodes used.

import os
import json
import random
from argparse import ArgumentParser
import networkx as nx
import matplotlib.pyplot as plt

from SimulaQron.settings import Settings


def construct_node_configs(nodes):
    """
    Constructs the config files for the nodes and their port numbers.
    Port number used will start from 8801 and end at '8801 + 3*len(nodes)'.
    :param nodes: list of str
        List of the names of the nodes.
    :return: None
    """
    nrNodes = len(nodes)
    if nrNodes == 0:
        return

    # Get path from environment variable
    netsim_path = os.environ["NETSIM"] + "/"

    # Get path to configuration files
    conf_files = [
        netsim_path + "config/virtualNodes.cfg",
        netsim_path + "config/cqcNodes.cfg",
        netsim_path + "config/appNodes.cfg",
    ]

    # File for just a simple list of the nodes
    node_file = netsim_path + "config/Nodes.cfg"
    # What port numbers to start with
    start_nr = [8801, 8801 + nrNodes, 8801 + 2 * nrNodes]

    # Start of the configuration files
    conf_top = [
        "# Network configuration file",
        "#",
        "# For each host its informal name, as well as its location in the network must",
        "# be listed.",
        "#",
        "# [name], [hostname], [port number]",
        "#",
    ]

    # Write to the configuration files
    for i in range(len(conf_files)):
        with open(conf_files[i], "w") as f:
            for line in conf_top:
                f.write(line + "\n")
            for j in range(nrNodes):
                f.write("{}, localhost, {}\n".format(nodes[j], start_nr[i] + j))

    with open(node_file, "w") as f:
        for j in range(nrNodes):
            f.write("{}\n".format(nodes[j]))


def construct_topology_config(topology, nodes, save_fig=True):
    """
    Constructs a json file at $NETSIM/config/topology.json, used to define the topology of the network.
    :param topology: str
        Should be one of the following: None, 'complete', 'ring', 'random_tree'.
    :param nodes: list of str
        List of the names of the nodes.
    :param save_fig: bool
        Whether to save a picture of the network
    :return: None
    """
    if topology:
        if topology == "complete":
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

        if save_fig:
            network = nx.from_dict_of_lists(adjacency_dct)
            nx.draw(network, with_labels=True)
            plt.savefig(os.environ["NETSIM"] + "/config/topology.png")

        topology_file = os.environ["NETSIM"] + "/config/topology.json"
        with open(topology_file, "w") as top_file:
            json.dump(adjacency_dct, top_file)

        Settings.set_setting("BACKEND", "topology_file", "config/topology.json")
    else:
        Settings.set_setting("BACKEND", "topology_file", "")


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


def set_settings(settings):
    for section, section_settings in settings.items():
        for key, value in section_settings.items():
            Settings.set_setting(section=section, key=key, value=value)


def parse_input():
    # Get inputs from terminal
    parser = ArgumentParser()
    parser.add_argument(
        "--nrnodes", required=False, type=str, default=None, help="Number of nodes to use in the network."
    )
    parser.add_argument(
        "--topology",
        required=False,
        type=str,
        default=None,
        help="Which topology to use, if None it will be fully connected.",
    )
    parser.add_argument("--nodes", required=False, type=str, default=None, help="Node names to be used in the network")
    parser.add_argument("--maxqubits_per_node", required=False, type=str, default="")
    parser.add_argument("--maxregisters_per_node", required=False, type=str, default="")
    parser.add_argument("--waittime", required=False, type=str, default="")
    parser.add_argument("--backend_loglevel", required=False, type=str, default="")
    parser.add_argument("--backendhandler", required=False, type=str, default="")
    parser.add_argument("--backend", required=False, type=str, default="")
    parser.add_argument("--topology_file", required=False, type=str, default="")
    parser.add_argument("--noisy_qubits", required=False, type=str, default="")
    parser.add_argument("--t1", required=False, type=str, default="")
    parser.add_argument("--frontend_loglevel", required=False, type=str, default="")
    args = parser.parse_args()

    # Get the pre set node names
    if args.nodes:
        nodes = args.nodes.split(" ")
    else:
        nodes = []

    if args.nrnodes:
        nrNodes = int(args.nrnodes)

        # Check if there 'nrnodes' is greater then the number of pre-set nodes
        # If so, add more of the form 'node{int}'.
        node_number = 0
        while len(nodes) < nrNodes:
            node_name = "Node{}".format(node_number)
            if node_name not in nodes:
                nodes.append(node_name)
                node_number += 1
            else:
                # This node name was already added, try another one
                node_number += 1

    topology = args.topology

    settings = {"BACKEND": {}, "FRONTEND": {}}

    if len(args.maxqubits_per_node) > 0:
        settings["BACKEND"]["maxqubits_per_node"] = args.maxqubits_per_node
    if len(args.maxregisters_per_node) > 0:
        settings["BACKEND"]["maxregisters_per_node"] = args.maxregisters_per_node
    if len(args.waittime) > 0:
        settings["BACKEND"]["waittime"] = args.waittime
    if len(args.backend_loglevel) > 0:
        settings["BACKEND"]["loglevel"] = args.backend_loglevel
    if len(args.backendhandler) > 0:
        settings["BACKEND"]["backendhandler"] = args.backendhandler
    if len(args.backend) > 0:
        settings["BACKEND"]["backend"] = args.backend
    if len(args.topology_file) > 0:
        settings["BACKEND"]["topology_file"] = args.topology_file
    if len(args.noisy_qubits) > 0:
        settings["BACKEND"]["noisy_qubits"] = args.noisy_qubits
    if len(args.t1) > 0:
        settings["BACKEND"]["t1"] = args.t1
    if len(args.frontend_loglevel) > 0:
        settings["FRONTEND"]["loglevel"] = args.frontend_loglevel

    return nodes, topology, settings


if __name__ == "__main__":
    nodes, topology, settings = parse_input()
    construct_node_configs(nodes=nodes)
    construct_topology_config(topology=topology, nodes=nodes)
    set_settings(settings)

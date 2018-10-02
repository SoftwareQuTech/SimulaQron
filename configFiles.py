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
#	'python configFiles.py --nrnodes 10
# Node names will then be 'Node0' until 'Node9'.
# If you want a specific topology you can also add:
#	'python configFiles.py --nrnodes 10 --topology "ring".
# This will make changes to the files 'config/{virtual,cqc,app}Nodes.cfg' and 'config/topology.json'.
# Port numbers will start at 8801 and depend on the number of nodes used.

import os
import json
from argparse import ArgumentParser

from SimulaQron.settings import Settings
# from configparser import ConfigParser


def construct_node_configs(nodes):
	"""
	Constructs the config files for the nodes and their port numbers.
	Port number used will start from 8801 and end at '8801 + 3*len(nodes)'.
	:param nodes: list of str
		List of the names of the nodes.
	:return: None
	"""
	nrNodes = len(nodes)

	# Get path from environment variable
	netsim_path = os.environ['NETSIM'] + '/'

	# Get path to configuration files
	conf_files = [netsim_path + "config/virtualNodes.cfg",
				  netsim_path + "config/cqcNodes.cfg",
				  netsim_path + "config/appNodes.cfg"]

	# File for just a simple list of the nodes
	node_file = netsim_path + "config/Nodes.cfg"
	# What port numbers to start with
	start_nr = [8801, 8801 + nrNodes, 8801 + 2 * nrNodes]

	# Start of the configuration files
	conf_top = ["# Network configuration file", "#",
				"# For each host its informal name, as well as its location in the network must", "# be listed.", "#",
				"# [name], [hostname], [port number]", "#"]

	# Write to the configuration files
	for i in range(len(conf_files)):
		with open(conf_files[i], 'w') as f:
			for line in conf_top:
				f.write(line + "\n")
			for j in range(nrNodes):
				f.write("{}, localhost, {}\n".format(nodes[j], start_nr[i] + j))

	with open(node_file, 'w') as f:
		for j in range(nrNodes):
			f.write("{}\n".format(nodes[j]))


def construct_topology_config(topology, nodes):
	"""
	Constructs a json file at $NETSIM/config/topology.json, used to define the topology of the network.
	:param topology: str
		Should be one of the following: None, 'complete', 'ring', 'random_tree'.
	:param nodes: list of str
		List of the names of the nodes.
	:return: None
	"""
	if topology:
		netsim_path = os.environ['NETSIM'] + '/'

		if topology == "complete":
			adjacency_dct = {}
			for i, node in enumerate(nodes):
				adjacency_dct[node] = nodes[:i] + nodes[i+1:]

		elif topology == "ring":
			adjacency_dct = {}
			nn = len(nodes)
			for i, node in enumerate(nodes):
				adjacency_dct[node] = [nodes[(i-1) % nn], nodes[(i+1) % nn]]

		elif topology == "path":
			adjacency_dct = {}
			nn = len(nodes)
			for i, node in enumerate(nodes):
				if i == 0:
					adjacency_dct[node] = [nodes[i + 1]]
				elif i == (nn - 1):
					adjacency_dct[node] = [nodes[i - 1]]
				else:
					adjacency_dct[node] = [nodes[(i-1) % nn], nodes[(i+1) % nn]]

		elif topology == 'random_tree':
			raise NotImplementedError("Not implemented yet")

		else:
			raise ValueError("Unknown topology name")


		# settings_file = os.environ["NETSIM"] + "/config/settings.ini"
		topology_file = os.environ["NETSIM"] + "/config/topology.json"
		with open(topology_file, 'w') as top_file:
			json.dump(adjacency_dct, top_file)

		# config = ConfigParser()
		# config.read(settings_file)
		# config["BACKEND"]["topology_file"] = "config/topology.json"
		# with open(settings_file, 'w') as set_file:
		# 	config.write(set_file)

		Settings.set_setting("BACKEND", "topology_file", "config/topology.json")
	else:
		# settings_file = os.environ["NETSIM"] + "/config/settings.ini"
		#
		# config = ConfigParser()
		# config.read(settings_file)
		# config["BACKEND"]["topology_file"] = ""
		# with open(settings_file, 'w') as set_file:
		# 	config.write(set_file)

		Settings.set_setting("BACKEND", "topology_file", "")


def parse_input():
	# Get inputs from terminal
	parser = ArgumentParser()
	parser.add_argument('--nrnodes', required=False, type=str, default=None,
						help='Number of nodes to use in the network.')
	parser.add_argument('--topology', required=False, type=str, default=None,
						help='Which topology to use, if None it will be fully connected.')
	parser.add_argument('--nodes', required=False, type=str, default=None,
						help='Node names to be used in the network')
	args = parser.parse_args()

	# Get the pre set node names
	if args.nodes:
		nodes=args.nodes.split(' ')
	else:
		nodes = []

	if args.nrnodes:
		nrNodes = int(args.nrnodes)

		# Check if there 'nrnodes' is greater then the number of pre-set nodes
		# If so, add more of the form 'node{int}'.
		node_number = 0
		while len(nodes) < nrNodes:
			node_name = "Node{}".format(node_number)
			if not node_name in nodes:
				nodes.append(node_name)
				node_number += 1
			else:
				# This node name was already added, try another one
				node_number += 1

	topology = args.topology

	return nodes, topology


if __name__ == '__main__':
	nodes, topology = parse_input()
	construct_node_configs(nodes=nodes)
	construct_topology_config(topology=topology, nodes=nodes)

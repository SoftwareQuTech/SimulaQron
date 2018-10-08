from argparse import ArgumentParser
import json
import os
import shutil


def construct_node_configs(nodes, config_path, start_nr, ip):
	"""
	Constructs the config files for the nodes and their port numbers.
	Port number used will start from 8801 and end at '8801 + 3*len(nodes)'.
	:param nodes: list of str
		List of the names of the nodes.
	:return: None
	"""
	nrNodes = len(nodes)

	if not os.path.exists(config_path):
		os.makedirs(config_path)

	# Get path to configuration files
	conf_files = [config_path + "/virtualNodes.cfg",
				  config_path + "/cqcNodes.cfg",
				  config_path + "/appNodes.cfg"]

	# File for just a simple list of the nodes
	node_file = config_path + "/Nodes.cfg"
	# What port numbers to start with
	start_nrs = [start_nr, start_nr + nrNodes, start_nr + 2 * nrNodes]

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
				f.write("{}, {}, {}\n".format(nodes[j], ip, start_nrs[i] + j))

	with open(node_file, 'w') as f:
		for j in range(nrNodes):
			f.write("{}\n".format(nodes[j]))

	network_name = config_path.split('/')[-1]
	shutil.copy(conf_files[1], "../network_configs/{}.cfg".format(network_name))

	return start_nr + 3 * nrNodes


def construct_settings(config_path, maxqubits=20, maxregs=1000, waittime=0.5, loglevel_back="warning", backendhandler="simulaqron", topology_file="", noisy_qubits=False, T1=1, loglevel_front="warning"):
	with open(config_path + "/settings.ini", 'w') as settings:
		settings.write("[BACKEND]\n")
		settings.write("maxqubits_per_node = {}\n".format(maxqubits))
		settings.write("maxregisters_per_node = {}\n".format(maxregs))
		settings.write("waittime = {}\n".format(waittime))
		settings.write("loglevel = {}\n".format(loglevel_back))
		settings.write("backendhandler = {}\n".format(backendhandler))
		settings.write("topology_file = {}\n".format(topology_file))
		settings.write("noisy_qubits = {}\n".format(noisy_qubits))
		settings.write("t1 = {}\n".format(T1))
		settings.write("\n")
		settings.write("[FRONTEND]\n")
		settings.write("loglevel = {}\n".format(loglevel_front))


def create_full_config_folder(network_name, start_port, T1, ip, nrnodes):
	topology_file = ".multiple_networks/dutch_topology.json"
	config_path = "configs/" + network_name

	if "complete" in network_name.split('_'):
		# Were creating a complete network
		nodes = ["Node{}".format(i) for i in range(nrnodes)]
		start_nr = construct_node_configs(nodes, config_path, start_port, ip)
		if (T1 is not None) and (T1 > 0):
			construct_settings(config_path, T1=T1, noisy_qubits=True)
		else:
			construct_settings(config_path)
	elif "topology" in network_name.split('_'):
		# Were creating a network with restricted topology
		with open("dutch_topology.json", 'r') as topology:
			tp = json.load(topology)
		nodes = [node for node in tp]
		start_nr = construct_node_configs(nodes, config_path, start_port, ip)
		if (T1 is not None) and (T1 > 0):
			construct_settings(config_path, topology_file=topology_file, T1=T1, noisy_qubits=True)
		else:
			construct_settings(config_path, topology_file=topology_file)
	else:
		raise ValueError("Unknown network name {}".format(network_name))
	return start_nr


def main(T1, IP, start_port, nrnodes):
	network_names = []
	with open("networks.cfg",'r') as network_file:
		for line in network_file.readlines():
			if line[-1] == '\n':
				line = line[:-1]
			if len(line) > 0:
				if line[0] != '#':
					network_names.append(line)
	print(network_names)
	for network_name in network_names:
		start_port = create_full_config_folder(network_name, start_port, T1, IP, nrnodes)





def parse_args():
	parser = ArgumentParser()
	parser.add_argument('--T1', required=False, type=str, default=None,
						help='T1.')
	parser.add_argument('--IP', required=True, type=str,
						help='The IP of this computer.')
	parser.add_argument('--start_port', required=False, type=int, default=8801,
						help='The port number to start with.')
	parser.add_argument('--nr_nodes', required=False, type=int, default=20,
						help='The number of nodes in the complete networks.')
	return parser.parse_args()

if __name__ == '__main__':
	args = parse_args()
	main(args.T1, args.IP, args.start_port, args.nr_nodes)
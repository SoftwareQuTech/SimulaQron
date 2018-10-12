networks = [("network_complete_team01", 1),
	    ("network_complete_team02", 1),
	    ("network_complete_team03", 1),
	    ("network_complete_team04", 2),
	    ("network_complete_team05", 2),
	    ("network_complete_team06", 3),
	    ("network_complete_team07", 3),
	    ("network_complete_team08", 3),
	    ("network_complete_team09", 4),
	    ("network_complete_team10", 4),
            ("network_topology_team01", 1),
	    ("network_topology_team02", 1),
	    ("network_topology_team03", 2),
	    ("network_topology_team04", 2),
	    ("network_topology_team05", 2),
	    ("network_topology_team06", 3),
	    ("network_topology_team07", 3),
	    ("network_topology_team08", 3),
	    ("network_topology_team09", 4),
	    ("network_topology_team10", 4),
	    ("network_complete_common", 4),
	    ("network_topology_common", 4)]

def main():
	ips = []
	with open("computers.cfg", 'r') as comp_file:
		for line in comp_file.readlines():
			ip = line.strip()
			ips.append(ip)

	with open("networks.cfg", 'w') as net_file:
		for network_name, computer in networks:
			net_file.write("{} {}\n".format(network_name, ips[computer-1]))

if __name__ == '__main__':
	main()

import networkx as nx
import os
import json
from matplotlib import pyplot as plt

path = os.environ['NETSIM'] + "/.multiple_networks/"

G = nx.read_gml(path + "SubSurfnet.gml")

nx.draw(G, with_labels=True)

plt.savefig(path + "topology.png")

print(G.number_of_nodes())
print(G.number_of_edges())
print(G.nodes())
topology = nx.to_dict_of_lists(G)
print(type(topology))
with open(path + "dutch_topology.json", 'w') as f:
	json.dump(topology, f)

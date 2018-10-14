import subprocess
import os 
import ast
import cabler

pass_ok=True
port=None
host=None
node=None

while pass_ok:
	node = input("Enter node: ")
	port = int(input("Enter port: "))
	host = input("Enter host: ")
	pass_ok=False

#
cabler = cabler.Command()
cabler.add_node(node, host, port)


fh = open("../config/Nodes.cfg", "r")
nodes=[]
for n in fh.readlines():
	nodes.append(n)

print("The nodes are: ", nodes )

neigbors = input("Enter neigbors of "+ node )

## read the topology file and update it


with open("../config/topology.json", "r") as f:
        s = f.read()
        topology = ast.literal_eval(s)
        topology[node] = [neigbors]

print(topology)

fh = open("../config/topology.json", "w")
fh.write(str(topology))

exit()

os.system("python startNode.py "+node)
os.system("python startCQC.py "+node)

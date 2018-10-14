import subprocess
import os 
import ast
import cabler
import socket

port=None
host=None
node=None

node=input("Enter node: ")

while(True):
    try:
        port=int(input("Enter port: "))
        if port >= 1024 and port <= 65535:
            break
    except:
        print("Please provide a valid port number in the range 1024-65535.")

while(True):
    try:
        host=input("Enter host: ")
        socket.gethostbyname(host)
        break
    except socket.error:
        print("Please provide a valid host name.")


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

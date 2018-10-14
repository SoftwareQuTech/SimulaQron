import subprocess
import os 
import ast
from cabler import Command
import socket
import json

config = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'config'))
run = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'run'))

nodesFile = os.environ.get('NETSIM') + "/config/Nodes.cfg"
topologyFile = os.environ.get('NETSIM') + "/config/topology.json"

startNode = os.environ.get('NETSIM') + "/run/startNode.py"
startCQC = os.environ.get('NETSIM') + "/run/startCQC.py"
# startCQC = os.path.join(run, 'startCQC.py')

def get_input():
    port, host, node = None, None, None
    node=input("Enter node: ")

    while(True):
        try:
            port=int(input("Enter port: "))
            if port >= 8000 and port <= 9000:
                break
        except:
            print("Please provide a valid port number in the range 8000-9000.")

    while(True):
        try:
            host=input("Enter host: ")
            socket.gethostbyname(host)
            break
        except socket.error:
            print("Please provide a valid host name.")

    return port, host, node

def add_cabler(port, host, node):
    cabler = Command()
    cabler.add_node(node, host, port)
    
def read_config_Nodes():
    fh = open(nodesFile, "r")
    nodes=[]
    for n in fh.readlines():
        nodes.append(n.strip())
    print("The nodes are: ", nodes )
    return nodes

def get_input_neigbors(node):
    neigbors = input("Enter neigbors of "+ node )
    return neigbors

## read the topology file and update it
def update_topology(node, neigbors):
    with open(topologyFile, "r") as f:
            # s = f.read()
            topology = json.load(f)
            topology[node] = [neigbors]
    print("The new topology {}".format(topology))

    with open(topologyFile, 'w') as fp:
        fp.write(str(topology))


if __name__ == "__main__":
    port, host, node = get_input()
    add_cabler(port, host, node)
    nodes = read_config_Nodes()
    neigbors = get_input_neigbors(node)
    update_topology(node, neigbors)

    print("Where are here 0")
    print ("python " + startNode + " " +node)
    os.system("python " + startNode + " " +node + "&")
    print("Where are here 1")
    os.system("python "+ startCQC   + " " +node + "&")
    print("Where are here 2")

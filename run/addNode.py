import subprocess
import os 
import ast
import cabler
import socket
import json


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
    cabler = cabler.Command()
    cabler.add_node(node, host, port)

def read_config_Nodes():
    fh = open("../config/Nodes.cfg", "r")
    nodes=[]
    for n in fh.readlines():
        nodes.append(n)
    print("The nodes are: ", nodes )
    return nodes

def get_input_neigbors(node):
    neigbors = input("Enter neigbors of "+ node )
    return neigbors

## read the topology file and update it
def update_topology(node, neigbors):
    with open("../config/topology.json", "r") as f:
            s = f.read()
            topology = ast.literal_eval(s)
            topology[node] = [neigbors]
    print(topology)

    with open('../config/topology.json', 'w') as fp:
        json.dump(topology, fp)


if __name__ == "__main__":
    port, host, node = get_input()
    add_cabler(port, host, node)
    nodes = read_config_Nodes()
    neigbors = get_input_neigbors(node)
    update_topology(node, neigbors)

    os.system("python startNode.py "+node)
    os.system("python startCQC.py "+node)

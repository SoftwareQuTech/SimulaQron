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

import socket
import struct
from twisted.spread import pb
from ipaddress import IPv4Address

from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor


def node_id(fam, ip):
    if fam == socket.AF_INET:
        return struct.unpack("!L", IPv4Address(ip).packed)[0]
    else:
        raise ValueError("No IPv6 yet :(")


def node_id_from_addrinfo(addr):
    fam = addr[0]
    sockaddr = addr[4]
    ip = sockaddr[0]
    return node_id(fam, ip)


def get_node_id_from_net_config(net_config, node_name):
    """
    NOTE node ID is the index of the node name of a sorted list of all the node names in the network.
    """
    if node_name not in net_config.hostDict:
        raise ValueError(f"node name {node_name} not in host_dict ({net_config.hostDict.keys()})")
    return list(sorted(net_config.hostDict.keys())).index(node_name)


def load_node_names(config_file):
    """
    Load list of nodes from Nodes.cfg file

    :param config_file: str
        pointing to Nodes.cfg file
    """
    with open(config_file, 'r') as f:
        return [line.strip() for line in f.readlines()]


class Host(pb.Referenceable):
    def __init__(self, name, hostname, port):
        """
        Initialize the details of the host. For now, we just keep the following:

        name        informal name of the host (e.g. Alice)
        hostname    name of the node on the network (e.g. localhost or yournode.qutech.nl)
        port        port number on hostname
        """

        self.name = name
        self.hostname = hostname
        self.port = int(port)

        # Lookup IP address
        addrs = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP, family=socket.AF_INET)
        addr = addrs[0]
        self.family = addr[0]
        self.addr = addr

        self.ip = node_id_from_addrinfo(addr)

        # Connection identifiers used after connected
        self.factory = 0
        self.root = 0
        self.defer = 0


class SocketsConfig(pb.Referenceable):
    def __init__(self, filename, network_name="default", config_type="vnode"):
        """
        Initialize by reading in the configuration file.

        With version 3.0.0 there is a single config used for all networks and all config types.
        Therefore one needs to also specify the network_name and config_type ('vnode', 'app')
        """
        # Dictionary where we will keep host details, indexed by node name (e.g. Alice)
        self.hostDict = {}

        # Read config file
        self.read_config(filename, network_name=network_name, config_type=config_type)

    def read_config(self, filename, network_name="default", config_type="vnode"):
        """
        Reads the configuration file in which each line has the form: node name, hostname, port number.
        For example:
        Alice, localhost, 8888
        """
        with open(filename) as confFile:
            if filename.endswith(".json"):
                if config_type not in ["vnode", "qnodeos", "app"]:
                    raise ValueError("Type needs to be either 'vnode', 'qnodeos' or 'app'")
                if network_name is None:
                    network_name = "default"
                network_config = NetworksConfigConstructor(file_path=filename).networks[network_name]
                nodes = network_config.nodes
                for node_name, node_config in nodes.items():
                    hostname = getattr(node_config, "{}_hostname".format(config_type))
                    port = getattr(node_config, "{}_port".format(config_type))
                    self.hostDict[node_name] = Host(node_name, hostname, port)

            elif filename.endswith(".cfg"):
                for line in confFile:
                    if not line.startswith("#"):
                        words = line.split(",")

                        # We will simply ignore lines which are not of the right form
                        if len(words) == 3:
                            newHost = Host(words[0].strip(), words[1].strip(), words[2].strip())
                            self.hostDict[words[0]] = newHost
            else:
                raise ValueError("Unknown file type {}".format(filename.split(".")[-1]))

    def print_details(self, name):
        """
        Prints the details of the specified node with name.
        """
        host = self.hostDict[name]
        print("Host details of ", name, ": ", host.hostname, ":", host.port)

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
from ipaddress import IPv4Address
from typing import Dict

from twisted.spread import pb

from simulaqron.settings.network_config import NetworkConfigBuilder, NodeConfigType


class Host(pb.Referenceable):
    def __init__(self, name: str, hostname: str, port: int):
        """
        Initialize the details of the host. For now, we just keep the following:

        name        informal name of the host (e.g. Alice)
        hostname    name of the node on the network (e.g. localhost or yournode.qutech.nl)
        port        port number on hostname
        """

        self.name = name
        self.hostname = hostname
        self.port = port

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
    def __init__(self, nets_config: NetworkConfigBuilder, network_name: str = "default",
                 config_type: str | NodeConfigType = "vnode"):
        """
        Initialize by reading in the configuration file.

        With version 4.0.0, we use the already in-memory information to create the SocketsConfig object.
        This avoids reading the file multiple times, which might have been updated by other processes
        in between reads. Additionally, this also simplifies the code, and reduces the potential source
        of bugs in the configuration read/write code.
        """
        # Dictionary where we will keep host details, indexed by node name (e.g. Alice)
        self.hostDict: Dict[str, Host] = {}

        for node in nets_config.get_nodes(network_name):
            self.hostDict[node.name] = Host(node.name, *node.get_config(config_type))

    def print_details(self, name: str):
        """
        Prints the details of the specified node with name.
        """
        host = self.hostDict[name]
        print("Host details of ", name, ": ", host.hostname, ":", host.port)


def node_id(fam: socket.AddressFamily, ip: str) -> int:
    if fam == socket.AF_INET:
        return struct.unpack("!L", IPv4Address(ip).packed)[0]
    else:
        raise ValueError("No IPv6 yet :(")


def node_id_from_addrinfo(
        addr: tuple[socket.AddressFamily, socket.SocketKind, int, str, tuple[str, int]]
) -> int:
    fam = addr[0]
    sockaddr = addr[4]
    ip = sockaddr[0]
    return node_id(fam, ip)


def get_node_id_from_net_config(net_config: SocketsConfig, node_name: str) -> int:
    """
    NOTE node ID is the index of the node name of a sorted list of all the node names in the network.
    """
    if node_name not in net_config.hostDict:
        raise ValueError(f"node name {node_name} not in host_dict ({net_config.hostDict.keys()})")
    return list(sorted(net_config.hostDict.keys())).index(node_name)

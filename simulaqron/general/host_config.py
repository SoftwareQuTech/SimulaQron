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
from typing import Dict, List

from twisted.spread import pb

from simulaqron.settings.network_config import NetworksConfiguration, NodeConfigType


class Host(pb.Referenceable):
    def __init__(self, name: str, hostname: str, port: int):
        """
        Class representing a host that runs a SimulaQron Virtual Node. It holds the following information:

        :param name: Informal name of the host (e.g. Alice)
        :type name: str
        :param hostname: Name of the node on the network (e.g. localhost or yournode.qutech.nl)
        :type hostname: str
        :param port: Port number on hostname
        :type port: int
        """

        self.name = name
        self.hostname = hostname
        self.port = port

        # Lookup IP address
        addrs = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP, family=socket.AF_INET)
        addr = addrs[0]
        self.family = addr[0]
        self.addr = addr

        self.ip = _node_id_from_addrinfo(addr)

        # Connection identifiers used after connected
        self.factory = 0
        self.root = 0
        self.defer = 0


class SocketsConfig(pb.Referenceable):
    def __init__(self, nets_config: NetworksConfiguration, network_name: str = "default",
                 config_type: NodeConfigType | str = "vnode"):
        """
        Structure used to hold the sockets configuration for a particular component.

        With version 4.0.0, we use the already in-memory information to create the SocketsConfig object.
        This avoids reading the file multiple times, which might have been updated by other processes
        in between reads. Additionally, this also simplifies the code, and reduces the potential source
        of bugs in the configuration read/write code.

        :param nets_config: :py:class:`NetworksConfiguration` object, containing the loaded ``simulaqron_network.json``
                            file.
        :type nets_config: NetworksConfiguration
        :param network_name: The name of the network to use. This name must exist in the loaded network
                             configuration object.
        :type network_name: str
        :param config_type: The type of configuration to use. Valid values are instances of the
                            :py:class:`NodeConfigType` enum, or the string that represent each of those values.
        :type config_type: NodeConfigType | str
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

    def filter(self, nodes_to_keep: List[str]):
        """
        Filter the loaded sockets configurations to only contain the given names.
        If a given node name is not found in the loaded one, it will simply be ignored
        from the exclusion process (i.e. it will not break the process)

        :param nodes_to_keep: The node names to keep after filtering.
        :type nodes_to_keep: List[str]
        """
        nodes_kept = {}
        for node_name in self.hostDict.keys():
            if node_name in nodes_to_keep:
                nodes_kept[node_name] = self.hostDict[node_name]
        self.hostDict = nodes_kept


def _node_id(fam: socket.AddressFamily, ip: str) -> int:
    if fam == socket.AF_INET:
        return struct.unpack("!L", IPv4Address(ip).packed)[0]
    else:
        raise ValueError("No IPv6 yet :(")


def _node_id_from_addrinfo(
        addr: tuple[socket.AddressFamily, socket.SocketKind, int, str, tuple[str, int]]
) -> int:
    fam = addr[0]
    sockaddr = addr[4]
    ip = sockaddr[0]
    return _node_id(fam, ip)


def get_node_id_from_net_config(net_config: SocketsConfig, node_name: str) -> int:
    """
    Gets the node ID from the given sockets config and node name.

    .. note:: node ID is the index of the node name of a sorted list of all the node names in the network.

    :param net_config: SocketsConfig object.
    :type net_config: SocketsConfig
    :param node_name: The name of the node to get the node ID from.
    :type node_name: str
    :return: The node ID from the given sockets config and node name.
    :rtype: int
    """
    if node_name not in net_config.hostDict:
        raise ValueError(f"node name {node_name} not in host_dict ({net_config.hostDict.keys()})")
    return list(sorted(net_config.hostDict.keys())).index(node_name)

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

import json
import logging

from twisted.internet.defer import DeferredLock
from twisted.internet.protocol import Factory

from simulaqron.settings import simulaqron_settings
from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor

from cqc.Protocol import CQCProtocol


###############################################################################
#
# CQC Factory
#
# Twisted factory for the CQC protocol
#


class CQCFactory(Factory):
    def __init__(self, host, name, cqc_net, backend, network_name="default"):
        """
        Initialize CQC Factory.

        lhost	details of the local host (class host)
        """

        self.host = host
        self.name = name
        self.cqcNet = cqc_net
        self.virtRoot = None
        self.qReg = None
        self.backend = backend(self)
        self.network_name = network_name

        # Dictionary that keeps qubit dictorionaries for each application
        self.qubitList = {}

        # Lock governing access to the qubitList
        self._lock = DeferredLock()

        # Read in topology, if specified. topology=None means fully connected
        # topology
        self.topology = None
        if simulaqron_settings.topology_file is not None and simulaqron_settings.topology_file != "":
            self._setup_topology(simulaqron_settings.topology_file)
        else:
            if simulaqron_settings.network_config_file is not None:
                networks_config = NetworksConfigConstructor(file_path=simulaqron_settings.network_config_file)
                self.topology = networks_config.networks[network_name].topology

    def buildProtocol(self, addr):
        """
        Return an instance of CQCProtocol when a connection is made.
        """
        return CQCProtocol(self)

    def set_virtual_node(self, virtRoot):
        """
        Set the virtual root allowing connections to the SimulaQron backend.
        """
        self.virtRoot = virtRoot

    def lookup(self, ip, port):
        """
        Lookup name of remote host used within SimulaQron given ip and
        portnumber.
        """
        for entry in self.cqcNet.hostDict:
            node = self.cqcNet.hostDict[entry]
            if (node.ip == ip) and (node.port == port):
                return node.name

        logging.debug("CQC %s: No such node", self.name)
        return None

    def _setup_topology(self, topology_file):
        """
        Sets up the topology, if specified.
        :param topology_file: str
            The relative path to the json-file defining the topology. It will
            be assumed that the absolute path to the file is
            $simulaqron_path/topology_file.
            If topology is an empty string then a fully connected topology will
            be used.
        :return: None
        """
        try:
            with open(topology_file, "r") as top_file:
                try:
                    self.topology = json.load(top_file)
                except json.JSONDecodeError:
                    raise RuntimeError("Could not parse the json file: {}".format(topology_file))
        except FileNotFoundError:
            raise FileNotFoundError("Could not find the file specifying the topology:" " {}".format(topology_file))
        except IsADirectoryError:
            raise FileNotFoundError("Could not find the file specifying the topology: " "{}".format(topology_file))

    def is_adjacent(self, remote_host_name):
        """
        Checks if remote host is adjacent to this node, according to the
        specified topology.

        :param remote_host_name: str
            The name of the remote host
        :return:
        """
        # Check if a topology is defined, otherwise use fully connected
        if self.topology is None:
            return True

        if self.name in self.topology:
            if remote_host_name in self.topology[self.name]:
                return True
            else:
                return False
        else:
            logging.warning(
                "Node {} is not in the specified topology and is therefore "
                "assumed to have no neighbors".format(self.name)
            )
            return False

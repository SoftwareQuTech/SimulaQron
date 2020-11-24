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

import sys

from twisted.internet import reactor
from twisted.internet.defer import DeferredLock, inlineCallbacks
from twisted.internet.protocol import Factory, Protocol, connectionDone
from twisted.internet.task import deferLater

from netqasm.logging.glob import get_netqasm_logger
from netqasm.backend.messages import MessageHeader, ErrorMessage, ErrorCode, deserialize_host_msg

from simulaqron.settings import simulaqron_settings
from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor


class IncompleteMessageError(ValueError):
    pass


class NetQASMProtocol(Protocol):
    # Dictionary storing the next unique qubit id for each used app_id
    _next_q_id = {}

    # Dictionary storing the next unique entanglement id for each used
    # (host_app_id,remote_node,remote_app_id)
    _next_ent_id = {}

    def __init__(self, factory):

        # NetQASM Factory, including our connection to the SimulaQron backend
        self.factory = factory

        # Default application ID, typically one connection per application but
        # we will deliberately NOT check for that since this is the task of
        # higher layers or an OS
        self.app_id = 0

        # Define the backend to use.
        self.messageHandler = factory.backend
        self.messageHandler.protocol = self

        # Flag to determine whether we already received _all_ of the NetQASM header
        self.got_netqasm_header = False

        # Header for which we are currently processing a packet
        self.currHeader = None

        # Buffer received data (which may arrive in chunks)
        self.buf = None

        # Convenience
        self.name = self.factory.name

        self._logger = get_netqasm_logger(f"{self.__class__.__name__}({self.name})")
        self._logger.debug("Initialized Protocol")

    def connectionMade(self):
        pass

    def connectionLost(self, reason=connectionDone):
        pass

    def dataReceived(self, data):
        """
        Receive data. We will always wait to receive enough data for the
        header, and then the entire packet first before commencing processing.
        """
        # Read whatever we received into a buffer
        if self.buf:
            self.buf = self.buf + data
        else:
            self.buf = data

        try:
            msg_id, msg = self._parse_message()
        except IncompleteMessageError:
            return

        d = self.messageHandler.handle_netqasm_message(msg_id=msg_id, msg=msg)
        d.addCallback(self.log_handled_message)
        d.addErrback(self.log_error)

    def log_handled_message(self, result):
        self._logger.info(f"Finished handling message with result = {result}")

    @inlineCallbacks
    def log_error(self, failure):
        self._logger.error(f"Handling message failed with failure = {failure}")
        sys.stderr.write(str(failure))
        self._return_msg(msg=ErrorMessage(err_code=ErrorCode.GENERAL))
        yield deferLater(reactor, 0.1, self.stop)

    def stop(self):
        self.factory.stop()

    def _parse_message(self):
        try:
            msg_hdr = MessageHeader.from_buffer_copy(self.buf)
        except ValueError:
            raise IncompleteMessageError
        if len(self.buf) < msg_hdr.length:
            raise IncompleteMessageError
        msg = deserialize_host_msg(self.buf[MessageHeader.len():])
        self.buf = self.buf[msg_hdr.length:]

        return msg_hdr.id, msg

    def _handle_init_new_app(self, msg):
        app_id = msg.app_id
        self._add_app(app_id=app_id)
        max_qubits = msg.max_qubits
        self._logger.debug(f"Allocating a new "
                           f"unit module of size {max_qubits} for application with app ID {app_id}.\n")
        self._executioner.init_new_application(
            app_id=app_id,
            max_qubits=max_qubits,
        )

    def _return_msg(self, msg):
        """
        Return a msg to the host.
        """
        self.transport.write(msg)


###############################################################################
#
# NetQASM Factory
#
# Twisted factory for the NetQASM protocol
#


class NetQASMFactory(Factory):
    def __init__(self, host, name, qnodeos_net, backend, network_name="default"):
        """
        Initialize NetQASM Factory.

        lhost	details of the local host (class host)
        """

        self.host = host
        self.name = name
        self.qnodeos_net = qnodeos_net
        self.virtRoot = None
        self.qReg = None
        self.backend = backend(self)
        self.network_name = network_name

        # Dictionary that keeps qubit dictorionaries for each application
        self.qubitList = {}

        # Lock governing access to the qubitList
        self._lock = DeferredLock()

        self._logger = get_netqasm_logger(f"{self.__class__.__name__}({name})")

        # Read in topology, if specified. topology=None means fully connected
        # topology
        self.topology = None
        if simulaqron_settings.network_config_file is not None:
            networks_config = NetworksConfigConstructor(file_path=simulaqron_settings.network_config_file)
            self.topology = networks_config.networks[network_name].topology

    def stop(self):
        reactor.stop()

    def buildProtocol(self, addr):
        """
        Return an instance of NetQASMProtocol when a connection is made.
        """
        return NetQASMProtocol(self)

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
        for entry in self.qnodeos_net.hostDict:
            node = self.qnodeos_net.hostDict[entry]
            if (node.ip == ip) and (node.port == port):
                return node.name

        self._logger.debug("No such node")
        return None

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
            self._logger.warning(
                "Node {} is not in the specified topology and is therefore "
                "assumed to have no neighbors".format(self.name)
            )
            return False

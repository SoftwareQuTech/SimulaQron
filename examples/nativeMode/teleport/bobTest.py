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


import logging
import numpy as np

from simulaqron.local.setup import setup_local, assemble_qubit
from simulaqron.general.hostConfig import socketsConfig
from simulaqron.settings import simulaqron_settings
from simulaqron.toolbox.stabilizerStates import StabilizerState
from twisted.internet.defer import inlineCallbacks
from twisted.spread import pb


#####################################################################################################
#
# runClientNode
#
# This will be run on the local node if all communication links are set up (to the virtual node
# quantum backend, as well as the nodes in the classical communication network), and the local classical
# communication server is running (if applicable).
#
def runClientNode(qReg, virtRoot, myName, classicalNet):
    """
    Code to execture for the local client node. Called if all connections are established.

    Arguments
    qReg        quantum register (twisted object supporting remote method calls)
    virtRoot    virtual quantum ndoe (twisted object supporting remote method calls)
    myName        name of this node (string)
    classicalNet    servers in the classical communication network (dictionary of hosts)
    """

    logging.debug("LOCAL %s: Runing client side program.", myName)


#####################################################################################################
#
# localNode
#
# This will be run if the local node acts as a server on the classical communication network,
# accepting remote method calls from the other nodes.


class localNode(pb.Root):
    def __init__(self, node, classicalNet):

        self.node = node
        self.classicalNet = classicalNet

        self.virtRoot = None
        self.qReg = None

    def set_virtual_node(self, virtRoot):
        self.virtRoot = virtRoot

    def set_virtual_reg(self, qReg):
        self.qReg = qReg

    def remote_test(self):
        return "Tested!"

        # This can be called by Alice to tell Bob where to get the qubit and what corrections to apply

    @inlineCallbacks
    def remote_recover_teleport(self, a, b, virtualNum):
        """
        Recover the qubit from teleportation.

        Arguments
        a,b        received measurement outcomes from Alice
        virtualNum    number of the virtual qubit corresponding to the EPR pair received
        """

        logging.debug("LOCAL %s: Getting reference to qubit number %d.", self.node.name, virtualNum)

        eprB = yield self.virtRoot.callRemote("get_virtual_ref", virtualNum)

        # Apply the desired correction info
        logging.debug("LOCAL %s: Correction info is a=%d, b=%d.", self.node.name, a, b)
        if b == 1:
            yield eprB.callRemote("apply_X")
        if a == 1:
            yield eprB.callRemote("apply_Z")

        # Just print the qubit we received
        if simulaqron_settings.backend == "qutip":
            print("here")
            (realRho, imagRho) = yield eprB.callRemote("get_qubit")
            state = np.array(assemble_qubit(realRho, imagRho), dtype=complex)
        elif simulaqron_settings.backend == "projectq":
            realvec, imagvec = yield self.virtRoot.callRemote("get_register_RI", eprB)
            state = [r + (1j * j) for r, j in zip(realvec, imagvec)]
        elif simulaqron_settings.backend == "stabilizer":
            array, _, = yield self.virtRoot.callRemote("get_register_RI", eprB)
            state = StabilizerState(array)
        else:
            ValueError("Unknown backend {}".format(simulaqron_settings.backend))

        print("Qubit is:\n{}".format(state))


#####################################################################################################
#
# main
#
def main():

    # In this example, we are Bob.
    myName = "Bob"

    # This file defines the network of virtual quantum nodes
    network_file = simulaqron_settings.network_config_file

    # This file defines the nodes acting as servers in the classical communication network
    classicalFile = "classicalNet.cfg"

    # Read configuration files for the virtual quantum, as well as the classical network
    virtualNet = socketsConfig(network_file)
    classicalNet = socketsConfig(classicalFile)

    # Check if we should run a local classical server. If so, initialize the code
    # to handle remote connections on the classical communication network
    if myName in classicalNet.hostDict:
        lNode = localNode(classicalNet.hostDict[myName], classicalNet)
    else:
        lNode = None

        # Set up the local classical server if applicable, and connect to the virtual
        # node and other classical servers. Once all connections are set up, this will
        # execute the function runClientNode
    setup_local(myName, virtualNet, classicalNet, lNode, runClientNode)


##################################################################################################
logging.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s", level=logging.DEBUG)
main()

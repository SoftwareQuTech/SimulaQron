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
import time
from twisted.spread import pb
from twisted.internet import reactor, error
from twisted.internet.defer import DeferredList
from twisted.internet.error import ReactorNotRunning

from simulaqron.settings import simulaqron_settings


# logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)
#####################################################################################################
#
# setup_local
#
# Sets up the local classical comms server (if applicable), and connects to the local virtual node
# and other classical communication servers.


def setup_local(myName, virtualNet, classicalNet, lNode, func, *args, **kwargs):
    """
    Sets up
    - local classical communication server (if desired according to the configuration file)
    - client connection to the local virtual node quantum backend
    - client connections to all other classical communication servers

    Arguments
    myName            name of this node (string)
    virtualNet        servers of the virtual nodes (dictionary of host objects)
    classicalNet      servers on the classical communication network (dictionary of host objects)
    lNode             Twisted PB root to use as local server (if applicable)
    func              function to run if all connections are set up
    args, kwargs   additional arguments to be given to func
    """

    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s",
        level=simulaqron_settings.log_level,
    )

    # Initialize Twisted callback framework
    dList = []

    # If we are listed as a server node for the classical network, start this server
    if myName in classicalNet.hostDict:
        try:
            logging.debug("LOCAL %s: Starting local classical communication server.", myName)
            nb = classicalNet.hostDict[myName]
            nb.root = lNode
            nb.factory = pb.PBServerFactory(nb.root)
            reactor.listenTCP(nb.port, nb.factory)
        except Exception as e:
            logging.error("LOCAL %s: Cannot start classical communication servers.", myName, e.strerror)
            return

    # Give the server some time to start up
    time.sleep(3)

    # Connect to the local virtual node simulating the "local" qubits
    logging.debug("LOCAL %s: Connecting to local virtual node.", myName)
    node = virtualNet.hostDict[myName]
    factory = pb.PBClientFactory()
    reactor.connectTCP(node.hostname, node.port, factory)
    deferVirtual = factory.getRootObject()
    dList.append(deferVirtual)

    # Set up a connection to all the other nodes in the classical network
    for node in classicalNet.hostDict:
        nb = classicalNet.hostDict[node]
        if nb.name != myName:
            logging.debug("LOCAL %s: Making classical connection to %s.", myName, nb.name)
            nb.factory = pb.PBClientFactory()
            reactor.connectTCP(nb.hostname, nb.port, nb.factory)
            dList.append(nb.factory.getRootObject())

    deferList = DeferredList(dList, consumeErrors=True)
    deferList.addCallback(init_register, myName, virtualNet, classicalNet, lNode, func, *args, **kwargs)
    deferList.addErrback(localError)
    try:
        reactor.run()
    except error.ReactorNotRestartable:
        pass


##################################################################################################
#
# init_register
#
# Called if all servers are started and all connections are made. Retrieves the relevant
# root objects to talk to such remote connections
#


def init_register(resList, myName, virtualNet, classicalNet, lNode, func, *args, **kwargs):

    logging.debug("LOCAL %s: All connections set up.", myName)

    # Retrieve the connection to the local virtual node, if successfull
    j = 0
    if resList[j][0]:
        virtRoot = resList[j][1]
        if lNode is not None:
            lNode.set_virtual_node(virtRoot)
    else:
        print(resList)
        logging.error("LOCAL %s: Connection to virtual server failed!", myName)
        reactor.stop()

        # Retrieve connections to the classical nodes
    for node in classicalNet.hostDict:
        nb = classicalNet.hostDict[node]
        if nb.name != myName:
            j = j + 1
            if resList[j][0]:
                nb.root = resList[j][1]
                logging.debug("LOCAL %s: Connected node %s with %s", myName, nb.name, nb.root)
            else:
                logging.error("LOCAL %s: Connection to %s failed!", myName, nb.name)
                reactor.stop()

                # On the local virtual node, we still want to initialize a qubit register
    defer = virtRoot.callRemote("add_register")
    defer.addCallback(fill_register, myName, lNode, virtRoot, classicalNet, func, *args, **kwargs)
    defer.addErrback(localError)


def fill_register(obj, myName, lNode, virtRoot, classicalNet, func, *args, **kwargs):
    logging.debug("LOCAL %s: Created quantum register at virtual node.", myName)
    qReg = obj

    # If we run a server, record the handle to the local virtual register
    if lNode is not None:
        lNode.set_virtual_reg(qReg)

        # Run client side function
    func(qReg, virtRoot, myName, classicalNet, *args, **kwargs)


def localError(reason):
    """
    Error handling for the connection.
    """
    print("Critical error: ", reason)
    try:
        reactor.stop()
    except ReactorNotRunning:
        pass


def assemble_qubit(realM, imagM):
    """
    Reconstitute the qubit as array from its real and imaginary components given as a list.
    We need this since Twisted PB does not support sending complex valued object natively.
    """
    M = realM
    for s in range(len(M)):
        for t in range(len(M)):
            M[s][t] = realM[s][t] + 1j * imagM[s][t]

    return M

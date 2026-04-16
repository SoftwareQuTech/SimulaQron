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
from typing import Callable

from twisted.internet import error
from twisted.internet.defer import Deferred, DeferredList
from twisted.internet.error import ReactorNotRunning
from twisted.spread import pb

from simulaqron.general.host_config import SocketsConfig
from simulaqron.reactor import reactor
from simulaqron.settings import simulaqron_settings

_logger = logging.getLogger("setup-local")

# Connection retry settings (uses simulaqron's config values)
_CONN_RETRY_TIME = None   # Lazy-loaded from simulaqron_settings
_CONN_MAX_RETRIES = None


def _get_retry_settings():
    """Load retry settings from simulaqron config (lazy, to avoid import-time issues)."""
    global _CONN_RETRY_TIME, _CONN_MAX_RETRIES
    if _CONN_RETRY_TIME is None:
        try:
            _CONN_RETRY_TIME = simulaqron_settings.conn_retry_time
            _CONN_MAX_RETRIES = simulaqron_settings.conn_max_retries
        except Exception:
            _CONN_RETRY_TIME = 0.5
            _CONN_MAX_RETRIES = 10
    return _CONN_RETRY_TIME, _CONN_MAX_RETRIES


def _connect_with_retry(hostname, port, name="unknown"):
    """
    Connect to a PB server with retry logic.  Returns a Deferred that fires
    with the PB root object once the connection succeeds, or errbacks after
    exhausting all retries.

    This mirrors the retry pattern used by the virtual nodes in virtual.py.
    """
    retry_time, max_retries = _get_retry_settings()
    result_deferred = Deferred()

    def attempt(retries_left):
        factory = pb.PBClientFactory()
        reactor.connectTCP(hostname, port, factory)
        d = factory.getRootObject()
        d.addCallback(on_success)
        d.addErrback(on_failure, retries_left)

    def on_success(root):
        if not result_deferred.called:
            result_deferred.callback(root)

    def on_failure(failure, retries_left):
        if retries_left > 0:
            _logger.debug("Connection to %s (%s:%d) failed, retrying in %ss (%d retries left)...",
                          name, hostname, port, retry_time, retries_left)
            reactor.callLater(retry_time, attempt, retries_left - 1)
        else:
            _logger.error("Connection to %s (%s:%d) failed after all retries.", name, hostname, port)
            if not result_deferred.called:
                result_deferred.errback(failure)

    # Schedule the first attempt for when the reactor is running
    reactor.callWhenRunning(attempt, max_retries)
    return result_deferred


#####################################################################################################
#
# setup_local
#
# Sets up the local classical application level comms server (if applicable), and connects to the local
# virtual node and other classical communication servers.


def setup_local(myName: str, virtualNet: SocketsConfig, classicalNet: SocketsConfig,
                lNode: pb.Root, func: Callable, *args, **kwargs):
    """
    Sets up a local classical application level communication server (if desired according to the configuration file),
    a client connection to the local virtual node quantum backend and a client connections to all other
    classical communication servers.

    :param myName: Name of this node.
    :type myName: str
    :param virtualNet: Servers of the virtual nodes (dictionary of host objects).
    :type virtualNet: SocketsConfig
    :param classicalNet: Servers on the classical communication network (dictionary of host objects).
    :type classicalNet: SocketsConfig
    :param lNode: Twisted PB root to use as local server (if applicable).
    :type lNode: pb.Root
    :param func: Function to run if all connections are set up.
    :type func: Callable
    :param args: Additional arguments to be given to ``func``.
    :type args: Any
    :param kwargs: Additional keyword-based arguments to be passed to ``func``.
    :type kwargs: Any
    """

    # If we are listed as a server node for the classical network, start this server
    if myName in classicalNet.hostDict:
        try:
            nb = classicalNet.hostDict[myName]
            _logger.debug("SETUP_LOCAL %s: Starting local classical communication server (%s: %s, %d).",
                          myName, nb.name, nb.hostname, nb.port
                          )
            nb.root = lNode
            nb.factory = pb.PBServerFactory(nb.root)
            reactor.listenTCP(nb.port, nb.factory)
        except Exception as e:
            _logger.error("SETUP_LOCAL %s: Cannot start classical communication servers: %s", myName, e)
            return

    # Connect to the local virtual node simulating the "local" qubits (with retry)
    node = virtualNet.hostDict[myName]
    _logger.debug("SETUP_LOCAL %s: Connecting to local virtual node (%s: %s, %d).", myName, node.name, node.hostname,
                  node.port)
    dList = [_connect_with_retry(node.hostname, node.port, name=f"vnode-{node.name}")]

    # Set up connections to all other nodes in the classical network (with retry)
    for node in classicalNet.hostDict:
        nb = classicalNet.hostDict[node]
        if nb.name != myName:
            _logger.debug("SETUP_LOCAL %s: Making classical connection to %s (%s: %s, %d).", myName, nb.name, nb.name,
                          nb.hostname, nb.port)
            dList.append(_connect_with_retry(nb.hostname, nb.port, name=nb.name))

    deferList = DeferredList(dList, consumeErrors=True)
    deferList.addCallback(_init_register, myName, virtualNet, classicalNet, lNode, func, *args, **kwargs)
    deferList.addErrback(_localError)
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


def _init_register(resList: DeferredList, myName: str, virtualNet: SocketsConfig, classicalNet: SocketsConfig,
                   lNode: pb.Root, func: Callable, *args, **kwargs):
    _logger.debug("SETUP_LOCAL %s: All connections set up.", myName)

    # Retrieve the connection to the local virtual node, if successful
    j = 0
    if resList[j][0]:
        virtRoot = resList[j][1]
        if lNode is not None:
            lNode.set_virtual_node(virtRoot)
    else:
        _logger.error("SETUP_LOCAL %s: Connection to virtual server failed!", myName)
        reactor.stop()
        return

    # Retrieve connections to the classical nodes
    for node in classicalNet.hostDict:
        nb = classicalNet.hostDict[node]
        if nb.name != myName:
            j = j + 1
            if resList[j][0]:
                nb.root = resList[j][1]
                _logger.debug("SETUP_LOCAL %s: Connected node %s with %s", myName, nb.name, nb.root)
            else:
                _logger.error("SETUP_LOCAL %s: Connection to %s failed!", myName, nb.name)
                reactor.stop()
                return

    # On the local virtual node, we still want to initialize a qubit register
    defer = virtRoot.callRemote("add_register")
    defer.addCallback(_fill_register, myName, lNode, virtRoot, classicalNet, func, *args, **kwargs)
    defer.addErrback(_localError)


def _fill_register(obj, myName, lNode, virtRoot, classicalNet, func, *args, **kwargs):
    _logger.debug("SETUP_LOCAL %s: Created quantum register at virtual node.", myName)
    qReg = obj

    # If we run a server, record the handle to the local virtual register
    if lNode is not None:
        lNode.set_virtual_reg(qReg)

    # Run client side function
    func(qReg, virtRoot, myName, classicalNet, *args, **kwargs)


def _localError(reason):
    """
    Error handling for the connection.
    """
    _logger.error("SETUP_LOCAL: Critical error: %s", reason)
    try:
        reactor.stop()
    except ReactorNotRunning:
        pass

#!/usr/bin/env python
import logging
import sys
import signal
from twisted.internet import reactor
from twisted.internet.error import ConnectionRefusedError, CannotListenError
from twisted.spread import pb

from simulaqron.cqc_backend.cqcProtocol import CQCFactory
from simulaqron.cqc_backend.cqcMessageHandler import SimulaqronCQCHandler
from simulaqron.general.hostConfig import networkConfig
from simulaqron.settings import Settings
from simulaqron.toolbox import get_simulaqron_path


def init_register(virtRoot, myName, node):
    """Retrieves the relevant root objects to talk to such remote connections"""
    logging.debug("LOCAL %s: All connections set up.", myName)
    # Set the virtual node
    node.set_virtual_node(virtRoot)
    # Start listening to CQC messages
    setup_CQC_server(myName, node)


def connect_to_virtNode(myName, cqc_factory, virtualNet):
    """Trys to connect to local virtual node.

    If connection is refused, we try again after a set amount of time
    (specified in handle_connection_error)
    """
    logging.debug("LOCAL %s: Trying to connect to local virtual node.", myName)
    virtual_node = virtualNet.hostDict[myName]
    factory = pb.PBClientFactory()
    # Connect
    reactor.connectTCP(virtual_node.hostname, virtual_node.port, factory)
    deferVirtual = factory.getRootObject()
    # If connection succeeds do:
    deferVirtual.addCallback(init_register, myName, cqc_factory)
    # If connection fails do:
    deferVirtual.addErrback(handle_connection_error, myName, cqc_factory, virtualNet)


def handle_connection_error(reason, myName, cqc_factory, virtualNet):
    """ Handles errors from trying to connect to local virtual node.

    If a ConnectionRefusedError is raised another try will be made after
    Settings.CONF_WAIT_TIME seconds. Any other error is raised again.
    """
    try:
        reason.raiseException()
    except ConnectionRefusedError:
        logging.debug("LOCAL %s: Could not connect, trying again...", myName)
        reactor.callLater(
            Settings.CONF_WAIT_TIME,
            connect_to_virtNode,
            myName,
            cqc_factory,
            virtualNet,
        )
    except Exception as e:
        logging.error(
            "LOCAL %s: Critical error when connection to local virtual node: %s",
            myName,
            e,
        )
        reactor.stop()


def setup_CQC_server(myName, cqc_factory):
    """Setup CQC server to handle remote on the classical communication network."""
    try:
        logging.debug(
            "LOCAL %s: Starting local classical communication server.", myName
        )
        myHost = cqc_factory.host
        myHost.root = cqc_factory
        myHost.factory = cqc_factory
        reactor.listenTCP(myHost.port, myHost.factory)
    except CannotListenError as e:
        logging.error(
            "LOCAL {}: CQC server address ({}) is already in use.".format(
                myName, myHost.port
            )
        )
        reactor.stop()
    except Exception as e:
        logging.error(
            "LOCAL {}: Critical error when starting CQC server: {}".format(myName, e)
        )
        reactor.stop()


def sigterm_handler(_signo, _stack_frame):
    reactor.stop()


def main(myName):
    """Start the indicated backend CQC Server"""
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s",
        level=Settings.CONF_LOGGING_LEVEL_BACKEND,
    )

    # Get path to SimulaQron folder
    simulaqron_path = get_simulaqron_path.main()

    # This file defines the network of virtual quantum nodes
    virtualFile = Settings.CONF_VNODE_FILE

    # This file defines the network of CQC servers interfacing to virtual quantum nodes
    cqcFile = Settings.CONF_CQC_FILE

    # Read configuration files for the virtual quantum, as well as the classical network
    virtualNet = networkConfig(virtualFile)
    cqcNet = networkConfig(cqcFile)

    # Check if we are in the host-dictionary
    if myName in cqcNet.hostDict:
        myHost = cqcNet.hostDict[myName]
        cqc_factory = CQCFactory(myHost, myName, cqcNet, SimulaqronCQCHandler)
    else:
        logging.error("LOCAL %s: Cannot start classical communication servers.", myName)
        return

        # Connect to the local virtual node simulating the "local" qubits
    connect_to_virtNode(myName, cqc_factory, virtualNet)

    # Run reactor
    reactor.run()


if __name__ == '__main__':
    main(sys.argv[1])

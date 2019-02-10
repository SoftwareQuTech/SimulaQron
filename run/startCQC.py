import logging

import sys
from SimulaQron.cqc.backend.cqcConfig import CQC_CONF_LINK_WAIT_TIME
from SimulaQron.cqc.backend.cqcProtocol import CQCFactory
from SimulaQron.cqc.backend.cqcMessageHandler import SimulaqronCQCHandler
from SimulaQron.general.hostConfig import networkConfig
from SimulaQron.settings import Settings
from SimulaQron.toolbox import get_simulaqron_path
from twisted.internet import reactor
from twisted.internet.error import ConnectionRefusedError, CannotListenError
import os


##################################################################################################
#
# init_register
#
# Called if all servers are started and all connections are made. Retrieves the relevant
# root objects to talk to such remote connections
#
from twisted.spread import pb


def init_register(virtRoot, myName, node):
    logging.info("LOCAL %s: All connections set up.", myName)

    # Set the virtual node
    node.set_virtual_node(virtRoot)

    # Start listening to CQC messages
    setup_CQC_server(myName, node)

    # On the local virtual node, we still want to initialize a qubit register
    # defer = virtRoot.callRemote("new_register")
    # defer.addCallback(fill_register, myName, node, virtRoot)
    # defer.addErrback(handle_register_error,myName)


# def fill_register(obj, myName, node, virtRoot):
#     logging.debug("LOCAL %s: Created quantum register at virtual node.",myName)
#     qReg = obj

#     # Record the handle to the local virtual register
#     node.set_virtual_reg(qReg)

#     setup_CQC_server(myName,node)


def connect_to_virtNode(myName, cqc_factory, virtualNet):
    """
    Trys to connect to local virtual node.
    If connection is refused, we try again after a set amount of time (specified in handle_connection_error)
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


# def handle_register_error(reason,myName):
#     """
#     Handles errors from remote call to new register.
#     """
#     logging.error("LOCAL %s: Critical error when making new register: %s",myName,reason.getErrorMessage())
#     reactor.stop()


def handle_connection_error(reason, myName, cqc_factory, virtualNet):
    """
    Handles errors from trying to connect to local virtual node.
    If a ConnectionRefusedError is raised another try will be made after CQC_CONF_WAIT_TIME seconds.
    CQC_CONF_WAIT_TIME is set in 'cqc/backend/cqcConfig.py'.
    Any other error is raised again.
    """

    try:
        reason.raiseException()
    except ConnectionRefusedError:
        logging.debug("LOCAL %s: Could not connect, trying again...", myName)
        reactor.callLater(CQC_CONF_LINK_WAIT_TIME, connect_to_virtNode, myName, cqc_factory, virtualNet)
    except Exception as e:
        logging.error("LOCAL %s: Critical error when connection to local virtual node: %s", myName, e)
        reactor.stop()


def setup_CQC_server(myName, cqc_factory):
    """
    Setup CQC server to handle remote connections using CQC on the classical communication network.
    """
    try:
        logging.debug("LOCAL %s: Starting local classical communication server.", myName)
        myHost = cqc_factory.host
        myHost.root = cqc_factory
        myHost.factory = cqc_factory
        reactor.listenTCP(myHost.port, myHost.factory)
    except CannotListenError:
        logging.error("LOCAL {}: CQC server address ({}) is already in use.".format(myName, myHost.port))
        reactor.stop()
    except Exception as e:
        logging.error("LOCAL {}: Critical error when starting CQC server: {}".format(myName, e))
        reactor.stop()


#####################################################################################################
#
# main
#
# Start the indicated backend CQC Server
#


def main(myName):
    # Get path to SimulaQron folder
    path_to_this_folder = os.path.dirname(os.path.abspath(__file__))
    simulaqron_path = os.path.split(path_to_this_folder)[0]

    # This file defines the network of virtual quantum nodes
    virtualFile = os.path.join(simulaqron_path, "config/virtualNodes.cfg")

    # This file defines the network of CQC servers interfacing to virtual quantum nodes
    cqcFile = os.path.join(simulaqron_path, "config/cqcNodes.cfg")

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


##################################################################################################
logging.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s", level=Settings.CONF_LOGGING_LEVEL_BACKEND)

main(sys.argv[1].strip())

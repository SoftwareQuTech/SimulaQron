#!/usr/bin/env python
import sys
import time
import signal
from timeit import default_timer as timer

from twisted.internet import reactor
from twisted.internet.error import ConnectionRefusedError, CannotListenError
from twisted.spread import pb

from netqasm.logging.glob import get_netqasm_logger, set_log_level

from simulaqron.netqasm_backend.factory import NetQASMFactory
from simulaqron.netqasm_backend.qnodeos import SubroutineHandler
from simulaqron.general.host_config import SocketsConfig
from simulaqron.settings import simulaqron_settings

logger = get_netqasm_logger("start_qnodeos")

_RETRY_TIME = 0.1
_TIMEOUT = 10


def init_register(virtRoot, myName, node):
    """Retrieves the relevant root objects to talk to such remote connections"""
    logger.debug("LOCAL %s: All connections set up.", myName)
    # Set the virtual node
    node.set_virtual_node(virtRoot)
    # Start listening to NetQASM messages
    setup_netqasm_server(myName, node)


def connect_to_virtNode(myName, netqasm_factory, virtual_network):
    """Trys to connect to local virtual node.

    If connection is refused, we try again after a set amount of time
    (specified in handle_connection_error)
    """
    logger.debug("LOCAL %s: Trying to connect to local virtual node.", myName)
    virtual_node = virtual_network.hostDict[myName]
    factory = pb.PBClientFactory()
    # Connect
    reactor.connectTCP(virtual_node.hostname, virtual_node.port, factory)
    deferVirtual = factory.getRootObject()
    # If connection succeeds do:
    deferVirtual.addCallback(init_register, myName, netqasm_factory)
    # If connection fails do:
    deferVirtual.addErrback(handle_connection_error, myName, netqasm_factory, virtual_network)


def handle_connection_error(reason, myName, netqasm_factory, virtual_network):
    """ Handles errors from trying to connect to local virtual node.

    If a ConnectionRefusedError is raised another try will be made after
    Settings.CONF_WAIT_TIME seconds. Any other error is raised again.
    """
    try:
        reason.raiseException()
    except ConnectionRefusedError:
        logger.debug("LOCAL %s: Could not connect, trying again...", myName)
        reactor.callLater(
            simulaqron_settings.conn_retry_time,
            connect_to_virtNode,
            myName,
            netqasm_factory,
            virtual_network,
        )
    except Exception as e:
        logger.error(
            "LOCAL %s: Critical error when connection to local virtual node: %s",
            myName,
            e,
        )
        reactor.stop()


def setup_netqasm_server(myName, netqasm_factory):
    """Setup NetQASM server to handle remote on the classical communication network."""
    t_start = timer()
    while timer() - t_start < _TIMEOUT:
        try:
            logger.debug(
                "LOCAL %s: Starting local classical communication server.", myName
            )
            myHost = netqasm_factory.host
            myHost.root = netqasm_factory
            myHost.factory = netqasm_factory
            reactor.listenTCP(myHost.port, myHost.factory)
            break
        except CannotListenError:
            logger.error(
                "LOCAL {}: NetQASM server address ({}) is already in use, trying again.".format(
                    myName, myHost.port
                )
            )
            time.sleep(_RETRY_TIME)
        except Exception as e:
            logger.error(
                "LOCAL {}: Critical error when starting NetQASM server: {}".format(myName, e)
            )
            reactor.stop()
    else:
        reactor.stop()


def sigterm_handler(_signo, _stack_frame):
    reactor.stop()


def main(myName, network_name="default", log_level="WARNING"):
    """Start the indicated backend NetQASM Server"""
    set_log_level(log_level)
    logger.debug(f"Starting QNodeOS at {myName}")
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    # Since version 3.0.0 a single config file is used
    network_config_file = simulaqron_settings.network_config_file

    # Read configuration files for the virtual quantum, as well as the classical network
    virtual_network = SocketsConfig(network_config_file, network_name=network_name, config_type="vnode")
    qnodeos_network = SocketsConfig(network_config_file, network_name=network_name, config_type="qnodeos")

    # Check if we are in the host-dictionary
    if myName in qnodeos_network.hostDict:
        myHost = qnodeos_network.hostDict[myName]
        logger.debug(f"Setting up QNodeOS protocol factory for {myName}")
        netqasm_factory = NetQASMFactory(
            myHost,
            myName,
            qnodeos_network,
            SubroutineHandler,
            network_name=network_name,
        )
    else:
        logger.error("LOCAL %s: Cannot start classical communication servers.", myName)
        return

    # Connect to the local virtual node simulating the "local" qubits
    logger.debug(f"Connect to virtual node {myName}")
    connect_to_virtNode(myName, netqasm_factory, virtual_network)

    # Run reactor
    reactor.run()
    logger.debug(f"Ending QNodeOS at {myName}")


if __name__ == '__main__':
    main(sys.argv[1])

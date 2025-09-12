#!/usr/bin/env python
import sys
import time
import signal
from timeit import default_timer as timer

from twisted.internet.error import ConnectionRefusedError, CannotListenError
from twisted.spread import pb

from netqasm.logging.glob import get_netqasm_logger, set_log_level

from simulaqron.reactor import reactor
from simulaqron.netqasm_backend.factory import NetQASMFactory
from simulaqron.netqasm_backend.qnodeos import SubroutineHandler
from simulaqron.general.host_config import SocketsConfig
from simulaqron.settings import simulaqron_settings

logger = get_netqasm_logger("start_qnodeos")

_RETRY_TIME = 0.1
_TIMEOUT = 10


def init_register(virt_root, my_name: str, node: NetQASMFactory):
    """Retrieves the relevant root objects to talk to such remote connections"""
    logger.debug("LOCAL %s: Connection to local virtual node successful", my_name)
    # Set the virtual node
    node.set_virtual_node(virt_root)
    # Start listening to NetQASM messages
    setup_netqasm_server(my_name, node)


def connect_to_virt_node(my_name: str , netqasm_factory: NetQASMFactory, virtual_network: SocketsConfig):
    """Tries to connect to local virtual node.

    If connection is refused, we try again after a set amount of time
    (specified in handle_connection_error)
    """
    virtual_node = virtual_network.hostDict[my_name]
    logger.debug(
        "LOCAL %s: Trying to connect to local virtual node at %s, %d.",
        my_name, virtual_node.hostname, virtual_node.port
    )
    factory = pb.PBClientFactory()
    # Connect
    reactor.connectTCP(virtual_node.hostname, virtual_node.port, factory)
    defer_virtual_node = factory.getRootObject()
    # If connection succeeds do:
    defer_virtual_node.addCallback(init_register, my_name, netqasm_factory)
    # If connection fails do:
    defer_virtual_node.addErrback(handle_connection_error, my_name, netqasm_factory, virtual_network)


def handle_connection_error(reason, my_name: str, netqasm_factory: NetQASMFactory, virtual_network: SocketsConfig):
    """ Handles errors from trying to connect to local virtual node.

    If a ConnectionRefusedError is raised another try will be made after
    Settings.CONF_WAIT_TIME seconds. Any other error is raised again.
    """
    try:
        reason.raiseException()
    except ConnectionRefusedError:
        logger.debug("LOCAL %s: Could not connect, trying again...", my_name)
        reactor.callLater(
            simulaqron_settings.conn_retry_time,
            connect_to_virt_node,
            my_name,
            netqasm_factory,
            virtual_network,
        )
    except Exception as e:
        logger.error(
            "LOCAL %s: Critical error when connection to local virtual node: %s",
            my_name,
            e,
        )
        reactor.stop()


def setup_netqasm_server(my_name: str, netqasm_factory: NetQASMFactory):
    """Setup NetQASM server to handle remote on the classical communication network."""
    t_start = timer()
    while timer() - t_start < _TIMEOUT:
        try:
            logger.debug(
                "LOCAL %s: Starting local QNodeOS server, port %d.",
                my_name, netqasm_factory.host.port
            )
            my_host = netqasm_factory.host
            my_host.root = netqasm_factory
            my_host.factory = netqasm_factory
            reactor.listenTCP(my_host.port, my_host.factory)
            break
        except CannotListenError:
            logger.error(
                "LOCAL %s: NetQASM server address (%d) is already in use, trying again.",
                my_name, my_host.port
            )
            time.sleep(_RETRY_TIME)
        except Exception as e:
            logger.error(
                "LOCAL %s: Critical error when starting NetQASM server: %s", my_name, e
            )
            reactor.stop()
    else:
        reactor.stop()


def sigterm_handler(_signo, _stack_frame):
    reactor.stop()


def main(node_name: str, network_name="default", log_level="WARNING"):
    """Start the indicated backend NetQASM Server"""
    set_log_level(log_level)
    logger.debug("Starting QNodeOS at %s", node_name)
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    # Since version 3.0.0 a single config file is used
    network_config_file = simulaqron_settings.network_config_file

    # Read configuration files for the virtual quantum, as well as the classical network
    virtual_network = SocketsConfig(network_config_file, network_name=network_name, config_type="vnode")
    qnodeos_network = SocketsConfig(network_config_file, network_name=network_name, config_type="qnodeos")

    # Check if we are in the host-dictionary
    if node_name in qnodeos_network.hostDict:
        node_host_info = qnodeos_network.hostDict[node_name]
        logger.debug("Setting up QNodeOS protocol factory for %s", node_name)
        netqasm_factory = NetQASMFactory(
            node_host_info,
            node_name,
            qnodeos_network,
            SubroutineHandler,
            network_name=network_name,
        )
    else:
        logger.error("LOCAL %s: Cannot start classical communication servers.", node_name)
        return

    # Connect to the local virtual node simulating the "local" qubits
    logger.debug(f"Connect to virtual node {node_name}")
    connect_to_virt_node(node_name, netqasm_factory, virtual_network)

    # Run reactor
    reactor.run()
    logger.debug(f"Ending QNodeOS at {node_name}")


if __name__ == '__main__':
    main(sys.argv[1])

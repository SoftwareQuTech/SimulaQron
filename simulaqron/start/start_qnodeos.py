import os
import signal
import sys
import time
from timeit import default_timer as timer

import logging
from twisted.internet.error import ConnectionRefusedError, CannotListenError
from twisted.spread import pb
from pathlib import Path

from simulaqron.reactor import reactor
from simulaqron.netqasm_backend.factory import NetQASMFactory
from simulaqron.netqasm_backend.qnodeos import SubroutineHandler
from simulaqron.general.host_config import SocketsConfig
from simulaqron.settings import simulaqron_settings, network_config

logger = logging.getLogger("start_qnodeos")

_RETRY_TIME = 0.1
_TIMEOUT = 10


def _init_register(virt_root, my_name: str, node: NetQASMFactory):
    """Retrieves the relevant root objects to talk to such remote connections"""
    logger.debug("START_QNODEOS %s: Connection to local virtual node successful", my_name)
    # Set the virtual node
    node.set_virtual_node(virt_root)
    # Start listening to NetQASM messages
    _setup_netqasm_server(my_name, node)


def _connect_to_virt_node(my_name: str, netqasm_factory: NetQASMFactory, virtual_network: SocketsConfig, attempt: int = 0):
    """Tries to connect to local virtual node.

    If connection is refused, we try again after a set amount of time
    (specified in handle_connection_error)
    """
    virtual_node = virtual_network.hostDict[my_name]
    logger.debug(
        "START_QNODEOS %s: Trying to connect to local virtual node at %s, %d.",
        my_name, virtual_node.hostname, virtual_node.port
    )
    factory = pb.PBClientFactory()
    # Connect
    reactor.connectTCP(virtual_node.hostname, virtual_node.port, factory)
    defer_virtual_node = factory.getRootObject()
    # If connection succeeds do:
    defer_virtual_node.addCallback(_init_register, my_name, netqasm_factory)
    # If connection fails do:
    defer_virtual_node.addErrback(_handle_connection_error, my_name, netqasm_factory, virtual_network,
                                  virtual_node.hostname, virtual_node.port, attempt)


def _handle_connection_error(reason, my_name: str, netqasm_factory: NetQASMFactory, virtual_network: SocketsConfig,
                             virtual_node_hostname: str, virtual_node_port: int, attempt: int):
    """ Handles errors from trying to connect to local virtual node.

    If a ConnectionRefusedError is raised another try will be made after
    Settings.CONF_WAIT_TIME seconds. Any other error is raised again.
    """
    try:
        reason.raiseException()
    except Exception as err:
        if attempt > simulaqron_settings.conn_max_retries:
            logger.exception(
                "START_QNODEOS %s: Exhausted the maximum number of attempts to connect to local virtual node",
                my_name,
                exc_info=err,
            )
            reactor.stop()
            return
        else:
            logger.debug("START_QNODEOS %s: Could not connect to Virtual node (%s, %d), trying again...", my_name,
                         virtual_node_hostname, virtual_node_port, exc_info=err)
            reactor.callLater(
                simulaqron_settings.conn_retry_time,
                _connect_to_virt_node,
                my_name,
                netqasm_factory,
                virtual_network,
                attempt + 1
            )


def _setup_netqasm_server(my_name: str, netqasm_factory: NetQASMFactory):
    """Setup NetQASM server to handle remote on the classical communication network."""
    t_start = timer()
    while timer() - t_start < _TIMEOUT:
        try:
            logger.debug(
                "START_QNODEOS %s: Starting local QNodeOS server, port %d.",
                my_name, netqasm_factory.host.port
            )
            my_host = netqasm_factory.host
            my_host.root = netqasm_factory
            my_host.factory = netqasm_factory
            reactor.listenTCP(my_host.port, my_host.factory)
            break
        except CannotListenError:
            logger.error(
                "START_QNODEOS: %s: NetQASM server address (%d) is already in use, trying again.",
                my_name, my_host.port
            )
            time.sleep(_RETRY_TIME)
        except Exception as e:
            logger.error(
                "START_QNODEOS %s: Critical error when starting NetQASM server: %s", my_name, e
            )
            reactor.stop()
    else:
        reactor.stop()


stdout_file = None


def _sigterm_handler(_signo, _stack_frame):
    if stdout_file is not None:
        stdout_file.flush()
        stdout_file.close()
    reactor.stop()


def start_qnodeos(node_name: str, network_config_file: Path, network_name: str):
    """
    Start the QNPU that accepts NetQASM subroutines, and sends them as instructions to the SimulaQron virtual node
    backend over twisted PB (Native Mode SimulaQron).
    
    :param node_name: Name of the node (e.g., 'Alice').
    :type node_name: str
    :param network_config_file: Path to network config file.
    :type network_config_file: Path
    :param network_name: Name of the network (e.g., 'default').
    :type network_name: str
    """

    # Let's ensure we read the config file
    network_config.read_from_file(network_config_file)

    if simulaqron_settings.log_level == logging.DEBUG:
        global stdout_file
        stdout_file = open(f"/tmp/simulaqron-stdout-stderr-qnos-{node_name}-{os.getpid()}.out.txt", "w")
        sys.stdout = stdout_file
        sys.stderr = stdout_file

    # Force configure root logger with a handler
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(name)s:%(filename)s:%(lineno)d:%(message)s",
        level=simulaqron_settings.log_level,
        force=True,
        stream=stdout_file  # send logs to the same file
    )

    """Start the indicated backend NetQASM Server"""
    logger.debug("START_QNODEOS: Starting QNodeOS at %s", node_name)
    signal.signal(signal.SIGTERM, _sigterm_handler)
    signal.signal(signal.SIGINT, _sigterm_handler)

    # Read configuration files for the virtual quantum, as well as the classical network
    virtual_network = SocketsConfig(network_config, network_name=network_name, config_type="vnode")
    qnodeos_network = SocketsConfig(network_config, network_name=network_name, config_type="qnodeos")

    # Check if we are in the host-dictionary
    if node_name in qnodeos_network.hostDict:
        node_host_info = qnodeos_network.hostDict[node_name]
        logger.debug("START_QNODEOS: Setting up QNodeOS protocol factory for %s", node_name)
        netqasm_factory = NetQASMFactory(
            node_host_info,
            node_name,
            qnodeos_network,
            SubroutineHandler,
            network_name=network_name,
        )
    else:
        logger.error("START_QNODEOS %s: Cannot start classical communication servers.", node_name)
        return

    # Connect to the local virtual node simulating the "local" qubits
    logger.debug(f"START_QNODEOS: Connect to virtual node {node_name}")
    _connect_to_virt_node(node_name, netqasm_factory, virtual_network)

    # Run reactor
    reactor.run()
    logger.debug(f"START_QNODEOS: Ending QNodeOS at {node_name}")

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
import os
import signal
import sys
from functools import partial
from pathlib import Path
from typing import List

from simulaqron.general.constants import SIMULAQRON_LOGS_FOLDER
from simulaqron.reactor import reactor
from simulaqron.virtual_node.virtual import Backend
from simulaqron.settings import simulaqron_settings
from simulaqron.settings import network_config

logger = logging.getLogger("start_vnode")

log_file = None


def _sigterm_handler(name, _signo, _stack_frame):
    print(f"START_VNODE: Shutting down Node '{name}' from signal {_signo}.", flush=True)
    if log_file is not None:
        log_file.flush()
        log_file.close()
    reactor.stop()


def start_vnode(name: str, network_config_file: Path, network_name: str, nodes_running: List[str]):
    """
    Start the execution of a virtual simulaqron node. This node will simulate all quantum aspects
    of the node, and is then reachable via Twisted PB (Simulaqron Native Mode) or - when also starting QNPU - 
    the QNPU Server which translates NetQASM to native mode. 

    :param name: Name of the node (e.g., 'Alice').
    :type name: str
    :param network_config_file: Path to network config file.
    :type network_config_file: Path
    :param network_name: Name of the network (e.g., 'default').
    :type network_name: str
    :param nodes_running: List of nodes running (e.g., ['Alice', 'Bob']).
    :type nodes_running: List[str]
    """
    global log_file

    # Let's ensure we have read the config file. This relies on the right one being passed from network.py
    network_config.read_from_file(network_config_file)

    # We will have our logging output be written to a file in order to not distract from the app
    # logging that the user will later see on the screen
    vnode_log = SIMULAQRON_LOGS_FOLDER / f"simulaqron-vnode-{name}-{os.getpid()}.log"
    log_file = open(vnode_log, "w")
    sys.stdout = log_file
    sys.stderr = log_file
    
    # Force configure root logger with a handler, ensure our log output to this file
    # will allow us to trace back exactly where it came from in the codebase
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(name)s:%(filename)s:%(lineno)d:%(message)s",
        level=simulaqron_settings.log_level,
        force=True,
        stream=log_file if log_file is not None else sys.stdout
    )
    
    # Set up the handlers: those define what we will do when the process is terminated (by killing it)
    signal.signal(signal.SIGTERM, partial(_sigterm_handler, name))
    signal.signal(signal.SIGINT, partial(_sigterm_handler, name))

    # Let's now test logging works by printing a message we are starting
    logger.debug("START_VNODE: Starting VIRTUAL NODE %s", name)

    # Start the backend with the parameters configured in the simulaqron log file
    be = Backend(name, nodes_running, network_name=network_name)
    be.start(max_qubits=simulaqron_settings.max_qubits, max_registers=simulaqron_settings.max_registers)

    # Print a message we have terminated the node.
    logger.debug("START_VNODE: Ending VIRTUAL NODE %s", name)

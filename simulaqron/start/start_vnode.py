#!/usr/bin/env python
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

import sys
import signal
from functools import partial
from twisted.internet import reactor

from netqasm.logging.glob import get_netqasm_logger, set_log_level
from simulaqron.virtual_node.virtual import Backend
from simulaqron.settings import simulaqron_settings

logger = get_netqasm_logger("start_vnode")


def sigterm_handler(name, _signo, _stack_frame):
    logger.info("Shutting down Node")
    reactor.stop()


def main(name, network_name="default", log_level="WARNING"):
    set_log_level(log_level)
    signal.signal(signal.SIGTERM, partial(sigterm_handler, name))
    signal.signal(signal.SIGINT, partial(sigterm_handler, name))

    logger.debug("Starting VIRTUAL NODE %s", name)
    if simulaqron_settings.network_config_file is not None:
        virtualFile = simulaqron_settings.network_config_file
    else:
        virtualFile = simulaqron_settings.vnode_file
    be = Backend(name, virtualFile, network_name=network_name)
    be.start(maxQubits=simulaqron_settings.max_qubits, maxRegisters=simulaqron_settings.max_registers)
    logger.debug("Ending VIRTUAL NODE %s", name)


if __name__ == "__main__":
    main(sys.argv[1])

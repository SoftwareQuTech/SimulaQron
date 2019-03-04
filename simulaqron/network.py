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
# THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import json
import time
import logging
import multiprocessing as mp
from timeit import default_timer as timer

from simulaqron.toolbox import get_simulaqron_path
from simulaqron.settings import Settings
from simulaqron.general.hostConfig import load_node_names
from simulaqron.configFiles import construct_node_configs, construct_topology_config
from simulaqron.run.startNode import main as start_node
from simulaqron.run.startCQC import main as start_cqc
from cqc.pythonLib import CQCConnection

#########################################################################################
# Network class, sets up (part of) a simulated network.                                 #
# The processes consisting of the network are killed when the object goes out of scope. #
#########################################################################################


class Network:
    def __init__(self, nodes=None, topology=None):
        simulaqron_path = get_simulaqron_path.main()

        # Set the nodes
        if nodes is None:
            node_config_file = os.path.join(simulaqron_path, "config", "Nodes.cfg")
            self.nodes = load_node_names(node_config_file)
        else:
            self.nodes = nodes
            construct_node_configs(nodes=nodes)

        # Set the topology
        if topology is None:
            rel_topology_config_file = Settings.CONF_TOPOLOGY_FILE
            if rel_topology_config_file == '':
                self.topology = None
            else:
                abs_topology_config_file = os.path.join(simulaqron_path, rel_topology_config_file)
                with open(abs_topology_config_file, 'r') as f:
                    self.topology = json.load(f)
        else:
            self.topology = topology
            construct_topology_config(topology=self.topology, nodes=self.nodes)

        self.processes = []
        self._setup_processes()

        self._running = False

    @property
    def running(self):
        for node in self.nodes:
            try:
                cqc = CQCConnection(node, retry_connection=False)
            except ConnectionRefusedError:
                self._running = False
                break
            else:
                cqc.close()
        else:
            self._running = True

        return self._running

    def __del__(self):
        self.stop()

    def _setup_processes(self):
        mp.set_start_method("spawn", force=True)
        for node in self.nodes:
            process_virtual = mp.Process(
                target=start_node, args=(node,), name="VirtNode {}".format(node)
            )
            process_cqc = mp.Process(
                target=start_cqc, args=(node,), name="CQCNode {}".format(node)
            )
            self.processes += [process_virtual, process_cqc]

    def start(self, wait_until_running=True):
        for p in self.processes:
            if not p.is_alive():
                logging.info("Starting process {}".format(p.name))
                p.start()

        if wait_until_running:
            max_time = 10  # s
            t_start = timer()
            while timer() < t_start + max_time:
                if self.running:
                    break
                else:
                    time.sleep(0.1)

    def stop(self):
        if not self._running:
            return

        self._running = False
        logging.info("Stopping network")
        for p in self.processes:
            while p.is_alive():
                time.sleep(0.1)
                try:
                    p.terminate()
                except Exception as err:
                    print(err)

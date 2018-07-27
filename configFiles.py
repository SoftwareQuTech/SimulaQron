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

# INFO:
# This file can be used to configure the nodes used in the simulation of SimulaQron.
# To setup a network with the nodes Alice, Bob and Charlie, simply type 'python configFiles.py Alice Bob Charlie'.
# This will make changes to the files 'config/{virtual,cqc,app}Nodes.cfg' and 'run/start{V,CQC}Nodes.sh'.
# Port numbers will start at 8801 and depend on the number of nodes used.

import sys
import os

# Get inputs from terminal
nodes = sys.argv[1:]
nrNodes = len(nodes)

# Get path from environment variable
netsim_path = os.environ['NETSIM'] + '/'

# Get path to configuration files
conf_files = [netsim_path + "config/virtualNodes.cfg",
				netsim_path + "config/cqcNodes.cfg",
				netsim_path + "config/appNodes.cfg",
				netsim_path + "config/classicalNet.cfg"]

# Get path to run files
run_files = [netsim_path + "run/startVNodes.sh", netsim_path + "run/startCQCNodes.sh"]

# File for just a simple list of the nodes
node_file = netsim_path + "config/Nodes.cfg"
# What port numbers to start with
start_nr = [8801, 8801 + nrNodes, 8801 + 2 * nrNodes, 8801 + 3 * nrNodes]

# Start of the configuration files
conf_top = ["# Network configuration file", "#",
			"# For each host its informal name, as well as its location in the network must", "# be listed.", "#",
			"# [name], [hostname], [port number]", "#"]

# run_top=["","# start the nodes {}".format(nodes),""]

# Write to the configuration files
for i in range(len(conf_files)):
	with open(conf_files[i], 'w') as f:
		for line in conf_top:
			f.write(line + "\n")
		for j in range(nrNodes):
			f.write("{}, localhost, {}\n".format(nodes[j], start_nr[i] + j))

with open(node_file, 'w') as f:
	for j in range(nrNodes):
		f.write("{}\n".format(nodes[j]))

# # Write to the virtual nodes run file
# with open(run_files[0],'w') as f:
# 	f.write("\n")
# 	f.write("# start the nodes {}\n".format(nodes))
# 	f.write("\n")
# 	f.write("cd \"$NETSIM\"/run\n")
# 	f.write("\n")
# 	for j in range(nrNodes):
# 		f.write("python startNode.py {} &\n".format(nodes[j]))
#
# # Write to the CQC nodes run file
# with open(run_files[1],'w') as f:
# 	f.write("\n")
# 	f.write("# start the nodes {}\n".format(nodes))
# 	f.write("\n")
# 	f.write("cd \"$NETSIM\"/run\n")
# 	f.write("\n")
# 	for j in range(nrNodes):
# 		f.write("python startCQC.py {} &\n".format(nodes[j]))

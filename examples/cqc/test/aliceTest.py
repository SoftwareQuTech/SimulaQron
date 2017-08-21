#
# Copyright (c) 2017, Stephanie Wehner
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

import socket
import sys
import os
import struct
import logging

from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *
from SimulaQron.cqc.pythonLib.cqc import *


#####################################################################################################
#
# init
#
def init(name,cqcFile=None):
	"""
	Initialize a connection to the cqc server with the name given as input.
	A path to a configure file for the cqc network can be given,
	if it's not given the config file '$NETSIM/config/cqcNodes.cfg' will be used.
	Returns a socket object.
	"""

	# This file defines the network of CQC servers interfacing to virtual quantum nodes
	if cqcFile==None:
		cqcFile = os.environ.get('NETSIM') + "/config/cqcNodes.cfg"

	# Read configuration files for the cqc network
	cqcNet = networkConfig(cqcFile)

	# Host data
	if name in cqcNet.hostDict:
		myHost = cqcNet.hostDict[name]
	else:
		logging.error("The name '%s' is not in the cqc network.",name)

	#Get IP of correct form
	myIP=socket.inet_ntoa(struct.pack("!L",myHost.ip))

	#Connect to cqc server and run protocol
	cqc=None
	try:
		cqc=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
	except socket.error:
		logging.error("Could not connect to cqc server: %s",name)
	try:
		cqc.connect((myIP,myHost.port))
	except socket.error:
		cqc.close()
		logging.error("Could not connect to cqc server: %s",name)
	return cqc


#####################################################################################################
#
# main
#
def main():

	# In this example, we are Alice.
	myName="Alice"

	# Initialize the connection
	cqc=init(myName)

	#Create qubit
	hdr=CQCHeader()
	hdr.setVals(CQC_VERSION,CQC_TP_COMMAND,0,CQC_CMD_HDR_LENGTH)
	msg=hdr.pack()
	cqc.send(msg)

	#Command Header
	qid=0
	cmd_hdr=CQCCmdHeader()
	cmd_hdr.setVals(qid,CQC_CMD_NEW,0,0,0)
	cmd_msg=cmd_hdr.pack()
	cqc.send(cmd_msg)

	data=cqc.recv(1024) #WHAT IS A GOOD MAXSIZE?
	hdr=CQCHeader(data)
	print(hdr.printable())

	#Perform Hadamard
	hdr=CQCHeader()
	hdr.setVals(CQC_VERSION,CQC_TP_COMMAND,0,CQC_CMD_HDR_LENGTH)
	msg=hdr.pack()
	cqc.send(msg)

	#Command Header
	cmd_hdr=CQCCmdHeader()
	cmd_hdr.setVals(qid,CQC_CMD_H,0,0,0)
	cmd_msg=cmd_hdr.pack()
	cqc.send(cmd_msg)

	data=cqc.recv(1024) #WHAT IS A GOOD MAXSIZE?
	hdr=CQCHeader(data)
	print(hdr.printable())
	cqc.close()


##################################################################################################
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)
main()


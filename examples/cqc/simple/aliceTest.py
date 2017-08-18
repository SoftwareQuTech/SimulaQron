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

import os

from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *

from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

#####################################################################################################
#
# protocol
#

class Greeter(Protocol):
	def sendMessage(self,msg):
		self.transport.write(msg)

	def dataReceived(self,data):
		hdr=CQCHeader(data)
		print(hdr.printable())

def gotProtocol(p):
	hdr=CQCHeader()
	hdr.setVals(CQC_VERSION,CQC_TP_HELLO,0,0)
	msg=hdr.pack()
	p.sendMessage(msg)

def getHostData(name):

	# Config file for cqc layer
	cqcFileName=os.environ.get('NETSIM') + "/config/cqcNodes.cfg"

	# Find port of name
	with open(cqcFileName) as cqcFile:
		for line in cqcFile:
			if not line.startswith("#"):
				words=line.split(',')
				tmpName=words[0].strip()
				if tmpName==name:
					hostType=words[1].strip()
					port=words[2].strip()
					return (hostType,int(port))
	raise ValueError("No such host-name")

#####################################################################################################
#
# main
#
def main():

	# In this example, we are Alice.
	myName="Alice"

	# Get the hostType and port of Alice cqc server
	(hostType,port)=getHostData(myName)

	#Connect to cqc server and run protocol
	point=TCP4ClientEndpoint(reactor,hostType,port)
	d=connectProtocol(point,Greeter())
	d.addCallback(gotProtocol)
	reactor.run()

##################################################################################################
# logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)
main()


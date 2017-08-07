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


import sys, os
sys.path.insert(0, os.environ.get('NETSIM'))

from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList, Deferred

from SimulaQron.virtNode.basics import *
from SimulaQron.virtNode.quantum import *
from SimulaQron.general.hostConfig import *
from SimulaQron.virtNode.crudeSimulator import *

from SimulaQron.local.setup import *

#####################################################################################################
#
# CQC Factory
#
# Twisted factory for the CQC protocol
#

class CQCFactory(Factory):
	
	def __init__(self, host):
		''' 
		Initialize CQC Factory. 

		lhost	details of the local host (class host)
		'''

		self.host = host	
		self.virtRoot = None
		self.qReg = None

	def buildProtocol(self, addr):
		'''
		Return an instance of CQCProtocol when a connection is made.
		'''
		return CQCProtocol(self)

	def set_virtual_node(self, virtRoot):
		'''
		Set the virtual root allowing connections to the SimulaQron backend.
		'''
		self.virtRoot = virtRoot

	def set_virtual_reg(self, qReg):
		'''
		Set the default register to use on the SimulaQron backend.
		'''
		self.qReg = qReg


#####################################################################################################
#
# CQC Protocol 
#
# Execute the CQC Protocol giving access to the SimulaQron backend via the universal interface.
#

class CQCProtocol(Protocol):

	def __init__(self, factory):
		self.factory = factory

	def connectionMade(self):
		pass

	def connectionLost(self, reason):
		pass

	def dataReceived(self, data):
		self.transport.write(data)
		


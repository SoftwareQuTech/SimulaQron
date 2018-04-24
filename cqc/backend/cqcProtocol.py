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


from SimulaQron.cqc.backend.cqcMessageHandler import *
from settings import Settings
from twisted.internet.defer import DeferredLock
from twisted.internet.protocol import Factory, Protocol


#####################################################################################################
#
# CQC Factory
#
# Twisted factory for the CQC protocol
#


class CQCFactory(Factory):

	def __init__(self, host, name, cqc_net):
		"""
		Initialize CQC Factory.

		lhost	details of the local host (class host)
		"""

		self.host = host
		self.name = name
		self.cqcNet = cqc_net
		self.virtRoot = None
		self.qReg = None

		# Dictionary that keeps qubit dictorionaries for each application
		self.qubitList = {}

		# Lock governing access to the qubitList
		self._lock = DeferredLock()

	def buildProtocol(self, addr):
		"""
		Return an instance of CQCProtocol when a connection is made.
		"""
		return CQCProtocol(self)

	def set_virtual_node(self, virtRoot):
		"""
		Set the virtual root allowing connections to the SimulaQron backend.
		"""
		self.virtRoot = virtRoot

	def set_virtual_reg(self, qReg):
		"""
		Set the default register to use on the SimulaQron backend.
		"""
		self.qReg = qReg

	def lookup(self, ip, port):
		"""
		Lookup name of remote host used within SimulaQron given ip and portnumber.
		"""
		for entry in self.cqcNet.hostDict:
			node = self.cqcNet.hostDict[entry]
			if (node.ip == ip) and (node.port == port):
				return node.name

		logging.debug("CQC %s: No such node", self.name)
		return None


#####################################################################################################
#
# CQC Protocol
#
# Execute the CQC Protocol giving access to the SimulaQron backend via the universal interface.
#

class CQCProtocol(Protocol):
	# Dictionary storing the next unique qubit id for each used app_id
	_next_q_id = {}

	# Dictionary storing the next unique entanglement id for each used (host_app_id,remote_node,remote_app_id)
	_next_ent_id = {}

	def __init__(self, factory):

		# CQC Factory, including our connection to the SimulaQron backend
		self.factory = factory

		# Default application ID, typically one connection per application but we will
		# deliberately NOT check for that since this is the task of higher layers or an OS
		self.app_id = 0

		# Define the backend to use. Is a setting in settings.ini
		backend = Settings.CONF_BACKEND_HANDLER
		self.messageHandler = backend(factory)

		# Flag to determine whether we already received _all_ of the CQC header
		self.gotCQCHeader = False

		# Header for which we are currently processing a packet
		self.currHeader = None

		# Buffer received data (which may arrive in chunks)
		self.buf = None

		# Convenience
		self.name = self.factory.name

		logging.debug("CQC %s: Initialized Protocol", self.name)

	def connectionMade(self):
		pass

	def connectionLost(self, reason):
		pass

	def dataReceived(self, data):
		"""
		Receive data. We will always wait to receive enough data for the header,
		and then the entire packet first before commencing processing.
		"""
		# Read whatever we received into a buffer
		if self.buf:
			self.buf = self.buf + data
		else:
			self.buf = data

		# If we don't have the CQC header yet, try and read it in full.
		if not self.gotCQCHeader:
			if len(self.buf) < CQC_HDR_LENGTH:
				# Not enough data for CQC header, return and wait for the rest
				return

			# Got enough data for the CQC Header so read it in
			self.gotCQCHeader = True
			rawHeader = self.buf[0:CQC_HDR_LENGTH]
			self.currHeader = CQCHeader(rawHeader)

			# Remove the header from the buffer
			self.buf = self.buf[CQC_HDR_LENGTH:len(self.buf)]

			logging.debug("CQC %s: Read CQC Header: %s", self.name, self.currHeader.printable())

		# Check whether we already received all the data
		if len(self.buf) < self.currHeader.length:
			# Still waiting for data
			logging.debug("CQC %s: Incomplete data. Waiting. Current length %s, required length %s", self.name,
						  len(self.buf), self.currHeader.length)
			return

		# We got the header and all the data for this packet. Start processing.
		# Update our app ID
		self.app_id = self.currHeader.app_id
		# Invoke the relevant message handler, processing the possibly remaining data
		try:
			self._parseData(self.currHeader, self.buf[0:self.currHeader.length])
		except Exception as e:
			print(e)
			import traceback
			traceback.print_exc()

		# if self.currHeader.tp in self.messageHandlers:
		# 	self.messageHandlers[self.currHeader.tp](self.currHeader, )
		# else:
		# 	self._send_back_cqc(self.currHeader, CQC_ERR_UNSUPP)

		# Reset and await the next packet
		self.gotCQCHeader = False

		# Check if we received data already for the next packet, if so save it
		if self.currHeader.length < len(self.buf):
			self.buf = self.buf[self.currHeader.length:len(self.buf)]
			self.dataReceived(b'')
		else:
			self.buf = None

	@inlineCallbacks
	def _parseData(self, header, data):
		messages = yield self.messageHandler.handle_cqc_message(header, data)
		if messages:
			# self.factory._lock.acquire()
			for msg in messages:
				self.transport.write(msg)
		# self.factory._lock.release()

	def _send_back_cqc(self, header, msgType, length=0):
		"""
		Return a simple CQC header with the specified type.

		header	 CQC header of the packet we respond to
		msgType  Message type to return
		length	 Length of additional message
		"""
		hdr = CQCHeader()
		hdr.setVals(CQC_VERSION, msgType, header.app_id, length)

		msg = hdr.pack()
		self.transport.write(msg)

	def new_qubit_id(self, app_id):

		"""
		Returns a new unique qubit id for the specified app_id. Used by cmd_new and cmd_recv
		"""
		if app_id in CQCProtocol._next_q_id:
			q_id = CQCProtocol._next_q_id[app_id]
			CQCProtocol._next_q_id[app_id] += 1
			return q_id
		else:
			"""
			Returns a new unique qubit id for the specified app_id. Used by cmd_new and cmd_recv
			"""
			if app_id in CQCProtocol._next_q_id:
				q_id = CQCProtocol._next_q_id[app_id]
				CQCProtocol._next_q_id[app_id] += 1
				return q_id
			else:
				CQCProtocol._next_q_id[app_id] = 1
				return 0

	def new_ent_id(self, host_app_id, remote_node, remote_app_id):
		"""
		Returns a new unique entanglement id for the specified host_app_id, remote_node and remote_app_id. Used by cmd_epr.
		"""
		pair_id = (host_app_id, remote_node, remote_app_id)
		if pair_id in CQCProtocol._next_ent_id:
			ent_id = CQCProtocol._next_ent_id[pair_id]
			CQCProtocol._next_ent_id[pair_id] += 1
			return ent_id
		else:
			CQCProtocol._next_ent_id[pair_id] = 1
			return 0

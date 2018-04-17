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

import socket, struct, os, sys, time, math

from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *
from SimulaQron.cqc.backend.entInfoHeader import *


def shouldReturn(command):
	return command in {CQC_CMD_NEW, CQC_CMD_MEASURE, CQC_CMD_MEASURE_INPLACE, CQC_CMD_RECV, CQC_CMD_EPR_RECV,
					   CQC_CMD_EPR}


def hasXtraHeader(command):
	return command in {CQC_CMD_CNOT, CQC_CMD_SEND, CQC_CMD_EPR, CQC_CMD_ROT_X, CQC_CMD_ROT_Y, CQC_CMD_ROT_Z,
					   CQC_CMD_CPHASE}


def createXtraHeader(command, values):
	if command == CQC_CMD_SEND or command == CQC_CMD_EPR:
		header = CQCCommunicationHeader()
		header.setVals(values[0], values[1], values[2])
	elif command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
		header = CQCXtraQubitHeader()
		header.setVals(values)
	elif command == CQC_CMD_ROT_Z or command == CQC_CMD_ROT_Y or command == CQC_CMD_ROT_X:
		header = CQCRotationHeader()
		header.setVals(values)
	else:
		header = None
	return header


class CQCConnection:
	_appIDs = []

	def __init__(self, name, cqcFile=None, appFile=None, appID=0, pend_messages=False):
		"""
		Initialize a connection to the cqc server.

		- **Arguments**
			:name:		Name of the host.
			:cqcFile:	Path to cqcFile. If None, '$NETSIM/config/cqcNodes.cfg is used.
			:appFile:	Path to appFile. If None, '$NETSIM/config/appNodes.cfg is used.
			:appID:		Application ID, defaults to a nonused ID.
			:pend_messages: True if you want to wait with sending messages to the back end.
					Use flush() to send all pending messages in one go as a sequence to the server
		"""

		# Host name
		self.name = name

		# Which appID
		if appID in self._appIDs:
			raise ValueError("appID={} is already in use".format(appID))
		self._appID = appID
		self._appIDs.append(self._appID)

		# Buffer received data
		self.buf = None

		# ClassicalServer
		self._classicalServer = None

		# Classical connections in the application network
		self._classicalConn = {}

		# This file defines the network of CQC servers interfacing to virtual quantum nodes
		if cqcFile == None:
			self.cqcFile = os.environ.get('NETSIM') + "/config/cqcNodes.cfg"

		# Read configuration files for the cqc network
		self._cqcNet = networkConfig(self.cqcFile)

		# Host data
		if self.name in self._cqcNet.hostDict:
			myHost = self._cqcNet.hostDict[self.name]
		else:
			raise ValueError("Host name '{}' is not in the cqc network".format(name))

		# Get IP of correct form
		myIP = socket.inet_ntoa(struct.pack("!L", myHost.ip))

		# Connect to cqc server
		self._s = None
		try:
			self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
		except socket.error:
			raise RuntimeError("Could not connect to cqc server '{}'".format(name))
		try:
			self._s.connect((myIP, myHost.port))
		except socket.error:
			self._s.close()
			raise RuntimeError("Could not connect to cqc server '{}'".format(name))

		# This file defines the application network
		if appFile == None:
			self.appFile = os.environ.get('NETSIM') + "/config/appNodes.cfg"

		# Read configuration files for the application network
		self._appNet = networkConfig(self.appFile)

		# List of pending messages waiting to be send to the back-end
		self.pend_messages = pend_messages
		self.pending_messages = []

	def __str__(self):
		return "Socket to cqc server '{}'".format(self.name)

	def get_appID(self):
		"""
		Returns the application ID.
		"""
		return self._appID

	def close(self):
		"""
		Closes the connection.
		"""
		self._s.close()
		self._appIDs.remove(self._appID)

		self.closeClassicalServer()

		for name in list(self._classicalConn):
			self.closeClassicalChannel(name)

	def startClassicalServer(self):
		"""
		Sets up a server for the application communication, if not already set up.
		"""

		if not self._classicalServer:
			# Get host data
			myHost = self._appNet.hostDict[self.name]

			# Setup server
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind((myHost.hostname, myHost.port))
			s.listen(1)
			(conn, addr) = s.accept()
			self._classicalServer = conn

	def closeClassicalServer(self):
		if self._classicalServer:
			self._classicalServer.close()
			self._classicalServer = None

	def recvClassical(self, timout=1, msg_size=1024):
		if not self._classicalServer:
			self.startClassicalServer()
		for _ in range(10 * timout):
			msg = self._classicalServer.recv(msg_size)
			if len(msg) > 0:
				return msg
			time.sleep(0.1)

	def openClassicalChannel(self, name, timout=1):
		"""
		Opens a classical connection to another host in the application network.

		- **Arguments**

			:name:		The name of the host in the application network.
			:timout:	The time to try to connect to the server. When timout is reached an RuntimeError is raised.
		"""
		if name not in self._classicalConn:
			if name in self._appNet.hostDict:
				remoteHost = self._appNet.hostDict[name]
			else:
				raise ValueError("Host name '{}' is not in the cqc network".format(name))
			connected = False
			for _ in range(int(10 * timout)):
				try:
					s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					s.connect((remoteHost.hostname, remoteHost.port))
					connected = True
					break
				except:
					time.sleep(0.1)
			if not connected:
				raise RuntimeError("Could not connect to server {}".format(name))
			self._classicalConn[name] = s

	def closeClassicalChannel(self, name):
		"""
		Closes a classical connection to another host in the application network.

		- **Arguments**

			:name:		The name of the host in the application network.
		"""
		if name in self._classicalConn:
			s = self._classicalConn.pop(name)
			s.close()

	def sendClassical(self, name, msg, timout=1):
		"""
		Sends a classical message to another host in the application network.

		- **Arguments**

			:name:		The name of the host in the application network.
			:msg:		The message to send. Should be either a int in range(0,256) or a list of such ints.
			:timout:	The time to try to connect to the server. When timout is reached an RuntimeError is raised.
		"""
		if name not in self._classicalConn:
			self.openClassicalChannel(name)
		try:
			to_send = [int(msg)]
		except:
			to_send = msg
		self._classicalConn[name].send(bytes(to_send))

	def sendSimple(self, tp):
		"""
		Sends a simple message to the cqc server, for example a HELLO message if tp=CQC_TP_HELLO.
		"""
		hdr = CQCHeader()
		hdr.setVals(CQC_VERSION, tp, self._appID, 0)
		msg = hdr.pack()
		self._s.send(msg)

	def sendCommand(self, qID, command, notify=1, block=1, action=0):
		"""
		Sends a simple message and command message to the cqc server.

		- **Arguments**

			:qID:		qubit ID
			:command:	Command to be executed, eg CQC_CMD_H
			:nofify:	Do we wish to be notified when done.
			:block:		Do we want the qubit to be blocked
			:action:	Are there more commands to be executed
		"""
		# Send Header
		hdr = CQCHeader()
		hdr.setVals(CQC_VERSION, CQC_TP_COMMAND, self._appID, CQC_CMD_HDR_LENGTH)
		msg = hdr.pack()
		self._s.send(msg)

		# Send Command
		cmd_hdr = CQCCmdHeader()
		cmd_hdr.setVals(qID, command, notify, block, action)
		cmd_msg = cmd_hdr.pack()
		self._s.send(cmd_msg)

	def sendCmdXtra(self, qID, command, notify=1, block=1, action=0, xtra_qID=0, step=0, remote_appID=0, remote_node=0,
					remote_port=0):
		"""
		Sends a simple message, command message and xtra message to the cqc server.

		- **Arguments**

			:qID:		 qubit ID
			:command:	 Command to be executed, eg CQC_CMD_H
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:action:	 Are there more commands to be executed
			:xtra_qID:	 Extra qubit ID for for example CNOT
			:step:		 Defines the angle of rotation.
			:remote_appID:	 Application ID of remote host
			:remote_node:	 ip of remote host in cqc network
			:remote_port:	 port of remote host in cqc network
		"""

		# Check what extra header we require
		xtra_hdr = None
		if command == CQC_CMD_SEND or command == CQC_CMD_EPR:
			xtra_hdr = CQCCommunicationHeader()
			xtra_hdr.setVals(remote_appID, remote_node, remote_port)
		elif command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
			xtra_hdr = CQCXtraQubitHeader()
			xtra_hdr.setVals(xtra_qID)
		elif command == CQC_CMD_ROT_X or command == CQC_CMD_ROT_Y or command == CQC_CMD_ROT_Z:
			xtra_hdr = CQCRotationHeader()
			xtra_hdr.setVals(step)

		if xtra_hdr is None:
			header_length = CQC_CMD_HDR_LENGTH
			xtra_msg = b''
		else:
			xtra_msg = xtra_hdr.pack()
			header_length = CQC_CMD_HDR_LENGTH + xtra_hdr.HDR_LENGTH

		# Send Header
		hdr = CQCHeader()
		hdr.setVals(CQC_VERSION, CQC_TP_COMMAND, self._appID, header_length)
		msg = hdr.pack()

		# Send Command
		cmd_hdr = CQCCmdHeader()
		cmd_hdr.setVals(qID, command, notify, block, action)
		cmd_msg = cmd_hdr.pack()

		# Send headers
		self._s.send(msg + cmd_msg + xtra_msg)

	def sendGetTime(self, qID, notify=1, block=1, action=0):
		"""
		Sends get-time message

		- **Arguments**

			:qID:		 qubit ID
			:command:	 Command to be executed, eg CQC_CMD_H
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:action:	 Are there more commands to be executed
		"""
		# Send Header
		hdr = CQCHeader()
		hdr.setVals(CQC_VERSION, CQC_TP_GET_TIME, self._appID, CQC_CMD_HDR_LENGTH)
		msg = hdr.pack()
		self._s.send(msg)

		# Send Command
		cmd_hdr = CQCCmdHeader()
		cmd_hdr.setVals(qID, 0, notify, block, action)
		cmd_msg = cmd_hdr.pack()
		self._s.send(cmd_msg)

	def sendFactory(self, qID, command, num_iter, notify=1, block=1, action=0, xtra_qID=-1, remote_appID=0,
					remote_node=0, remote_port=0, step_size=0, print_info=False):
		"""
		Sends a factory message

		- **Arguments**

			:qID:		 qubit ID
			:command:	 Command to be executed, eg CQC_CMD_H
			:num_iter:	 Number of times to execute command
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:action:	 Are there more commands to be executed
			:xtra_qID:	 Extra qubit ID for for example CNOT
			:remote_appID:	 Application ID of remote host
			:remote_node:	 ip of remote host in cqc network
			:remote_port:	 port of remote host in cqc network
			:cmd_length:	 length of extra commands
		"""
		warnings.warn("Send factory is deprecated. Use flush_factory() instead", DeprecationWarning)

		if xtra_qID == -1:
			if command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
				raise CQCUnsuppError("Please provide a target qubit")
			xtra_qID = 0

		# Check what extra header we require
		xtra_hdr = None
		if hasXtraHeader(command):
			if command == CQC_CMD_SEND or command == CQC_CMD_EPR:
				xtra_hdr = CQCCommunicationHeader()
				xtra_hdr.setVals(remote_appID, remote_node, remote_port)
			elif command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
				xtra_hdr = CQCXtraQubitHeader()
				xtra_hdr.setVals(xtra_qID)
			else:
				xtra_hdr = CQCRotationHeader()
				xtra_hdr.setVals(step_size)
			xtra_msg = xtra_hdr.pack()
			hdr_length = CQC_CMD_HDR_LENGTH + CQCFactoryHeader.HDR_LENGTH + xtra_hdr.HDR_LENGTH
		else:
			xtra_msg = b''
			hdr_length = CQC_CMD_HDR_LENGTH + CQCFactoryHeader.HDR_LENGTH

		# Send Header
		hdr = CQCHeader()
		hdr.setVals(CQC_VERSION, CQC_TP_FACTORY, self._appID, hdr_length)
		msg = hdr.pack()

		# Factory header
		factory_hdr = CQCFactoryHeader()
		factory_hdr.setVals(num_iter, notify)
		factory_msg = factory_hdr.pack()

		# Send Command
		cmd_hdr = CQCCmdHeader()
		cmd_hdr.setVals(qID, command, 0, block, action)
		cmd_msg = cmd_hdr.pack()
		if print_info:
			print("App {} sends CQC message {}".format(self.name, hdr.printable()))
			print("App {} sends CQC message {}".format(self.name, factory_hdr.printable()))

			print("App {} sends CQC message {}".format(self.name, cmd_hdr.printable()))
			if xtra_hdr:
				print("App {} sends CQC message {}".format(self.name, xtra_hdr.printable()))
		self._s.send(msg + factory_msg + cmd_msg + xtra_msg)

		# Get RECV messages
		# Some commands expect to get a list of messages back, check those
		res = []
		if shouldReturn(command):
			for _ in range(num_iter):
				message = self.readMessage()
				if message[0].tp in {CQC_TP_NEW_OK, CQC_TP_RECV, CQC_TP_EPR_OK}:
					qID = message[1].qubit_id
					q = qubit(self, createNew=False, q_id=qID, notify=notify, block=block)
					q._active = True
					res.append(q)
				elif message[0].tp == CQC_TP_MEASOUT:
					outcome = message[1].outcome
					res.append(outcome)
		if notify:
			message = self.readMessage()
			if message[0].tp != CQC_TP_DONE:
				raise CQCUnsuppError(
					"Unexpected message send back from the server. Message: {}".format(message[0].printable()))
		return res

	def readMessage(self, maxsize=192):  # WHAT IS GOOD SIZE?
		"""
		Receive the whole message from cqc server.
		Returns (CQCHeader,None,None), (CQCHeader,CQCNotifyHeader,None) or (CQCHeader,CQCNotifyHeader,EntInfoHeader)
		depending on the type of message.
		Maxsize is the max size of message.
		"""

		# Initilize checks
		gotCQCHeader = False
		if self.buf:
			checkedBuf = False
		else:
			checkedBuf = True

		while True:
			# If buf does not contain enough data, read in more
			if checkedBuf:
				# Receive data
				data = self._s.recv(maxsize)

				# Read whatever we received into a buffer
				if self.buf:
					self.buf += data
				else:
					self.buf = data

			# If we don't have the CQC header yet, try and read it in full.
			if not gotCQCHeader:
				if len(self.buf) < CQC_HDR_LENGTH:
					# Not enough data for CQC header, return and wait for the rest
					checkedBuf = True
					continue

				# Got enough data for the CQC Header so read it in
				gotCQCHeader = True
				rawHeader = self.buf[0:CQC_HDR_LENGTH]
				currHeader = CQCHeader(rawHeader)

				# Remove the header from the buffer
				self.buf = self.buf[CQC_HDR_LENGTH:len(self.buf)]

				# Check for error
				self.check_error(currHeader)

			# Check whether we already received all the data
			if len(self.buf) < currHeader.length:
				# Still waiting for data
				checkedBuf = True
				continue
			else:
				break
		# We got all the data, read notify (and ent_info) if there is any
		if currHeader.length == 0:
			return currHeader, None, None
		elif currHeader.length == CQC_NOTIFY_LENGTH:
			try:
				rawNotifyHeader = self.buf[:CQC_NOTIFY_LENGTH]
				self.buf = self.buf[CQC_NOTIFY_LENGTH:len(self.buf)]
				notifyHeader = CQCNotifyHeader(rawNotifyHeader)
				return currHeader, notifyHeader, None
			except struct.error as err:
				print(err)
		elif currHeader.length == CQC_NOTIFY_LENGTH + ENT_INFO_LENGTH:
			try:
				rawNotifyHeader = self.buf[:CQC_NOTIFY_LENGTH]
				self.buf = self.buf[CQC_NOTIFY_LENGTH:len(self.buf)]
				notifyHeader = CQCNotifyHeader(rawNotifyHeader)

				rawEntInfoHeader = self.buf[:ENT_INFO_LENGTH]
				self.buf = self.buf[ENT_INFO_LENGTH:len(self.buf)]
				entInfoHeader = EntInfoHeader(rawEntInfoHeader)

				return currHeader, notifyHeader, entInfoHeader
			except struct.error as err:
				print(err)
		else:
			print("Warning: Received message of unknown length, return None")

	def print_CQC_msg(self, message):
		"""
		Prints messsage returned by the readMessage method of CQCConnection.
		"""
		hdr = message[0]
		notifyHdr = message[1]
		entInfoHdr = message[2]

		if hdr.tp == CQC_TP_HELLO:
			print("CQC tells App {}: 'HELLO'".format(self.name))
		elif hdr.tp == CQC_TP_EXPIRE:
			print("CQC tells App {}: 'Qubit with ID {} has expired'".format(self.name, notifyHdr.qubit_id))
		elif hdr.tp == CQC_TP_DONE:
			print("CQC tells App {}: 'Done with command'".format(self.name))
		elif hdr.tp == CQC_TP_RECV:
			print("CQC tells App {}: 'Received qubit with ID {}'".format(self.name, notifyHdr.qubit_id))
		elif hdr.tp == CQC_TP_EPR_OK:

			# Lookup host name
			remote_node = entInfoHdr.node_B
			remote_port = entInfoHdr.port_B
			for node in self._cqcNet.hostDict.values():
				if (node.ip == remote_node) and (node.port == remote_port):
					remote_name = node.name
					break

			print("CQC tells App {}: 'EPR created with node {}, using qubit with ID {}'".format(self.name, remote_name,
																								notifyHdr.qubit_id))
		elif hdr.tp == CQC_TP_MEASOUT:
			print("CQC tells App {}: 'Measurement outcome is {}'".format(self.name, notifyHdr.outcome))
		elif hdr.tp == CQC_TP_INF_TIME:
			print("CQC tells App {}: 'Timestamp is {}'".format(self.name, notifyHdr.datetime))

	def parse_CQC_msg(self, message, q=None, is_factory=False):
		"""
		parses the cqc message and returns the relevant value of that measure
		(qubit, measurement outcome)
		:param message: the cqc message to be parsed
		:param q: the qubit object we should save the qubit to
		:param is_factory: wether the returned message came from a factory. If so, do not chance the qubit, but create a new one
		:return: the result of the message (either a qubit, or a measurement outcome. Otherwise None
		"""
		hdr = message[0]
		notifyHdr = message[1]
		entInfoHdr = message[2]

		if hdr.tp in {CQC_TP_RECV, CQC_TP_NEW_OK, CQC_TP_EPR_OK}:
			if is_factory:
				q._active = False  # Set qubit to inactive so it can't be used anymore
				q = qubit(self, createNew=False)
			q._qID = notifyHdr.qubit_id
			q.set_entInfo(entInfoHdr)
			q._active = True
			return q
		if hdr.tp in {CQC_TP_MEASOUT, CQC_TP_GET_TIME}:
			return notifyHdr.outcome
		if hdr.tp == CQC_TP_INF_TIME:
			return notifyHdr.datetime

	def check_error(self, hdr):
		"""
		Checks if there is an error returned.
		"""
		self._errorHandler(hdr.tp)

	def _errorHandler(self, cqc_err):
		"""
		Raises an error if there is an error-message
		"""
		if cqc_err == CQC_ERR_GENERAL:
			raise CQCGeneralError("General error")
		if cqc_err == CQC_ERR_NOQUBIT:
			raise CQCNoQubitError("Qubit not available or no more qubits available")
		if cqc_err == CQC_ERR_UNSUPP:
			raise CQCUnsuppError("Sequence not supported")
		if cqc_err == CQC_ERR_TIMEOUT:
			raise CQCTimeoutError("Timout")

	def sendQubit(self, q, name, remote_appID=0, notify=True, block=True, print_info=True):
		"""
		Sends qubit to another node in the cqc network. If this node is not in the network an error is raised.

		- **Arguments**

			:q:		 The qubit to send.
			:Name:		 Name of the node as specified in the cqc network config file.
			:remote_appID:	 The app ID of the application running on the receiving node.
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
		"""

		# Get receiving host
		hostDict = self._cqcNet.hostDict
		if name in hostDict:
			recvHost = hostDict[name]
		else:
			raise ValueError("Host name '{}' is not in the cqc network".format(name))

		if self.pend_messages:
			# print info
			if print_info:
				print("App {} pends message: 'Send qubit with ID {} to {} and appID {}'".format(self.name, q._qID, name,
																								remote_appID))
			self.pending_messages.append([q, CQC_CMD_SEND, int(notify), int(block), [remote_appID,
																					 recvHost.ip, recvHost.port]])
		else:
			# print info
			if print_info:
				print("App {} tells CQC: 'Send qubit with ID {} to {} and appID {}'".format(self.name, q._qID, name,
																							remote_appID))
			self.sendCmdXtra(q._qID, CQC_CMD_SEND, notify=int(notify), block=int(block), remote_appID=remote_appID,
							 remote_node=recvHost.ip, remote_port=recvHost.port)
			if notify:
				message = self.readMessage()
				if print_info:
					self.print_CQC_msg(message)

			# Deactivate qubit
			q._active = False

	def recvQubit(self, notify=True, block=True, print_info=True):
		"""
		Receives a qubit.

		- **Arguments**

			:q:		 The qubit to send.
			:Name:		 Name of the node as specified in the cqc network config file.
			:remote_appID:	 The app ID of the application running on the receiving node.
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""

		# initialize the qubit
		q = qubit(self, createNew=False)

		if self.pend_messages:
			# print info
			if print_info:
				print("App {} pends message: 'Receive qubit'".format(self.name))
			self.pending_messages.append([q, CQC_CMD_RECV, int(notify), int(block)])
			return q
		else:
			# print info
			if print_info:
				print("App {} tells CQC: 'Receive qubit'".format(self.name))
			self.sendCommand(0, CQC_CMD_RECV, notify=int(notify), block=int(block))

			# Get RECV message
			message = self.readMessage()
			notifyHdr = message[1]
			q_id = notifyHdr.qubit_id

			if print_info:
				self.print_CQC_msg(message)

			if notify:
				message = self.readMessage()
				if print_info:
					self.print_CQC_msg(message)

			# initialize the qubit
			q._qID = q_id

			# Activate and return qubit
			q._active = True
			return q

	def createEPR(self, name, remote_appID=0, notify=True, block=True, print_info=True):
		"""
		Creates epr with other host in cqc network.

		- **Arguments**

			:name:		 Name of the node as specified in the cqc network config file.
			:remote_appID:	 The app ID of the application running on the receiving node.
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""

		# Get receiving host
		hostDict = self._cqcNet.hostDict
		if name in hostDict:
			recvHost = hostDict[name]
		else:
			raise ValueError("Host name '{}' is not in the cqc network".format(name))

		# initialize the qubit
		q = qubit(self, createNew=False)

		if self.pend_messages:
			# print info
			if print_info:
				print("App {} pends message: 'Create EPR-pair with {} and appID {}'".format(self.name, name,
																							remote_appID))

			self.pending_messages.append(
				[q, CQC_CMD_EPR, int(notify), int(block), [remote_appID, recvHost.ip, recvHost.port]])
			return q
		else:
			# print info
			if print_info:
				print("App {} tells CQC: 'Create EPR-pair with {} and appID {}'".format(self.name, name, remote_appID))

			self.sendCmdXtra(0, CQC_CMD_EPR, notify=int(notify), block=int(block), remote_appID=remote_appID,
							 remote_node=recvHost.ip, remote_port=recvHost.port)
			# Get RECV message
			message = self.readMessage()
			notifyHdr = message[1]
			entInfoHdr = message[2]
			q_id = notifyHdr.qubit_id

			if print_info:
				self.print_CQC_msg(message)

			if notify:
				message = self.readMessage()
				if print_info:
					self.print_CQC_msg(message)

			q.set_entInfo(entInfoHdr)
			q._qID = q_id
			# Activate and return qubit
			q._active = True
			return q

	def recvEPR(self, notify=True, block=True, print_info=True):
		"""
		Receives a qubit from an EPR-pair generated with another node.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""

		# initialize the qubit
		q = qubit(self, createNew=False)
		if self.pend_messages:
			# print info
			if print_info:
				print("App {} pends message: 'Receive half of EPR'".format(self.name))
			self.pending_messages.append([q, CQC_CMD_EPR_RECV, int(notify), int(block)])
			return q
		else:
			# print info
			if print_info:
				print("App {} tells CQC: 'Receive half of EPR'".format(self.name))
			self.sendCommand(0, CQC_CMD_EPR_RECV, notify=int(notify), block=int(block))

			# Get RECV message
			message = self.readMessage()
			notifyHdr = message[1]
			entInfoHdr = message[2]
			q_id = notifyHdr.qubit_id

			if print_info:
				self.print_CQC_msg(message)

			if notify:
				message = self.readMessage()
				if print_info:
					self.print_CQC_msg(message)

			# initialize the qubit
			q.set_entInfo(entInfoHdr)
			q._qID = q_id

			# Activate and return qubit
			q._active = True
			return q

	def set_pending(self, pend_messages, print_info=False):
		"""
			Set the pend_messages flag.
			If true, flush() has to be called to send all pending_messages in sequence to the backend
			If false, all commands are directly send to the back_end
		:param pend_messages: Boolean to indicate if messages should pend or not
		:param print_info: If info should be printed
		"""
		# Check if the list is not empty, give a warning if it isn't
		if self.pending_messages:
			logging.warning("List of pending messages is not empty, flushing them")
			self.flush(print_info)
		self.pend_messages = pend_messages

	def flush(self, do_sequence=True, print_info=True):
		"""
			Flush all pending messages to the backend.
			:param do_sequence: boolean to indicate if you want to send the pending messages as a sequence
			:param print_info: If info should be printed
			:return: A list of things that are send back from the server. Can be qubits, or outcomes
		"""
		return self.flush_factory(1, do_sequence, print_info)

	def flush_factory(self, num_iter, do_sequence=True, print_info=True):
		"""
		Flushes the current pending sequence in a factory. It is performed multiple times
		:param num_iter: The amount of times the current pending sequence is performed
		:return: A list of outcomes/qubits that are produced by the commands
		"""
		# Because of new/recv we might have to send headers multiple times
		# Loop over the pending_messages until there are no more
		# It should only enter the while loop ones if num_iter == 1
		# Otherwise it loops for every non active qubit it encouters
		res = []
		while self.pending_messages:
			if print_info:
				print("App {} starts flushing pending messages".format(self.name))
			pending_headers = []
			should_notify = False
			header_length = 0
			ready_messages = []
			# Loop over the messages until we encounter an inactive qubit (or end of list)
			for message in self.pending_messages[:]:
				q = message[0]
				cqc_command = message[1]

				# Check if the q is active, if it is not, send the current pending_headers
				# Then check again, if it still not active, throw an error
				if not q._active and cqc_command not in {CQC_CMD_EPR_RECV, CQC_CMD_RECV, CQC_CMD_NEW, CQC_CMD_EPR}:
					if num_iter != 1:
						raise CQCUnsuppError("Some qubits are non active in the factory, this is not supported (yet)")
					if not pending_headers:  # If all messages already have been send, the qubit is inactive
						raise CQCNoQubitError("Qubit is not active")
					if print_info:
						print(
							"App {} encountered a non active qubit, sending current pending messages".format(self.name))
					break  # break out the for loop

				# set qubit to inactive, since we send it away or measured it
				if cqc_command == CQC_CMD_SEND or cqc_command == CQC_CMD_MEASURE:
					q._active = False

				q_id = q._qID if q._qID is not None else 0

				self.pending_messages.remove(message)
				ready_messages.append(message)

				notify = message[2]
				should_notify = should_notify or notify
				block = message[3]
				if len(message) > 4:
					values = message[4]
				else:
					values = []

				cmd_header = CQCCmdHeader()
				cmd_header.setVals(q_id, cqc_command, notify, block, int(do_sequence))
				header_length += cmd_header.HDR_LENGTH
				pending_headers.append(cmd_header)

				xtra_header = createXtraHeader(cqc_command, values)

				if xtra_header is not None:
					header_length += xtra_header.HDR_LENGTH
					pending_headers.append(xtra_header)

				if do_sequence:
					sequence_header = CQCSequenceHeader()
					header_length += sequence_header.HDR_LENGTH
					pending_headers.append(sequence_header)

			# create the header and sequence headers if needed
			# We need to find the header length for sequence,
			# so loop over the pending_headers in reverse
			if do_sequence:
				sequence_length = 0
				for header in reversed(pending_headers):
					if isinstance(header, CQCSequenceHeader):
						header.setVals(sequence_length)
					sequence_length += header.HDR_LENGTH

			if num_iter != 1:
				factory_header = CQCFactoryHeader()
				factory_header.setVals(num_iter, should_notify)
				header_length += factory_header.HDR_LENGTH
				pending_headers.insert(0, factory_header)
				cqc_type = CQC_TP_FACTORY
			else:
				cqc_type = CQC_TP_COMMAND

			cqc_header = CQCHeader()
			cqc_header.setVals(CQC_VERSION, cqc_type, self._appID, header_length)
			pending_headers.insert(0, cqc_header)

			# send the headers
			for header in pending_headers:
				if print_info:
					print("App {} sends CQC: {}".format(self.name, header.printable()))
				self._s.send(header.pack())

			# Read out any returned messages from the backend
			for i in range(num_iter):
				for data in ready_messages:
					q = data[0]
					cmd = data[1]
					if shouldReturn(cmd):
						message = self.readMessage()
						self.check_error(message[0])
						res.append(self.parse_CQC_msg(message, q, num_iter != 1))
						if print_info:
							self.print_CQC_msg(message)

			if should_notify:
				message = self.readMessage()
				self.check_error(message[0])
		return res

	def tomography(self, preparation, iterations, progress=True):
		"""
		Does a tomography on the output from the preparation specified.
		The frequencies from X, Y and Z measurements are returned as a tuple (f_X,f_Y,f_Z).

		- **Arguments**

			:preparation:	 A function that takes a CQCConnection as input and prepares a qubit and returns this (and preferably sets print_info=False)
			:iterations:	 Number of measurements in each basis.
			:progress_bar:	 Displays a progress bar
		"""
		accum_outcomes = [0, 0, 0]
		if progress:
			bar = ProgressBar(3 * iterations)

		# Measure in X
		for _ in range(iterations):
			# Progress bar
			if progress:
				bar.increase()

			# prepare and measure
			q = preparation(self)
			q.H(print_info=False)
			m = q.measure(print_info=False)
			accum_outcomes[0] += m

		# Measure in Y
		for _ in range(iterations):
			# Progress bar
			if progress:
				bar.increase()

			# prepare and measure
			q = preparation(self)
			q.K(print_info=False)
			m = q.measure(print_info=False)
			accum_outcomes[1] += m

		# Measure in Z
		for _ in range(iterations):
			# Progress bar
			if progress:
				bar.increase()

			# prepare and measure
			q = preparation(self)
			m = q.measure(print_info=False)
			accum_outcomes[2] += m

		if progress:
			bar.close()
			del bar

		freqs = map(lambda x: x / iterations, accum_outcomes)
		return list(freqs)

	def test_preparation(self, preparation, exp_values, conf=2, iterations=100, progress=True):
		"""
		Test the preparation of a qubit.
		Returns True if the expected values are inside the confidence interval produced from the data received from the tomography function

		- **Arguments**

			:preparation:	 A function that takes a CQCConnection as input and prepares a qubit and returns this (and preferably sets print_info=False)
			:exp_values:	 The expected values for measurements in the X, Y and Z basis.
			:conf:		 Determines the confidence region (+/- conf/sqrt(iterations) )
			:iterations:	 Number of measurements in each basis.
			:progress_bar:	 Displays a progress bar
		"""
		epsilon = conf / math.sqrt(iterations)

		freqs = self.tomography(preparation, iterations, progress=progress)
		for i in range(3):
			if abs(freqs[i] - exp_values[i]) > epsilon:
				return False
		return True


class ProgressBar:
	def __init__(self, maxitr):
		self.maxitr = maxitr
		self.itr = 0
		print("")
		self.update()

	def increase(self):
		self.itr += 1
		self.update()

	def update(self):
		procent = int(100 * self.itr / self.maxitr)
		sys.stdout.write('\r')
		sys.stdout.write("[%-100s] %d%%" % ('=' * procent, procent))
		sys.stdout.flush()
		pass

	def close(self):
		print("")


class CQCGeneralError(Exception):
	pass


class CQCNoQubitError(CQCGeneralError):
	pass


class CQCUnsuppError(CQCGeneralError):
	pass


class CQCTimeoutError(CQCGeneralError):
	pass


class CQCInuseError(CQCGeneralError):
	pass


class QubitNotActiveError(CQCGeneralError):
	pass


class qubit:
	"""
	A qubit.
	"""

	def __init__(self, cqc, notify=True, block=True, print_info=True, createNew=True, q_id=None, entInfo=None):
		"""
		Initializes the qubit. The cqc connection must be given.
		If notify, the return message is received before the method finishes.
		createNew is set to False when we receive a qubit.

		- **Arguments**

			:cqc:		 The CQCconnection used
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
			:createNew:	 If NEW-message should be sent, used internally
			:q_id:		 Qubit id, used internally if createNew
			:entInfo:	 Entanglement information, if qubit is part of EPR-pair
		"""

		# Cqc connection
		self._cqc = cqc

		if createNew:
			if cqc.pend_messages:
				# print info
				if print_info:
					print("App {} pends message:'Create qubit'".format(self._cqc.name))

				cqc.pending_messages.append([self, CQC_CMD_NEW, int(notify), int(block)])
				# Set q id, None by default
				self._qID = q_id
				self._active = False
			else:
				# print info
				if print_info:
					print("App {} tells CQC: 'Create qubit'".format(self._cqc.name))

				# Create new qubit at the cqc server
				self._cqc.sendCommand(0, CQC_CMD_NEW, notify=int(notify), block=int(block))

				# Activate qubit
				self._active = True
				# Get qubit id
				message = self._cqc.readMessage()
				try:
					notifyHdr = message[1]
					self._qID = notifyHdr.qubit_id
				except AttributeError:
					raise CQCGeneralError("Didn't receive the qubit id")

				if notify:
					message = self._cqc.readMessage()
					if print_info:
						self._cqc.print_CQC_msg(message)
		else:
			self._qID = q_id
			self._active = False  # Why?

		# Entanglement information
		self._entInfo = entInfo

		# Lookup remote entangled node
		self._remote_entNode = None
		if self._entInfo:
			ip = self._entInfo.node_B
			port = self._entInfo.port_B
			for node in self._cqc._cqcNet.hostDict.values():
				if (node.ip == ip) and (node.port == port):
					self._remote_entNode = node.name
					break

	def __str__(self):
		if self._active:
			return "Qubit at the node {}".format(self._cqc.name)
		else:
			return "Not active qubit"

	def get_entInfo(self):
		return self._entInfo

	def print_entInfo(self):
		if self._entInfo:
			print(self._entInfo.printable())
		else:
			print("No entanglement information")

	def set_entInfo(self, entInfo):
		self._entInfo = entInfo

		# Lookup remote entangled node
		self._remote_entNode = None
		if self._entInfo:
			ip = self._entInfo.node_B
			port = self._entInfo.port_B
			for node in self._cqc._cqcNet.hostDict.values():
				if (node.ip == ip) and (node.port == port):
					self._remote_entNode = node.name
					break

	def is_entangled(self):
		if self._entInfo:
			return True
		return False

	def get_remote_entNode(self):
		return self._remote_entNode

	def check_active(self):
		"""
		Checks if the qubit is active
		"""
		if self._cqc.pend_messages:
			return  # will be handled in the flush, not here
		if not self._active:
			raise QubitNotActiveError("Qubit is not active, has either been sent, measured or not received")

	def _single_qubit_gate(self, command, notify, block, print_info):
		"""
		Performs a single qubit gate specified by the command, called in I(), X(), Y() etc
		:param command: the identifier of the command, as specified in cqcHeader.py
		:param notify: Do we wish to be notified when done
		:param block: Do we want the qubit to be blocked
		:param print_info: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		if self._cqc.pend_messages:
			# print info
			if print_info:
				print("App {} pends message: 'Send command {} for qubit with ID {}'".format(self._cqc.name, command,
																							self._qID))

			self._cqc.pending_messages.append([self, command, int(notify), int(block)])
		else:
			# print info
			if print_info:
				print("App {} tells CQC: 'Send command {} for qubit with ID {}'".format(self._cqc.name, command,
																						self._qID))

			self._cqc.sendCommand(self._qID, command, notify=int(notify), block=int(block))
			if notify:
				message = self._cqc.readMessage()
				if print_info:
					self._cqc.print_CQC_msg(message)

	def I(self, notify=True, block=True, print_info=True):
		"""
		Performs an identity gate on the qubit.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_qubit_gate(CQC_CMD_I, notify, block, print_info)

	def X(self, notify=True, block=True, print_info=True):
		"""
		Performs a X on the qubit.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_qubit_gate(CQC_CMD_X, notify, block, print_info)

	def Y(self, notify=True, block=True, print_info=True):
		"""
		Performs a Y on the qubit.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_qubit_gate(CQC_CMD_Y, notify, block, print_info)

	def Z(self, notify=True, block=True, print_info=True):
		"""
		Performs a Z on the qubit.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_qubit_gate(CQC_CMD_Z, notify, block, print_info)

	def T(self, notify=True, block=True, print_info=True):
		"""
		Performs a T gate on the qubit.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_qubit_gate(CQC_CMD_T, notify, block, print_info)

	def H(self, notify=True, block=True, print_info=True):
		"""
		Performs a Hadamard on the qubit.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_qubit_gate(CQC_CMD_H, notify, block, print_info)

	def K(self, notify=True, block=True, print_info=True):
		"""
		Performs a K gate on the qubit.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_qubit_gate(CQC_CMD_K, notify, block, print_info)

	def _single_gate_rotation(self, command, step, notify, block, print_info):
		"""
		Perform a rotation on a qubit
		:param command: the rotation qubit command as specified in cqcHeader.py
		:param step: Determines the rotation angle in steps of 2*pi/256
		:param notify: Do we wish to be notified when done
		:param block: Do we want the qubit to be blocked
		:param print_info: If info should be printed
		:return:
		"""
		# check if qubit is active
		self.check_active()

		if self._cqc.pend_messages:
			# print info
			if print_info:
				print(
					"App {} pends message: 'Perform rotation command {} (angle {}*2pi/256) to qubit with ID {}'".format(
						self._cqc.name, command, step, self._qID))
			self._cqc.pending_messages.append([self, command, int(notify), int(block), step])
		else:
			# print info
			if print_info:
				print(
					"App {} tells CQC: 'Perform rotation command {} (angle {}*2pi/256) to qubit with ID {}'".format(
						self._cqc.name, command, step, self._qID))
			self._cqc.sendCmdXtra(self._qID, command, step=step, notify=int(notify), block=int(block))
			if notify:
				message = self._cqc.readMessage()
				if print_info:
					self._cqc.print_CQC_msg(message)

	def rot_X(self, step, notify=True, block=True, print_info=True):
		"""
		Applies rotation around the x-axis with the angle of step*2*pi/256 radians.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:step:		 Determines the rotation angle in steps of 2*pi/256
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_gate_rotation(CQC_CMD_ROT_X, step, notify, block, print_info)

	def rot_Y(self, step, notify=True, block=True, print_info=True):
		"""
		Applies rotation around the y-axis with the angle of step*2*pi/256 radians.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:step:		 Determines the rotation angle in steps of 2*pi/256
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_gate_rotation(CQC_CMD_ROT_Y, step, notify, block, print_info)

	def rot_Z(self, step, notify=True, block=True, print_info=True):
		"""
		Applies rotation around the z-axis with the angle of step*2*pi/256 radians.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:step:		 Determines the rotation angle in steps of 2*pi/256
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._single_gate_rotation(CQC_CMD_ROT_Z, step, notify, block, print_info)

	def _two_qubit_gate(self, command, target, notify, block, print_info):
		"""
		Perform a two qubit gate on the qubit
		:param command: the two qubit gate command as specified in cqcHeader.py
		:param target: The target qubit
		:param notify: Do we wish to be notified when done
		:param block: Do we want the qubit to be blocked
		:param print_info: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		# print info
		if print_info:
			print("App {} tells CQC: 'Perform CNOT to qubits with IDs {}(control) {}(target)'".format(self._cqc.name,
																									  self._qID,
																									  target._qID))
		if self._cqc.pend_messages:
			self._cqc.pending_messages.append([self, command, int(notify), int(block), target._qID])
		else:
			self._cqc.sendCmdXtra(self._qID, command, notify=int(notify), block=int(block), xtra_qID=target._qID)
			if notify:
				message = self._cqc.readMessage()
				if print_info:
					self._cqc.print_CQC_msg(message)

	def cnot(self, target, notify=True, block=True, print_info=True):
		"""
		Applies a cnot onto target.
		Target should be a qubit-object with the same cqc connection.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:target:	 The target qubit
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._two_qubit_gate(CQC_CMD_CNOT, target, notify, block, print_info)

	def cphase(self, target, notify=True, block=True, print_info=True):
		"""
		Applies a cphase onto target.
		Target should be a qubit-object with the same cqc connection.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:target:	 The target qubit
			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		self._two_qubit_gate(CQC_CMD_CPHASE, target, notify, block, print_info)

	def measure(self, inplace=False, block=True, print_info=True):
		"""
		Measures the qubit in the standard basis and returns the measurement outcome.
		If now MEASOUT message is received, None is returned.
		If inplace=False, the measurement is destructive and the qubit is removed from memory.
		If inplace=True, the qubit is left in the post-measurement state.

		- **Arguments**

			:inplace:	 If false, measure destructively.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		if inplace:
			command = CQC_CMD_MEASURE_INPLACE
		else:
			command = CQC_CMD_MEASURE

		if self._cqc.pend_messages:
			self._cqc.pending_messages.append([self, command, 0, int(block)])
			# print info
			if print_info:
				print("App {} pends message: 'Measure qubit with ID {}'".format(self._cqc.name, self._qID))

		else:
			# print info
			if print_info:
				print("App {} tells CQC: 'Measure qubit with ID {}'".format(self._cqc.name, self._qID))

			self._cqc.sendCommand(self._qID, command, notify=0, block=int(block))

			# Return measurement outcome
			message = self._cqc.readMessage()
			if not inplace:
				self._active = False
			try:
				notifyHdr = message[1]
				return notifyHdr.outcome
			except AttributeError:
				return None

	def reset(self, notify=True, block=True, print_info=True):
		"""
		Resets the qubit.
		If notify, the return message is received before the method finishes.

		- **Arguments**

			:nofify:	 Do we wish to be notified when done.
			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		if self._cqc.pend_messages:
			# print info
			if print_info:
				print("App {} pends message: 'Reset qubit with ID {}'".format(self._cqc.name, self._qID))

			self._cqc.pending_messages.append([self, CQC_CMD_RESET, int(notify), int(block)])
		else:
			# print info
			if print_info:
				print("App {} tells CQC: 'Reset qubit with ID {}'".format(self._cqc.name, self._qID))

			self._cqc.sendCommand(self._qID, CQC_CMD_RESET, notify=int(notify), block=int(block))
			if notify:
				message = self._cqc.readMessage()
				if print_info:
					self._cqc.print_CQC_msg(message)

	def getTime(self, block=True, print_info=True):
		"""
		Returns the time information of the qubit.
		If now INF_TIME message is received, None is returned.

		- **Arguments**

			:block:		 Do we want the qubit to be blocked
			:print_info:	 If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		# print info
		if print_info:
			print("App {} tells CQC: 'Return time-info of qubit with ID {}'".format(self._cqc.name, self._qID))

		self._cqc.sendGetTime(self._qID, notify=0, block=int(block))

		# Return time-stamp
		message = self._cqc.readMessage()
		try:
			notifyHdr = message[1]
			return notifyHdr.datetime
		except AttributeError:
			return None

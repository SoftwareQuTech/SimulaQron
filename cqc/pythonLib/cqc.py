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

import socket, struct, os, sys, time

from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *

class CQCConnection:
	_appIDs=[]
	def __init__(self,name,cqcFile=None,appID=0):
		"""
		Initialize a connection to the cqc server.
		Arguments:
		name	: Name of the host.
		cqcFile	: Path to cqcFile. If None, '$NETSIM/config/cqcNodes.cfg is used.
		appID	: Application ID, defaults to a nonused ID.
		"""

		# Host name
		self.name=name

		# Which appID
		if appID in self._appIDs:
			raise ValueError("appID={} is already in use".format(appID))
		self._appID=appID
		self._appIDs.append(self._appID)

		# Buffer received data
		self.buf=None

		# This file defines the network of CQC servers interfacing to virtual quantum nodes
		if cqcFile==None:
			self.cqcFile = os.environ.get('NETSIM') + "/config/cqcNodes.cfg"

		# Read configuration files for the cqc network
		self._cqcNet = networkConfig(self.cqcFile)

		# Host data
		if self.name in self._cqcNet.hostDict:
			myHost = self._cqcNet.hostDict[self.name]
		else:
			raise ValueError("Host name '{}' is not in the cqc network".format(name))

		#Get IP of correct form
		myIP=socket.inet_ntoa(struct.pack("!L",myHost.ip))

		#Connect to cqc server
		self._s=None
		try:
			self._s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
		except socket.error:
			raise RuntimeError("Could not connect to cqc server '{}'".format(name))
		try:
			self._s.connect((myIP,myHost.port))
		except socket.error:
			self._s.close()
			raise RuntimeError("Could not connect to cqc server '{}'".format(name))

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

	def sendSimple(self,tp):
		"""
		Sends a simple message to the cqc server, for example a HELLO message if tp=CQC_TP_HELLO.
		"""
		hdr=CQCHeader()
		hdr.setVals(CQC_VERSION,tp,self._appID,0)
		msg=hdr.pack()
		self._s.send(msg)

	def sendCommand(self,qID,command,notify=1,block=1,action=0):
		"""
		Sends a simple message and command message to the cqc server.
		Arguments:
		qID	: qubit ID
		command	: Command to be executed, eg CQC_CMD_H
		nofify	: Do we wish to be notified when done.
		block	: Do we want the qubit to be blocked
		action	: Are there more commands to be executed
		"""
		#Send Header
		hdr=CQCHeader()
		hdr.setVals(CQC_VERSION,CQC_TP_COMMAND,self._appID,CQC_CMD_HDR_LENGTH)
		msg=hdr.pack()
		self._s.send(msg)

		#Send Command
		cmd_hdr=CQCCmdHeader()
		cmd_hdr.setVals(qID,command,notify,block,action)
		cmd_msg=cmd_hdr.pack()
		self._s.send(cmd_msg)

	def sendCmdXtra(self,qID,command,notify=1,block=1,action=0,xtra_qID=0,step=0,remote_appID=0,remote_node=0,remote_port=0,cmd_length=0):
		"""
		Sends a simple message, command message and xtra message to the cqc server.
		Arguments:
		qID		: qubit ID
		command		: Command to be executed, eg CQC_CMD_H
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		action		: Are there more commands to be executed
		xtra_qID	: Extra qubit ID for for example CNOT
		step		: Defines the angle of rotation.
		remote_appID	: Application ID of remote host
		remote_node	: ip of remote host in cqc network
		remote_port	: port of remote host in cqc network
		cmd_length	: length of extra commands
		"""
		#Send Header
		hdr=CQCHeader()
		hdr.setVals(CQC_VERSION,CQC_TP_COMMAND,self._appID,CQC_CMD_HDR_LENGTH+CQC_CMD_XTRA_LENGTH)
		msg=hdr.pack()
		self._s.send(msg)

		#Send Command
		cmd_hdr=CQCCmdHeader()
		cmd_hdr.setVals(qID,command,notify,block,action)
		cmd_msg=cmd_hdr.pack()
		self._s.send(cmd_msg)

		#Send Xtra
		xtra_hdr=CQCXtraHeader()
		xtra_hdr.setVals(xtra_qID,step,remote_appID,remote_node,remote_port,cmd_length)
		xtra_msg=xtra_hdr.pack()
		self._s.send(xtra_msg)

	def sendGetTime(self,qID,notify=1,block=1,action=0):
		"""
		Sends a simple message and get-time message
		Arguments:
		qID		: qubit ID
		command		: Command to be executed, eg CQC_CMD_H
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		action		: Are there more commands to be executed
		"""
		#Send Header
		hdr=CQCHeader()
		hdr.setVals(CQC_VERSION,CQC_TP_GET_TIME,self._appID,CQC_CMD_HDR_LENGTH)
		print("Header")
		print(hdr.printable())
		msg=hdr.pack()
		self._s.send(msg)

		#Send Command
		cmd_hdr=CQCCmdHeader()
		cmd_hdr.setVals(qID,0,notify,block,action)
		print("CmdHeader")
		print(cmd_hdr.printable())
		cmd_msg=cmd_hdr.pack()
		self._s.send(cmd_msg)

	def sendFactory(self,qID,notify=1,block=1,action=0):
		"""
		Sends a simple message and factory message
		Arguments:
		qID		: qubit ID
		command		: Command to be executed, eg CQC_CMD_H
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		action		: Are there more commands to be executed
		"""
		raise NotImplementedError("Not implemented yet") #TODO
		#Send Header
		hdr=CQCHeader()
		hdr.setVals(CQC_VERSION,CQC_TP_FACTORY,self._appID,CQC_CMD_HDR_LENGTH)
		print("Header")
		print(hdr.printable())
		msg=hdr.pack()
		self._s.send(msg)

		#Send Command
		cmd_hdr=CQCCmdHeader()
		cmd_hdr.setVals(qID,0,notify,block,action)
		print("CmdHeader")
		print(cmd_hdr.printable())
		cmd_msg=cmd_hdr.pack()
		self._s.send(cmd_msg)

	def readMessage(self,maxsize=192): # WHAT IS GOOD SIZE?
		"""
		Receive the whole message from cqc server.
		Returns (CQCHeader,None) or (CQCHeader,CQCNotifyHeader) depending on the type of message.
		Maxsize is the max size of message.
		"""

		#Initilize checks
		gotCQCHeader=False
		if self.buf:
			checkedBuf=False
		else:
			checkedBuf=True

		while True:

			#If buf does not contain enough data, read in more
			if checkedBuf:
				# Receive data
				data=self._s.recv(maxsize)

				# Read whatever we received into a buffer
				if self.buf:
					self.buf+=data
				else:
					self.buf=data

			# If we don't have the CQC header yet, try and read it in full.
			if not gotCQCHeader:
				if len(self.buf) < CQC_HDR_LENGTH:
					# Not enough data for CQC header, return and wait for the rest
					checkedBuf=True
					continue

				# Got enough data for the CQC Header so read it in
				gotCQCHeader = True;
				rawHeader = self.buf[0:CQC_HDR_LENGTH]
				currHeader = CQCHeader(rawHeader);

				# Remove the header from the buffer
				self.buf = self.buf[CQC_HDR_LENGTH:len(self.buf)]

				# Check for error
				self.check_error(currHeader)

			# Check whether we already received all the data
			if len(self.buf) < currHeader.length:
				# Still waiting for data
				checkedBuf=True
				continue
			else:
				break

		# We got all the data, read notify if there is any
		if currHeader.length==0:
			return (currHeader,None)
		try:
			rawNotifyHeader=self.buf[:CQC_NOTIFY_LENGTH]
			self.buf=self.buf[CQC_NOTIFY_LENGTH:len(self.buf)]
			notifyHeader=CQCNotifyHeader(rawNotifyHeader)
			return (currHeader,notifyHeader)
		except struct.error as err:
			print(err)

	def print_CQC_msg(self,message):
		"""
		Prints messsage returned by the readMessage method of CQCConnection.
		"""
		hdr=message[0]
		notifyHdr=message[1]

		if hdr.tp==CQC_TP_HELLO:
			print("CQC tells App {}: 'HELLO'".format(self.name))
		elif hdr.tp==CQC_TP_EXPIRE:
			print("CQC tells App {}: 'Qubit with ID {} has expired'".format(self.name,notifyHdr.qubit_id))
		elif hdr.tp==CQC_TP_DONE:
			print("CQC tells App {}: 'Done with command'".format(self.name))
		elif hdr.tp==CQC_TP_RECV:
			print("CQC tells App {}: 'Received qubit with ID {}'".format(self.name,notifyHdr.qubit_id))
		elif hdr.tp==CQC_TP_EPR_OK:
			print("CQC tells App {}: 'EPR created using qubit with ID {}'".format(self.name,notifyHdr.qubit_id))
		elif hdr.tp==CQC_TP_MEASOUT:
			print("CQC tells App {}: 'Measurement outcome is {}'".format(self.name,notifyHdr.outcome))
		elif hdr.tp==CQC_TP_INF_TIME:
			print("CQC tells App {}: 'Timestamp is {}'".format(self.name,notifyHdr.datetime))

	def check_error(self,hdr):
		"""
		Checks if there is an error returned.
		"""
		self._errorHandler(hdr.tp)

	def _errorHandler(self,cqc_err):
		"""
		Raises an error if there is an error-message
		"""
		if cqc_err==CQC_ERR_GENERAL:
			raise CQCGeneralError("General error")
		if cqc_err==CQC_ERR_NOQUBIT:
			raise CQCNoQubitError("Qubit not available or no more qubits available")
		if cqc_err==CQC_ERR_UNSUPP:
			raise CQCUnsuppError("Sequence not supported")
		if cqc_err==CQC_ERR_TIMEOUT:
			raise CQCTimeoutError("Timout")
		if cqc_err==CQC_ERR_INUSE:
			raise CQCInuseError("Qubit ID in use")

	def sendQubit(self,q,name,remote_appID=0,notify=True,block=True,print_info=True):
		"""
		Sends qubit to another node in the cqc network. If this node is not in the network an error is raised.
		q		: The qubit to send.
		Name		: Name of the node as specified in the cqc network config file.
		remote_appID	: The app ID of the application running on the receiving node.
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		"""

		# Get receiving host
		hostDict=self._cqcNet.hostDict
		if name in hostDict:
			recvHost=hostDict[name]
		else:
			raise ValueError("Host name '{}' is not in the cqc network".format(name))

		#print info
		if print_info:
			print("App {} tells CQC: 'Send qubit with ID {} to {} and appID {}'".format(self.name,q._qID,name,remote_appID))

		self.sendCmdXtra(q._qID,CQC_CMD_SEND,notify=int(notify),block=int(block),remote_appID=remote_appID,remote_node=recvHost.ip,remote_port=recvHost.port)
		if notify:
			message=self.readMessage()
			if print_info:
				self.print_CQC_msg(message)

		#Deactivate qubit
		q._active=False

	def recvQubit(self,notify=True,block=True,print_info=True):
		"""
		Receives a qubit.
		q		: The qubit to send.
		Name		: Name of the node as specified in the cqc network config file.
		remote_appID	: The app ID of the application running on the receiving node.
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""

		q=qubit(self,createNew=False)

		#print info
		if print_info:
			print("App {} tells CQC: 'Receive qubit'".format(self.name))

		self.sendCommand(q._qID,CQC_CMD_RECV,notify=int(notify),block=int(block))

		# Get RECV message
		message=self.readMessage()
		if print_info:
			self.print_CQC_msg(message)

		if notify:
			message=self.readMessage()
			self.print_CQC_msg(message)

		#Activate and return qubit
		q._active=True
		return q

	def createEPR(self,name,remote_appID=0,notify=True,block=True,print_info=True):
		"""
		Creates epr with other host in cqc network.
		NOT YET IMPLEMENTED.
		Name		: Name of the node as specified in the cqc network config file.
		remote_appID	: The app ID of the application running on the receiving node.
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""

		# Get receiving host
		hostDict=self._cqcNet.hostDict
		if name in hostDict:
			recvHost=hostDict[name]
		else:
			raise ValueError("Host name '{}' is not in the cqc network".format(name))

		q=qubit(self,createNew=False)

		#print info
		if print_info:
			print("App {} tells CQC: 'Create EPR-pair with {} and appID {}'".format(self.name,name,remote_appID))

		self.sendCmdXtra(q._qID,CQC_CMD_EPR,notify=int(notify),block=int(block),remote_appID=remote_appID,remote_node=recvHost.ip,remote_port=recvHost.port)

		# Get RECV message
		message=self.readMessage() #TODO TAKE CARE OF RETURN MESSAGES OF RECEIVE
		# if print_info:
		# 	self.print_CQC_msg(message)

		if notify:
			message=self.readMessage()
			if print_info:
				self.print_CQC_msg(message)

		#Activate and return qubit
		q._active=True
		return q

	def tomography(self,preparation,iterations,progress_bar=True):
		"""
		Does a tomography on the output from the preparation specified.
		The frequencies from X, Y and Z measurements are returned as a tuple (f_X,f_Y,f_Z).
		Arguments:
		preparation	: A function that takes a qubit as input and applies the prepation-operations.
		iterations	: Number of measurements in each basis.
		progress_bar	: Displays a progress bar
		"""

		accum_outcomes=[0,0,0]
		if progress_bar:
			progress=100/(3*iterations)
			print("")

		# Measure in X
		for _ in range(iterations):
			# Progress bar
			if progress_bar:
				sys.stdout.write('\r')
				sys.stdout.write("[%-100s] %d%%" % ('='*int(progress),int(progress)))
				sys.stdout.flush()
				progress+=100/(3*iterations)

			# prepare and measure
			q=qubit(self,print_info=False)
			preparation(q)
			q.H(print_info=False)
			m=q.measure(print_info=False)
			accum_outcomes[0]+=m

		# Measure in Y
		for _ in range(iterations):
			# Progress bar
			if progress_bar:
				sys.stdout.write('\r')
				sys.stdout.write("[%-100s] %d%%" % ('='*int(progress),int(progress)))
				sys.stdout.flush()
				progress+=100/(3*iterations)

			# prepare and measure
			q=qubit(self,print_info=False)
			preparation(q)
			q.rot_X(192,print_info=False)
			m=q.measure(print_info=False)
			accum_outcomes[1]+=m

		# Measure in Z
		for _ in range(iterations):
			# Progress bar
			if progress_bar:
				sys.stdout.write('\r')
				sys.stdout.write("[%-100s] %d%%" % ('='*int(progress),int(progress)))
				sys.stdout.flush()
				progress+=100/(3*iterations)

			# prepare and measure
			q=qubit(self,print_info=False)
			preparation(q)
			m=q.measure(print_info=False)
			accum_outcomes[2]+=m

		if progress_bar:
			progress=0
			print("")

		freqs=map(lambda x:x/iterations,accum_outcomes)
		return list(freqs)

class CQCGeneralError(Exception):
	pass
class CQCNoQubitError(Exception):
	pass
class CQCUnsuppError(Exception):
	pass
class CQCTimeoutError(Exception):
	pass
class CQCInuseError(Exception):
	pass
class QubitNotActiveError(Exception):
	pass


class qubit:
	"""
	A qubit.
	"""
	_next_qID={}
	def __init__(self,cqc,notify=True,block=True,print_info=True,createNew=True):
		"""
		Initializes the qubit. The cqc connection must be given.
		If notify, the return message is received before the method finishes.
		createNew is set to False when we receive a qubit.
		Arguments:
		cqc		: The CQCconnection used
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		createNew	: If NEW-message should be sent, used internally
		"""

		#Cqc connection
		self._cqc=cqc

		# Active qubit
		if createNew:
			self._active=True
		else:
			self._active=False

		# Which qID
		if cqc._appID in qubit._next_qID:
			self._qID=qubit._next_qID[cqc._appID]
			qubit._next_qID[cqc._appID]+=1
		else:
			self._qID=0
			qubit._next_qID[cqc._appID]=1

		if createNew:
			#print info
			if print_info:
				print("App {} tells CQC: 'Create qubit with ID {}'".format(self._cqc.name,self._qID))

			# Create new qubit at the cqc server
			self._cqc.sendCommand(self._qID,CQC_CMD_NEW,notify=int(notify),block=int(block))
			if notify:
				message=self._cqc.readMessage()
				if print_info:
					self._cqc.print_CQC_msg(message)
	def __str__(self):
		if self._active:
			return "Qubit at the node {}".format(self._cqc.name)
		else:
			return "Not active qubit"

	def check_active(self):
		"""
		Checks if the qubit is active
		"""
		if not self._active:
			raise QubitNotActiveError("Qubit is not active, has either been sent, measured or not recieved")

	def I(self,notify=True,block=True,print_info=True):
		"""
		Performs an identity gate on the qubit.
		If notify, the return message is received before the method finishes.
		Arguments:
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Do nothing with qubit with ID {}'".format(self._cqc.name,self._qID))

		self._cqc.sendCommand(self._qID,CQC_CMD_I,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def X(self,notify=True,block=True,print_info=True):
		"""
		Performs a X on the qubit.
		If notify, the return message is received before the method finishes.
		Arguments:
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform X to qubit with ID {}'".format(self._cqc.name,self._qID))

		self._cqc.sendCommand(self._qID,CQC_CMD_X,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def Y(self,notify=True,block=True,print_info=True):
		"""
		Performs a Y on the qubit.
		If notify, the return message is received before the method finishes.
		Arguments:
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform Y to qubit with ID {}'".format(self._cqc.name,self._qID))

		self._cqc.sendCommand(self._qID,CQC_CMD_Y,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def Z(self,notify=True,block=True,print_info=True):
		"""
		Performs a Z on the qubit.
		If notify, the return message is received before the method finishes.
		Arguments:
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform Z to qubit with ID {}'".format(self._cqc.name,self._qID))

		self._cqc.sendCommand(self._qID,CQC_CMD_Z,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def T(self,notify=True,block=True,print_info=True):
		"""
		Performs a T gate on the qubit.
		If notify, the return message is received before the method finishes.
		Arguments:
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform T to qubit with ID {}'".format(self._cqc.name,self._qID))

		self._cqc.sendCommand(self._qID,CQC_CMD_T,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def H(self,notify=True,block=True,print_info=True):
		"""
		Performs a Hadamard on the qubit.
		If notify, the return message is received before the method finishes.
		Arguments:
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform H to qubit with ID {}'".format(self._cqc.name,self._qID))

		self._cqc.sendCommand(self._qID,CQC_CMD_H,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def rot_X(self,step,notify=True,block=True,print_info=True):
		"""
		Applies rotation around the x-axis with the angle of step*2*pi/256 radians.
		If notify, the return message is received before the method finishes.
		Arguments:
		step		: Determines the rotation angle in steps of 2*pi/256
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform X-rot (angle {}*2pi/256) to qubit with ID {}'".format(self._cqc.name,step,self._qID))

		self._cqc.sendCmdXtra(self._qID,CQC_CMD_ROT_X,step=step,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def rot_Y(self,step,notify=True,block=True,print_info=True):
		"""
		Applies rotation around the y-axis with the angle of step*2*pi/256 radians.
		If notify, the return message is received before the method finishes.
		Arguments:
		step		: Determines the rotation angle in steps of 2*pi/256
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform Y-rot (angle {}*2pi/256) to qubit with ID {}'".format(self._cqc.name,step,self._qID))

		self._cqc.sendCmdXtra(self._qID,CQC_CMD_ROT_Y,step=step,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def rot_Z(self,step,notify=True,block=True,print_info=True):
		"""
		Applies rotation around the z-axis with the angle of step*2*pi/256 radians.
		If notify, the return message is received before the method finishes.
		Arguments:
		step		: Determines the rotation angle in steps of 2*pi/256
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform Z-rot (angle {}*2pi/256) to qubit with ID {}'".format(self._cqc.name,step,self._qID))

		self._cqc.sendCmdXtra(self._qID,CQC_CMD_ROT_Z,step=step,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def cnot(self,target,notify=True,block=True,print_info=True):
		"""
		Applies a cnot onto target.
		Target should be a qubit-object with the same cqc connection.
		If notify, the return message is received before the method finishes.
		Arguments:
		target		: The target qubit
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform CNOT to qubits with IDs {}(control) {}(target)'".format(self._cqc.name,self._qID,target._qID))

		self._cqc.sendCmdXtra(self._qID,CQC_CMD_CNOT,notify=int(notify),block=int(block),xtra_qID=target._qID)
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def cphase(self,target,notify=True,block=True,print_info=True):
		"""
		Applies a cphase onto target.
		Target should be a qubit-object with the same cqc connection.
		If notify, the return message is received before the method finishes.
		Arguments:
		target		: The target qubit
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Perform CPHASE to qubits with IDs {}(control) {}(target)'".format(self._cqc.name,self._qID,target))

		self._cqc.sendCmdXtra(self._qID,CQC_CMD_CPHASE,notify=int(notify),block=int(block),xtra_qID=target._qID)
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)

	def measure(self,inplace=False,block=True,print_info=True):
		"""
		Measures the qubit in the standard basis and returns the measurement outcome.
		If now MEASOUT message is received, None is returned.
		If inplace=False, the measurement is destructive and the qubit is removed from memory.
		If inplace=True, the qubit is left in the post-measurement state.
		Arguments:
		inplace		: If false, measure destructively.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Measure qubit with ID {}'".format(self._cqc.name,self._qID))

		if inplace:
			self._cqc.sendCommand(self._qID,CQC_CMD_MEASURE_INPLACE,notify=0,block=int(block))
		else:
			self._cqc.sendCommand(self._qID,CQC_CMD_MEASURE,notify=0,block=int(block))

		#Return measurement outcome
		message=self._cqc.readMessage()
		if not inplace:
			self._active=False
		try:
			notifyHdr=message[1]
			return notifyHdr.outcome
		except AttributeError:
			return None

	def reset(self,notify=True,block=True,print_info=True):
		"""
		Resets the qubit.
		If notify, the return message is received before the method finishes.
		Arguments:
		nofify		: Do we wish to be notified when done.
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Reset qubit with ID {}'".format(self._cqc.name,self._qID))

		self._cqc.sendCommand(self._qID,CQC_CMD_RESET,notify=int(notify),block=int(block))
		if notify:
			message=self._cqc.readMessage()
			if print_info:
				self._cqc.print_CQC_msg(message)


	def getTime(self,block=True,print_info=True):
		"""
		Returns the time information of the qubit.
		If now INF_TIME message is received, None is returned.
		Arguments:
		block		: Do we want the qubit to be blocked
		print_info	: If info should be printed
		"""
		# check if qubit is active
		self.check_active()

		#print info
		if print_info:
			print("App {} tells CQC: 'Return time-info of qubit with ID {}'".format(self._cqc.name,self._qID))

		self._cqc.sendGetTime(self._qID,notify=int(notify),block=int(block))

		# Return time-stamp
		message=self._cqc.readMessage()
		try:
			notifyHdr=message[1]
			return notifyHdr.datetime
		except AttributeError:
			return None

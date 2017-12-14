
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


import sys, os, time, logging

from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList, Deferred

from SimulaQron.virtNode.basics import *
from SimulaQron.virtNode.quantum import *
from SimulaQron.general.hostConfig import *
from SimulaQron.virtNode.crudeSimulator import *

from SimulaQron.local.setup import *

from SimulaQron.cqc.backend.cqcHeader import *
from SimulaQron.cqc.backend.cqcHeader import CQCXtraHeader

#####################################################################################################
#
# CQC Factory
#
# Twisted factory for the CQC protocol
#

class CQCFactory(Factory):

	def __init__(self, host, name, cqcNet):
		"""
		Initialize CQC Factory.

		lhost	details of the local host (class host)
		"""

		self.host = host
		self.name = name
		self.cqcNet = cqcNet
		self.virtRoot = None
		self.qReg = None

		# Dictionary that keeps qubit dictorionaries for each application
		self.qubitList = { };

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

	def __init__(self, factory):

		# CQC Factory, including our connection to the SimulaQron backend
		self.factory = factory;

		# Default application ID, typically one connection per application but we will
		# deliberately NOT check for that since this is the task of higher layers or an OS
		self.app_id = 0;

		# Functions to invoke when receiving a CQC Header of a certain type
		self.messageHandlers = {
			CQC_TP_HELLO : self.handle_hello,
			CQC_TP_COMMAND : self.handle_command,
			CQC_TP_FACTORY : self.handle_factory,
			CQC_TP_GET_TIME : self.handle_time
		}

		# Functions to invoke when receiving a certain command
		self.commandHandlers = {
			CQC_CMD_I : self.cmd_i,
			CQC_CMD_X : self.cmd_x,
			CQC_CMD_Y : self.cmd_y,
			CQC_CMD_Z : self.cmd_z,
			CQC_CMD_T : self.cmd_t,
			CQC_CMD_H : self.cmd_h,
			CQC_CMD_K : self.cmd_k,
			CQC_CMD_ROT_X : self.cmd_rotx,
			CQC_CMD_ROT_Y : self.cmd_roty,
			CQC_CMD_ROT_Z : self.cmd_rotz,
			CQC_CMD_CNOT : self.cmd_cnot,
			CQC_CMD_CPHASE : self.cmd_cphase,
			CQC_CMD_MEASURE : self.cmd_measure,
			CQC_CMD_MEASURE_INPLACE : self.cmd_measure_inplace,
			CQC_CMD_RESET : self.cmd_reset,
			CQC_CMD_SEND : self.cmd_send,
			CQC_CMD_RECV : self.cmd_recv,
			CQC_CMD_EPR : self.cmd_epr,
			CQC_CMD_NEW : self.cmd_new
		}


		# Flag to determine whether we already received _all_ of the CQC header
		self.gotCQCHeader = False;

		# Header for which we are currently processing a packet
		self.currHeader = None

		# Buffer received data (which may arrive in chunks)
		self.buf = None

		# Convenience
		self.name = self.factory.name;

		# Dictionary storing the next unique qubit id for each used app_id
		self.next_q_id={}

		logging.debug("CQC %s: Initialized Protocol",self.name)

	def connectionMade(self):
		pass

	def connectionLost(self, reason):
		pass

	def dataReceived(self, data):
		"""
		Receive data. We will always wait to receive enough data for the header, and then the entire packet first before commencing processing.
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
			self.gotCQCHeader = True;
			rawHeader = self.buf[0:CQC_HDR_LENGTH]
			self.currHeader = CQCHeader(rawHeader);

			# Remove the header from the buffer
			self.buf = self.buf[CQC_HDR_LENGTH:len(self.buf)]

			logging.debug("CQC %s: Read CQC Header: %s", self.name, self.currHeader.printable())

		# Check whether we already received all the data
		if len(self.buf) < self.currHeader.length:
			# Still waiting for data
			logging.debug("CQC %s: Incomplete data. Waiting.", self.name)
			return

		# We got the header and all the data for this packet. Start processing.
		# Update our app ID
		self.app_id = self.currHeader.app_id;

		# Invoke the relevant message handler, processing the possibly remaining data
		if self.currHeader.tp in self.messageHandlers:
			self.messageHandlers[self.currHeader.tp](self.currHeader, self.buf[0:self.currHeader.length])
		else:
			self._send_back_cqc(header, CQC_ERR_UNSUPP)

		# Reset and await the next packet
		self.gotCQCHeader = False

		# Check if we received data already for the next packet, if so save it
		if self.currHeader.length < len(self.buf):
			self.buf = self.buf[self.currHeader.length:len(self.buf)]
			self.dataReceived(b'')
		else:
			self.buf = None

	def get_virt_qubit(self, header, qubit_id):
		"""
		Get reference to the virtual qubit reference in SimulaQron given app and qubit id, if it exists. If not found, send back no qubit error.

		Caution: Twisted PB does not allow references to objects to be passed back between connections. If you need to pass a qubit reference
		back to the Twisted PB on a _different_ connection, then use get_virt_qubit_indep below.
		"""
		if not (header.app_id, qubit_id) in self.factory.qubitList:
			logging.debug("CQC %s: Qubit not found",self.name)
			self._send_back_cqc(header, CQC_ERR_NOQUBIT)
			return None

		qubit = self.factory.qubitList[(header.app_id, qubit_id)]
		return qubit.virt

	@inlineCallbacks
	def get_virt_qubit_indep(self, header, qubit_id):
		"""
		Get NUMBER (not reference!) to virtual qubit in SimulaQron specific to this connection. If not found, send back no qubit error.
		"""

		# First let's get the general virtual qubit reference, if any
		general_ref = self.get_virt_qubit(header, qubit_id)
		if not general_ref:
			return(-1)

		num = yield general_ref.callRemote("get_virt_num")
		logging.debug("GOT NUMBER %d XXX",num)

		return num

	def _send_back_cqc(self,header, msgType,length=0):
		"""
		Return a simple CQC header with the specified type.

		header	 CQC header of the packet we respond to
		msgType  Message type to return
		length	 Length of additional message
		"""
		hdr = CQCHeader();
		hdr.setVals(CQC_VERSION, msgType, header.app_id,length);
		msg = hdr.pack();
		self.transport.write(msg)

	def handle_hello(self, header, data):
		"""
		Hello just requires us to return hello - for testing availablility.
		"""
		hdr = CQCHeader();
		hdr.setVals(CQC_VERSION, CQC_TP_HELLO, header.app_id,0);
		msg = hdr.pack();
		self.transport.write(msg)

	@inlineCallbacks
	def handle_command(self, header, data):
		"""
		Handle incoming command requests.
		"""

		logging.debug("CQC %s: Command received", self.name)

		# Run the entire command list, incl. actions after completion which here we will do instantly
		(succ,shouldNotify) = yield self._process_command(header, header.length, data);
		if succ:
			if shouldNotify:
				# Send a notification that we are done if successful
				self._send_back_cqc(header, CQC_TP_DONE);
				logging.debug("CQC %s: Command successful, sent done.", self.name)

	@inlineCallbacks
	def _process_command(self, cqc_header, length, data):
		"""
			Process the commands - called recursively to also process additional command lists.
		"""

		cmdData = data

		# Read in all the commands sent
		l = 0;
		while l < length:
			cmd = CQCCmdHeader(cmdData[l:l+CQC_CMD_HDR_LENGTH]);
			newl = l + CQC_CMD_HDR_LENGTH;

			# Should we notify
			shouldNotify=cmd.notify

			# Check if this command includes an additional header
			if self.hasXtra(cmd):
				if len(cmdData) < (newl + CQC_CMD_XTRA_LENGTH):
					logging.debug("CQC %s: Missing XTRA Header", self.name)
				else:
					logging.debug("XXX")
					xtra = CQCXtraHeader(cmdData[newl:newl+CQC_CMD_XTRA_LENGTH]);
					newl = newl + CQC_CMD_XTRA_LENGTH;
					logging.debug("CQC %s: Read XTRA Header: %s", self.name, xtra.printable())
			else:
				xtra = None;

			# Run this command
			logging.debug("CQC %s: Executing command: %s", self.name, cmd.printable())
			if not cmd.instr in self.commandHandlers:
				self._send_back_cqc(header, CQC_ERR_UNSUPP)
				return (False,0)

			succ = yield self.commandHandlers[cmd.instr](cqc_header, cmd, xtra);
			if not succ:
				return (False,0)

			# Check if there are additional commands to execute afterwards
			if cmd.action:
				(succ,retNotify) = self._process_command(cqc_header, xtra.cmdLength, data[newl:newl+xtra.cmdLength])
				shouldNotify=(shouldNotify or retNotify)
				if not succ:
					return (False,0)
				newl = newl + xtra.cmdLength;

			l = newl;

		return (True,shouldNotify)

	def hasXtra(self, cmd):
		"""
		Check whether this command includes an extra header with additional information.
		"""
		if cmd.instr == CQC_CMD_SEND:
			return(True)
		if cmd.instr == CQC_CMD_EPR:
			return(True)
		if cmd.instr == CQC_CMD_CNOT:
			return(True)
		if cmd.instr == CQC_CMD_CPHASE:
			return(True)
		if cmd.instr == CQC_CMD_ROT_X:
			return(True)
		if cmd.instr == CQC_CMD_ROT_Y:
			return(True)
		if cmd.instr == CQC_CMD_ROT_Z:
			return(True)
		if cmd.action:
			return(True)

		return(False)

	@inlineCallbacks
	def handle_factory(self, header, data):

		cmd_l=CQC_CMD_HDR_LENGTH
		xtra_l=CQC_CMD_XTRA_LENGTH

		#Get command header
		if len(data)<cmd_l:
			logging.debug("CQC %s: Missing CMD Header", self.name)
			self._send_back_cqc(header,CQC_ERR_UNSUPP)
		cmdHeader=CQCCmdHeader(data[:cmd_l])

		#Get xtra header
		if len(data)<(cmd_l+xtra_l):
			logging.debug("CQC %s: Missing XTRA Header", self.name)
			self._send_back_cqc(header,CQC_ERR_UNSUPP)
		xtraHeader=CQCXtraHeader(data[cmd_l:cmd_l+xtra_l])

		command=cmdHeader.instr
		num_iter=xtraHeader.step

		# Perform operation multiple times
		all_succ=True
		for _ in range(num_iter):
			if self.hasXtra(cmdHeader):
				(succ,shouldNotify)=yield self._process_command(header,header.length,data)
			else:
				data=data[:cmd_l]+data[cmd_l+xtra_l:]
				(succ,shouldNotify)=yield self._process_command(header,header.length-xtra_l,data)
			all_succ=(all_succ and succ)
		if all_succ:
			if shouldNotify:
				# Send a notification that we are done if successful
				self._send_back_cqc(header, CQC_TP_DONE);
				logging.debug("CQC %s: Command successful, sent done.", self.name)



	def handle_time(self, header, data):

		# Read the command header to learn the qubit ID
		rawCmdHeader = data[:CQC_CMD_HDR_LENGTH];
		cmd_hdr = CQCCmdHeader(rawCmdHeader);

		# Get the qubit list
		qList = self.factory.qubitList

		# Lookup the desired qubit
		if (header.app_id,cmd_hdr.qubit_id) in qList:
			q=qList[(header.app_id,cmd_hdr.qubit_id)]
		else:
			# Specified qubit is unknown
			self._send_back_cqc(header, CQC_ERR_NOQUBIT);
			return;

		# Craft reply
		# First send an appropriate CQC Header
		self._send_back_cqc(header, CQC_TP_INF_TIME,length=CQC_NOTIFY_LENGTH);

		# Then we send a notify header with the timing details
		notify = CQCNotifyHeader();
		notify.setVals(cmd_hdr.qubit_id, 0, 0, 0, 0, q.timestamp);
		msg = notify.pack();
		self.transport.write(msg)

	def cmd_i(self, cqc_header, cmd, xtra):
		"""
		Do nothing. In reality we would wait a timestep but in SimulaQron we just do nothing.
		"""
		logging.debug("CQC %s: Doing Nothing to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		return True

	@inlineCallbacks
	def cmd_x(self, cqc_header, cmd, xtra):
		"""
		Apply X Gate
		"""
		logging.debug("CQC %s: Applying X to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_X")
		return True

	@inlineCallbacks
	def cmd_z(self, cqc_header, cmd, xtra):
		"""
		Apply Z Gate
		"""
		logging.debug("CQC %s: Applying Z to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_Z")
		return True

	@inlineCallbacks
	def cmd_y(self, cqc_header, cmd, xtra):
		"""
		Apply Y Gate
		"""
		logging.debug("CQC %s: Applying Y to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_Y")
		return True

	@inlineCallbacks
	def cmd_t(self, cqc_header, cmd, xtra):
		"""
		Apply T Gate
		"""
		logging.debug("CQC %s: Applying T to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_T")
		return True

	@inlineCallbacks
	def cmd_h(self, cqc_header, cmd, xtra):
		"""
		Apply H Gate
		"""
		logging.debug("CQC %s: Applying H to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_H")
		return True


	@inlineCallbacks
	def cmd_k(self, cqc_header, cmd, xtra):
		"""
		Apply K Gate
		"""
		logging.debug("CQC %s: Applying K to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_K")
		return True

	@inlineCallbacks
	def cmd_rotx(self, cqc_header, cmd, xtra):
		"""
		Rotate around x axis
		"""
		logging.debug("CQC %s: Applying ROTX to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_rotation",[1,0,0],2 * np.pi/256 * xtra.step)
		return True

	@inlineCallbacks
	def cmd_rotz(self, cqc_header, cmd, xtra):
		"""
		Rotate around z axis
		"""
		logging.debug("CQC %s: Applying ROTZ to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_rotation",[0,1,0],2 * np.pi/256 * xtra.step)
		return True

	@inlineCallbacks
	def cmd_roty(self, cqc_header, cmd, xtra):
		"""
		Rotate around y axis
		"""
		logging.debug("CQC %s: Applying ROTY to App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		yield virt_qubit.callRemote("apply_rotation",[0,0,1],2 * np.pi/256 * xtra.step)
		return True

	@inlineCallbacks
	def cmd_cnot(self, cqc_header, cmd, xtra):
		"""
		Apply CNOT Gate
		"""
		if not xtra:
			logging.debug("CQC %s: Missing XTRA Header", self.name)
			return False

		logging.debug("CQC %s: Applying CNOT to App ID %d qubit id %d target %d",self.name,cqc_header.app_id,cmd.qubit_id, xtra.qubit_id)
		control = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		target = self.get_virt_qubit(cqc_header, xtra.qubit_id)
		if not(control) or not(target):
			return False

		yield control.callRemote("cnot_onto",target)
		return True

	@inlineCallbacks
	def cmd_cphase(self, cqc_header, cmd, xtra):
		"""
		Apply CPHASE Gate
		"""
		if not xtra:
			logging.debug("CQC %s: Missing XTRA Header", self.name)
			return False

		logging.debug("CQC %s: Applying CPHASE to App ID %d qubit id %d target %d",self.name,cqc_header.app_id,cmd.qubit_id, xtra.qubit_id)
		control = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		target = self.get_virt_qubit(cqc_header, xtra.qubit_id)
		if not(control) or not(target):
			return False

		yield control.callRemote("cphase_onto",target)
		return True

	@inlineCallbacks
	def cmd_reset(self, cqc_header, cmd, xtra):
		"""
		Reset Qubit to |0>
		"""
		logging.debug("CQC %s: Reset App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		outcome = yield virt_qubit.callRemote("measure",inplace=True)

		# If state is |1> do correction
		if outcome:
			yield virt_qubit.callRemote("apply_X")
		return True

	@inlineCallbacks
	def cmd_measure(self, cqc_header, cmd, xtra, inplace=False):
		"""
		Measure
		"""
		logging.debug("CQC %s: Measuring App ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		outcome = yield virt_qubit.callRemote("measure",inplace)
		if outcome == None:
			logging.debug("CQC %s: Measurement failed", self.name)
			self._send_back_cqc(cqc_header, CQC_ERR_GENERAL)
			return False

		logging.debug("CQC %s: Measured outcome %d",self.name,outcome)
		# Send the outcome back as MEASOUT
		self._send_back_cqc(cqc_header, CQC_TP_MEASOUT,length=CQC_NOTIFY_LENGTH)

		# Send notify header with outcome
		hdr = CQCNotifyHeader();
		hdr.setVals(cmd.qubit_id, outcome, 0, 0, 0, 0);
		msg = hdr.pack()
		self.transport.write(msg)
		logging.debug("CQC %s: Notify %s",self.name, hdr.printable())

		if not inplace:
			# Remove from active mapped qubits
			del self.factory.qubitList[(cqc_header.app_id, cmd.qubit_id)]

		return True

	@inlineCallbacks
	def cmd_measure_inplace(self, cqc_header, cmd, xtra):

		# Call measure with inplace=True
		succ = yield self.cmd_measure(cqc_header,cmd,xtra,inplace=True)

		return succ

	@inlineCallbacks
	def cmd_send(self, cqc_header, cmd, xtra):
		"""
		Send qubit to another node.
		"""

		# Lookup the virtual qubit form identifier
		virt_num = yield self.get_virt_qubit_indep(cqc_header, cmd.qubit_id)
		if virt_num < 0:
			logging.debug("CQC %s: No such qubit",self.name)
			return False

		# Lookup the name of the remote node used within SimulaQron
		targetName = self.factory.lookup(xtra.remote_node, xtra.remote_port)
		if targetName == None:
			logging.debug("CQC %s: Remote node not found %s",self.name,xtra.printable())
			return False

		# Send instruction to transfer the qubit
		yield self.factory.virtRoot.callRemote("cqc_send_qubit", virt_num, targetName, cqc_header.app_id, xtra.remote_app_id)
		logging.debug("CQC %s: Sent App ID %d qubit id %d to %s",self.name,cqc_header.app_id,cmd.qubit_id, targetName)

		# Remove from active mapped qubits
		del self.factory.qubitList[(cqc_header.app_id, cmd.qubit_id)]

		return True

	@inlineCallbacks
	def cmd_recv(self, cqc_header, cmd, xtra):
		"""
		Receive qubit from another node. Block until qubit is received.
		"""
		logging.debug("CQC %s: Asking to receive for App ID %d",self.name,cqc_header.app_id)

		# First get the app_id and q_id
		app_id = cqc_header.app_id
		q_id = self.new_qubit_id(app_id)

		# This will block until a qubit is received.
		noQubit = True
		while(noQubit):
			virt_qubit = yield self.factory.virtRoot.callRemote("cqc_get_recv", cqc_header.app_id)
			if virt_qubit:
				noQubit = False
			else:
				time.sleep(0.1)

		logging.debug("CQC %s: Qubit received for app_id %d",self.name, cqc_header.app_id)

		# Once we have the qubit, add it to the local list and send a reply we received it. Note that we will
		# recheck whether it exists: it could have been added by another connection in the mean time
		try:
			self.factory._lock.acquire()

			if (app_id,q_id) in self.factory.qubitList:
				logging.debug("CQC %s: Qubit already in use (%d,%d)", self.name, app_id, q_id)
				self._send_back_cqc(cqc_header, CQC_ERR_INUSE)
				return False

			q = CQCQubit(q_id, int(time.time()), virt_qubit)
			self.factory.qubitList[(app_id,q_id)] = q
		finally:
			self.factory._lock.release()

		# Send message we received a qubit back
		# logging.debug("GOO")
		self._send_back_cqc(cqc_header, CQC_TP_RECV,length=CQC_NOTIFY_LENGTH)

		# Send notify header with qubit ID
		# logging.debug("GOO")
		hdr = CQCNotifyHeader();
		hdr.setVals(q_id, 0, 0,0,0, 0);
		msg = hdr.pack()
		self.transport.write(msg)
		logging.debug("CQC %s: Notify %s",self.name, hdr.printable())

		return True

	@inlineCallbacks
	def cmd_epr(self, cqc_header, cmd, xtra):
		"""
		Create EPR pair with another node.
		Depending on the ips and ports this will either create an EPR-pair and send one part, or just receive.
		"""

		#Get ip and port of this host
		host_ip=self.factory.host.ip
		host_port=self.factory.host.port
		host_combined=int(str(host_ip)+str(host_port))

		#Get ip and port of remote host
		remote_ip=xtra.remote_node
		remote_port=xtra.remote_port
		remote_combined=int(str(remote_ip)+str(remote_port))

		# Check that remote is a different host
		if host_combined == remote_combined:
			logging.debug("CQC %s: For making EPR, the hosts cannot be the same.",self.name)
			self._send_back_cqc(cqc_header,CQC_ERR_GENERAL)
			return False

		#Check if we are sending or receiving
		if host_combined < remote_combined:
			# We are sending
			app_id = cqc_header.app_id

			# Create the first qubit
			succ = yield self.cmd_new(cqc_header,cmd,xtra)
			if not succ:
				return False

			# Find a temporary unused qubit id for the second qubit
			for q_id2 in range(len(self.factory.qubitList)+1):
				if not ((app_id,q_id2) in self.factory.qubitList):
					break

			#Create commmand header for second qubit
			cmd2=CQCCmdHeader()
			cmd2.setVals(q_id2,None,None,None,None)

			# Create second qubit
			succ = yield self.cmd_new(cqc_header,cmd2,None)
			if not succ:
				return False

			# Produce EPR-pair
			succ = yield self.cmd_h(cqc_header,cmd,None)
			if not succ:
				return False
			xtra_cnot=CQCXtraHeader()
			xtra_cnot.setVals(q_id2,None,None,None,None,None)
			succ = yield self.cmd_cnot(cqc_header,cmd,xtra_cnot)
			if not succ:
				return False

			# Send second qubit
			succ = yield self.cmd_send(cqc_header,cmd2,xtra)
			if not succ:
				return False

			# Send message we received a qubit back
			self._send_back_cqc(cqc_header, CQC_TP_RECV,length=CQC_NOTIFY_LENGTH)

			# Send notify header with qubit ID
			hdr = CQCNotifyHeader();
			hdr.setVals(cmd.qubit_id, 0, 0,0,0, 0);
			msg = hdr.pack()
			self.transport.write(msg)
			logging.debug("CQC %s: Notify %s",self.name, hdr.printable())

			logging.debug("CQC %s: EPR Pair ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
			return True
		else:
			# We are receiving. self.cmd_recv sends a RECV message.
			succ = yield self.cmd_recv(cqc_header,cmd,None)
			if not succ:
				return False

			logging.debug("CQC %s: EPR Pair ID %d qubit id %d",self.name,cqc_header.app_id,cmd.qubit_id)
			return True

	@inlineCallbacks
	def cmd_new(self, cqc_header, cmd, xtra):
		# """
		# Request a new qubit. Since we don't need it, this python CQC just provides very crude timing information.
		# """

		# app_id = cqc_header.app_id
		# q_id = cmd.qubit_id

		# try:
		# 	self.factory._lock.acquire()
		# 	if (app_id,q_id) in self.factory.qubitList:
		# 		logging.debug("CQC %s: Qubit already in use (%d,%d)", self.name, app_id, q_id)
		# 		self._send_back_cqc(cqc_header, CQC_ERR_INUSE)
		# 		return False

		# 	virt = yield self.factory.virtRoot.callRemote("new_qubit_inreg",self.factory.qReg)
		# 	if not virt: # if no more qubits
		# 		raise quantumError("No more qubits available")
		# 	q = CQCQubit(cmd.qubit_id, int(time.time()), virt)
		# 	self.factory.qubitList[(app_id,q_id)] = q
		# 	logging.debug("CQC %s: Requested new qubit (%d,%d)",self.name,app_id, q_id)
		# except quantumError: # if no more qubits
		# 	logging.error("CQC %s: Maximum number of qubits reached.", self.name)
		# 	self._send_back_cqc(cqc_header, CQC_ERR_NOQUBIT)
		# 	self.factory._lock.release()
		# 	return False

		# self.factory._lock.release()
		# return True

		"""
		Request a new qubit. Since we don't need it, this python CQC just provides very crude timing information.
		"""

		app_id = cqc_header.app_id

		try:
			self.factory._lock.acquire()
			# if (app_id,q_id) in self.factory.qubitList:
			# 	logging.debug("CQC %s: Qubit already in use (%d,%d)", self.name, app_id, q_id)
			# 	self._send_back_cqc(cqc_header, CQC_ERR_INUSE)
			# 	return False

			virt = yield self.factory.virtRoot.callRemote("new_qubit_inreg",self.factory.qReg)
			if not virt: # if no more qubits
				raise quantumError("No more qubits available")

			q_id=self.new_qubit_id(app_id)
			q = CQCQubit(q_id, int(time.time()), virt)
			self.factory.qubitList[(app_id,q_id)] = q
			logging.debug("CQC %s: Requested new qubit (%d,%d)",self.name,app_id, q_id)

			# Send message we created a qubit back
			# logging.debug("GOO")
			self._send_back_cqc(cqc_header, CQC_TP_DONE,length=CQC_NOTIFY_LENGTH)

			# Send notify header with qubit ID
			hdr = CQCNotifyHeader();
			hdr.setVals(q_id, 0, 0,0,0, 0);
			msg = hdr.pack()
			self.transport.write(msg)
			logging.debug("CQC %s: Notify %s",self.name, hdr.printable())

		except quantumError: # if no more qubits
			logging.error("CQC %s: Maximum number of qubits reached.", self.name)
			self._send_back_cqc(cqc_header, CQC_ERR_NOQUBIT)
			self.factory._lock.release()
			return False

		self.factory._lock.release()
		return True

	def new_qubit_id(self,app_id):
		"""
		Returns a new unique qubit id for the specified app_id. Used by cmd_new and cmd_recv
		"""
		if app_id in self.next_q_id:
			q_id=self.next_q_id[app_id]
			self.next_q_id[app_id]+=1
			return q_id
		else:
			self.next_q_id[app_id]=1
			return 0


#######################################################################################################
#
# CQC Internal qubit object to translate to the native mode of SimulaQron
#

class CQCQubit:

	def __init__(self, qubit_id = 0, timestamp = 0, virt = 0):
		self.qubit_id = qubit_id;
		self.timestamp = timestamp;
		self.virt = virt;







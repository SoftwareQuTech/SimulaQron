
# Copyright (c) 2018, Stephanie Wehner and Axel Dahlberg
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
from twisted.internet.defer import inlineCallbacks

from SimulaQron.virtNode.basics import *
from SimulaQron.virtNode.quantum import *
from SimulaQron.general.hostConfig import *
from SimulaQron.virtNode.crudeSimulator import *

from SimulaQron.local.setup import *

from SimulaQron.cqc.backend.cqcConfig import *


from SimulaQron.cqc.backend.entInfoHeader import *
from SimulaQron.cqc.backend.cqcHeader import *
from abc import ABC, abstractmethod

"""
Abstract class. Classes that inherit this class define how to handle incoming cqc messages. 
"""





class CQCMessageHandler(ABC):

	def __init__(self, factory):
		# Functions to invoke when receiving a CQC Header of a certain type
		self.messageHandlers = {
			CQC_TP_HELLO: self.handle_hello,
			CQC_TP_COMMAND: self.handle_command,
			CQC_TP_FACTORY: self.handle_factory,
			CQC_TP_GET_TIME: self.handle_time
		}

		# Functions to invoke when receiving a certain command
		self.commandHandlers = {
			CQC_CMD_I: self.cmd_i,
			CQC_CMD_X: self.cmd_x,
			CQC_CMD_Y: self.cmd_y,
			CQC_CMD_Z: self.cmd_z,
			CQC_CMD_T: self.cmd_t,
			CQC_CMD_H: self.cmd_h,
			CQC_CMD_K: self.cmd_k,
			CQC_CMD_ROT_X: self.cmd_rotx,
			CQC_CMD_ROT_Y: self.cmd_roty,
			CQC_CMD_ROT_Z: self.cmd_rotz,
			CQC_CMD_CNOT: self.cmd_cnot,
			CQC_CMD_CPHASE: self.cmd_cphase,
			CQC_CMD_MEASURE: self.cmd_measure,
			CQC_CMD_MEASURE_INPLACE: self.cmd_measure_inplace,
			CQC_CMD_RESET: self.cmd_reset,
			CQC_CMD_SEND: self.cmd_send,
			CQC_CMD_RECV: self.cmd_recv,
			CQC_CMD_EPR: self.cmd_epr,
			CQC_CMD_EPR_RECV: self.cmd_epr_recv,
			CQC_CMD_NEW: self.cmd_new
		}

		# Convenience
		self.name = factory.name
		# self.protocol = protocol  # ugly, but for now I don't know a better way

	# @inlineCallbacks
	def handle_cqc_message(self, header, message):
		"""
		This calls the correct method to handle the cqcmessage, based on the type specified in the header
		"""
		if header.tp in self.messageHandlers:
			try:
				messages = self.messageHandlers[header.tp](header, message)
				return messages
			except UnknownQubitError as e:
				logging.error(str(e))
				return self.create_return_message(header.app_id, CQC_ERR_NOQUBIT)
		else:
			return self.create_return_message(header.app_id, CQC_ERR_UNSUPP)

	@staticmethod
	def create_return_message(app_id, msg_type, length=0):
		"""
		Creates a messaage that the protocol should send back
		:param app_id: the app_id to which the message should be send
		:param msg_type: the type of message to return
		:return: a new header message to be send back
		:param length: the length of additional message
		"""
		hdr = CQCHeader()
		hdr.setVals(CQC_VERSION, msg_type, app_id, length)
		return hdr.pack()

	@staticmethod
	def has_extra(cmd):
		"""
		Check whether this command includes an extra header with additional information.
		"""
		if cmd.instr == CQC_CMD_SEND:
			return True
		if cmd.instr == CQC_CMD_EPR:
			return True
		if cmd.instr == CQC_CMD_CNOT:
			return True
		if cmd.instr == CQC_CMD_CPHASE:
			return True
		if cmd.instr == CQC_CMD_ROT_X:
			return True
		if cmd.instr == CQC_CMD_ROT_Y:
			return True
		if cmd.instr == CQC_CMD_ROT_Z:
			return True
		if cmd.action:
			return True

		return False

	@inlineCallbacks
	def handle_command(self, header, data):
		"""
		Handle incoming command requests.
		"""
		logging.debug("CQC %s: Command received", self.name)
		# Run the entire command list, incl. actions after completion which here we will do instantly
		msgs, success, should_notify = yield self._process_command(header, header.length, data)
		if success and should_notify:
			# Send a notification that we are done if successful
			logging.debug("CQC %s: Command successful, sent done.", self.name)
			msgs.append(self.create_return_message(header.app_id, CQC_TP_DONE))
		return msgs

	@abstractmethod
	def _process_command(self, cqc_header, length, data):
		"""
			Process the commands - called recursively to also process additional command lists.
		"""
		pass

	@abstractmethod
	def handle_hello(self, header, data):
		pass

	@abstractmethod
	def handle_factory(self, header, data):
		pass

	@abstractmethod
	def handle_time(self, header, data):
		pass

	@abstractmethod
	def cmd_i(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_x(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_y(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_z(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_t(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_h(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_k(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_rotx(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_roty(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_rotz(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_cnot(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_cphase(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_measure(self, cqc_header, cmd, xtra, inplace=False):
		pass

	@abstractmethod
	def cmd_measure_inplace(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_reset(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_send(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_recv(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_epr(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_epr_recv(self, cqc_header, cmd, xtra):
		pass

	@abstractmethod
	def cmd_new(self, cqc_header, cmd, xtra, return_q_id=False, return_succ=False):
		pass


class SimulaqronCQCHandler(CQCMessageHandler):

	# Dictionary storing the next unique qubit id for each used app_id
	_next_q_id = {}

	# Dictionary storing the next unique entanglement id for each used (host_app_id,remote_node,remote_app_id)
	_next_ent_id = {}

	def __init__(self, factory):
		super().__init__(factory)
		self.factory = factory

		# Dictionary that keeps qubit dictorionaries for each application
		self.qubitList = {}

	@inlineCallbacks
	def _process_command(self, cqc_header, length, data):
		"""
			Process the commands - called recursively to also process additional command lists.
		"""
		cmd_data = data

		# Read in all the commands sent
		cur_length = 0
		should_notify = False
		return_messages = []
		while cur_length < length:
			cmd = CQCCmdHeader(cmd_data[cur_length:cur_length + CQC_CMD_HDR_LENGTH])
			newl = cur_length + CQC_CMD_HDR_LENGTH

			# Should we notify
			should_notify = cmd.notify

			# Check if this command includes an additional header
			if self.has_extra(cmd):
				if len(cmd_data) < (newl + CQC_CMD_XTRA_LENGTH):
					logging.debug("CQC %s: Missing XTRA Header", self.name)
				else:
					xtra = CQCXtraHeader(cmd_data[newl:newl + CQC_CMD_XTRA_LENGTH])
					newl = newl + CQC_CMD_XTRA_LENGTH
					logging.debug("CQC %s: Read XTRA Header: %s", self.name, xtra.printable())
			else:
				xtra = None

			# Run this command
			logging.debug("CQC %s: Executing command: %s", self.name, cmd.printable())
			if cmd.instr not in self.commandHandlers:
				logging.debug("CQC {}: Unknown command {}".format(self.name, cmd.instr))
				msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP)
				return_messages.append(msg)
				return return_messages

			msgs = yield self.commandHandlers[cmd.instr](cqc_header, cmd, xtra)
			if msgs is None:
				return return_messages, False, 0

			return_messages.extend(msgs)

			# Check if there are additional commands to execute afterwards
			if cmd.action:
				(msgs, succ, retNotify) = yield self._process_command(cqc_header, xtra.cmdLength, data[newl:newl + xtra.cmdLength])
				should_notify = (should_notify or retNotify)
				if not succ:
					return return_messages, False, 0
				return_messages.extend(msgs)
				newl = newl + xtra.cmdLength

			cur_length = newl
		return return_messages, True, should_notify

	def handle_hello(self, header, data):
		"""
		Hello just requires us to return hello - for testing availability.
		"""
		msg = self.create_return_message(header.app_id, CQC_TP_HELLO)
		return [msg]

	@inlineCallbacks
	def handle_factory(self, header, data):

		cmd_l = CQC_CMD_HDR_LENGTH
		xtra_l = CQC_CMD_XTRA_LENGTH

		# Get command header
		if len(data) < cmd_l:
			logging.debug("CQC %s: Missing CMD Header", self.name)
			return [self.create_return_message(header.app_id, CQC_ERR_UNSUPP)]
		cmd_header = CQCCmdHeader(data[:cmd_l])

		# Get xtra header
		if len(data) < (cmd_l + xtra_l):
			logging.debug("CQC %s: Missing XTRA Header", self.name)
			return [self.create_return_message(header.app_id, CQC_ERR_UNSUPP)]
		xtra_header = CQCXtraHeader(data[cmd_l:cmd_l + xtra_l])

		command = cmd_header.instr
		num_iter = xtra_header.step

		# Perform operation multiple times
		all_succ = True
		should_notify = cmd_header.notify
		return_messages = []
		for _ in range(num_iter):
			try:
				if self.has_extra(cmd_header):
					(msgs, succ, should_notify) = yield self._process_command(header, header.length, data)
				else:
					data = data[:cmd_l] + data[cmd_l + xtra_l:]
					(msgs, succ, should_notify) = yield self._process_command(header, header.length - xtra_l, data)
			except TypeError as e:
				# A type error can indicate that the qubit is not active
				msg = self.create_return_message(header.app_id, CQC_ERR_NOQUBIT)
				# return_messages.add(msg)
				return [msg]
			all_succ = (all_succ and succ)
			return_messages.extend(msgs)
		if all_succ:
			if should_notify:
				# Send a notification that we are done if successful
				logging.debug("CQC %s: Command successful, sent done.", self.name)
				return_messages.append(self.create_return_message(header.app_id, CQC_TP_DONE))
		return return_messages

	def handle_time(self, header, data):

		# Read the command header to learn the qubit ID
		raw_cmd_header = data[:CQC_CMD_HDR_LENGTH]
		cmd_hdr = CQCCmdHeader(raw_cmd_header)

		# Get the qubit list
		q_list = self.factory.qubitList

		# Lookup the desired qubit
		if (header.app_id, cmd_hdr.qubit_id) in q_list:
			q = q_list[(header.app_id, cmd_hdr.qubit_id)]
		else:
			# Specified qubit is unknown
			return self.create_return_message(header.app_id, CQC_ERR_NOQUBIT)

		# Craft reply
		# First send an appropriate CQC Header
		cqc_msg = self.create_return_message(header.app_id, CQC_TP_INF_TIME, length=CQC_NOTIFY_LENGTH)

		# Then we send a notify header with the timing details
		notify = CQCNotifyHeader()
		notify.setVals(cmd_hdr.qubit_id, 0, 0, 0, 0, q.timestamp)
		msg = notify.pack()
		return [cqc_msg, msg]

	def cmd_i(self, cqc_header, cmd, xtra):
		"""
		Do nothing. In reality we would wait a timestep but in SimulaQron we just do nothing.
		"""
		logging.debug("CQC %s: Doing Nothing to App ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
		return []

	def cmd_x(self, cqc_header, cmd, xtra):
		"""
		Apply X Gate
		"""
		return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_X")

	def cmd_y(self, cqc_header, cmd, xtra):
		"""
		Apply Y Gate
		"""
		return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_Y")

	def cmd_z(self, cqc_header, cmd, xtra):
		"""
		Apply Z Gate
		"""
		return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_Z")

	def cmd_t(self, cqc_header, cmd, xtra):
		"""
		Apply T Gate
		"""
		return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_T")

	def cmd_h(self, cqc_header, cmd, xtra):
		"""
		Apply H Gate
		"""
		return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_H")

	def cmd_k(self, cqc_header, cmd, xtra):
		"""
		Apply K Gate
		"""
		return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_K")

	@inlineCallbacks
	def apply_rotation(self, cqc_header, cmd, xtra, axis):
		"""
		Apply a rotation of the qubit specified in cmd with an angle specified in xtra
		around the axis
		"""
		logging.debug("CQC %s: Applying a rotation around %s to App ID %d qubit id %d", self.name, axis, cqc_header.app_id, cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit", self.name)
			return self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT)

		yield virt_qubit.callRemote("apply_rotation", axis , 2 * np.pi/256 * xtra.step)
		return []

	def cmd_rotx(self, cqc_header, cmd, xtra):
		"""
		Rotate around x axis
		"""
		return self.apply_rotation(cqc_header, cmd, xtra, [1, 0, 0])

	def cmd_roty(self, cqc_header, cmd, xtra):
		"""
		Rotate around y axis
		"""
		return self.apply_rotation(cqc_header, cmd, xtra, [0, 1, 0])

	def cmd_rotz(self, cqc_header, cmd, xtra):
		"""
		Rotate around z axis
		"""
		return self.apply_rotation(cqc_header, cmd, xtra, [0, 0, 1])

	def cmd_cnot(self, cqc_header, cmd, xtra):
		"""
		Apply CNOT Gate
		"""
		return self.apply_two_qubit_gate(cqc_header, cmd, xtra, "cnot_onto")

	def cmd_cphase(self, cqc_header, cmd, xtra):
		"""
		Apply CPHASE Gate
		"""
		return self.apply_two_qubit_gate(cqc_header, cmd, xtra, "cphase_onto")

	@inlineCallbacks
	def cmd_measure(self, cqc_header, cmd, xtra, inplace=False):
		"""
		Measure
		"""
		logging.debug("CQC %s: Measuring App ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit", self.name)
			return self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT)

		outcome = yield virt_qubit.callRemote("measure", inplace)
		if outcome is None:
			logging.debug("CQC %s: Measurement failed", self.name)
			return self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL)

		logging.debug("CQC %s: Measured outcome %d", self.name, outcome)
		# Send the outcome back as MEASOUT
		cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_MEASOUT, length=CQC_NOTIFY_LENGTH)

		# Send notify header with outcome
		hdr = CQCNotifyHeader()
		hdr.setVals(cmd.qubit_id, outcome, 0, 0, 0, 0)
		msg = hdr.pack()
		# self.protocol.transport.write(msg)
		logging.debug("CQC %s: Notify %s", self.name, hdr.printable())

		if not inplace:
			# Remove from active mapped qubits
			del self.factory.qubitList[(cqc_header.app_id, cmd.qubit_id)]

		return [cqc_msg, msg]

	@inlineCallbacks
	def cmd_measure_inplace(self, cqc_header, cmd, xtra):

		# Call measure with inplace=True
		succ = yield self.cmd_measure(cqc_header, cmd, xtra, inplace=True)

		return succ

	@inlineCallbacks
	def cmd_reset(self, cqc_header, cmd, xtra):
		"""
		Reset Qubit to |0>
		"""
		logging.debug("CQC %s: Reset App ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit", self.name)
			return False

		outcome = yield virt_qubit.callRemote("measure", inplace=True)

		# If state is |1> do correction
		if outcome:
			yield virt_qubit.callRemote("apply_X")
		return []

	@inlineCallbacks
	def cmd_send(self, cqc_header, cmd, xtra):
		"""
		Send qubit to another node.
		"""

		# Lookup the name of the remote node used within SimulaQron
		target_name = self.factory.lookup(xtra.remote_node, xtra.remote_port)
		if target_name is None:
			logging.debug("CQC %s: Remote node not found %s", self.name, xtra.printable())
			return False

		# Check so that it is not the same node
		if self.name == target_name:
			logging.debug("CQC %s: Trying to send from node to itself.", self.name)
			# self.protocol._send_back_cqc(cqc_header, CQC_ERR_GENERAL)
			return self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL)

		# Lookup the virtual qubit from identifier
		virt_num = yield self.get_virt_qubit_indep(cqc_header, cmd.qubit_id)
		if virt_num < 0:
			logging.debug("CQC %s: No such qubit", self.name)
			return False

		# Send instruction to transfer the qubit
		yield self.factory.virtRoot.callRemote("cqc_send_qubit", virt_num, target_name, cqc_header.app_id, xtra.remote_app_id)
		logging.debug("CQC %s: Sent App ID %d qubit id %d to %s", self.name, cqc_header.app_id, cmd.qubit_id, target_name)

		# Remove from active mapped qubits
		del self.factory.qubitList[(cqc_header.app_id, cmd.qubit_id)]

		return []

	@inlineCallbacks
	def cmd_recv(self, cqc_header, cmd, xtra):
		"""
		Receive qubit from another node. Block until qubit is received.
		"""
		logging.debug("CQC %s: Asking to receive for App ID %d", self.name, cqc_header.app_id)

		# First get the app_id
		app_id = cqc_header.app_id

		# This will block until a qubit is received.
		no_qubit = True
		virt_qubit = None
		for _ in range(CQC_CONF_RECV_TIMEOUT):
			virt_qubit = yield self.factory.virtRoot.callRemote("cqc_get_recv", cqc_header.app_id)
			if virt_qubit:
				no_qubit = False
				break
			else:
				time.sleep(0.1)
		if no_qubit:
			logging.debug("CQC %s: TIMEOUT, no qubit received.", self.name)
			# self.protocol._send_back_cqc(cqc_header, CQC_ERR_TIMEOUT)
			return self.create_return_message(cqc_header.app_id, CQC_ERR_TIMEOUT)

		logging.debug("CQC %s: Qubit received for app_id %d",self.name, cqc_header.app_id)

		# Once we have the qubit, add it to the local list and send a reply we received it. Note that we will
		# recheck whether it exists: it could have been added by another connection in the mean time
		try:
			self.factory._lock.acquire()

			# Get new qubit ID
			q_id = self.new_qubit_id(app_id)

			if (app_id, q_id) in self.factory.qubitList:
				logging.debug("CQC %s: Qubit already in use (%d,%d)", self.name, app_id, q_id)
				# self.protocol._send_back_cqc(cqc_header, CQC_ERR_INUSE)
				return self.create_return_message(cqc_header.app_id, CQC_ERR_INUSE)

			q = CQCQubit(q_id, int(time.time()), virt_qubit)
			self.factory.qubitList[(app_id, q_id)] = q
		finally:
			self.factory._lock.release()

		# Send message we received a qubit back
		# logging.debug("GOO")
		recv_msg = self.create_return_message(cqc_header.app_id, CQC_TP_RECV, length=CQC_NOTIFY_LENGTH)

		# Send notify header with qubit ID
		# logging.debug("GOO")
		hdr = CQCNotifyHeader()
		hdr.setVals(q_id, 0, 0, 0, 0, 0)
		msg = hdr.pack()
		# self.protocol.transport.write(msg)
		logging.debug("CQC %s: Notify %s", self.name, hdr.printable())

		return [recv_msg, msg]

	@inlineCallbacks
	def cmd_epr(self, cqc_header, cmd, xtra):
		"""
		Create EPR pair with another node.
		Depending on the ips and ports this will either create an EPR-pair and send one part, or just receive.
		"""

		# Get ip and port of this host
		host_node = self.factory.host.ip
		host_port = self.factory.host.port
		host_app_id = cqc_header.app_id

		# Get ip and port of remote host
		remote_node = xtra.remote_node
		remote_port = xtra.remote_port
		remote_app_id = xtra.remote_app_id

		# Messages to write back
		return_messages = []

		# Create the first qubit
		(msgs, succ, q_id1) = yield self.cmd_new(cqc_header, cmd, xtra, return_q_id=True, return_succ=True)
		if not succ:
			return False
		return_messages.extend(msgs)

		# Create the second qubit
		(msgs, succ, q_id2) = yield self.cmd_new(cqc_header, cmd, xtra, return_q_id=True, return_succ=True)
		if not succ:
			return False
		return_messages.extend(msgs)

		# Create headers for qubits
		cmd1 = CQCCmdHeader()
		cmd1.setVals(q_id1, CQC_CMD_H, 0, 0, 0)

		cmd2 = CQCCmdHeader()
		cmd2.setVals(q_id2, 0, 0, 0, 0)

		xtra_cnot = CQCXtraHeader()
		xtra_cnot.setVals(q_id2, 0, 0, 0, 0, 0)

		# Produce EPR-pair
		msgs = yield self.cmd_h(cqc_header, cmd1, None)
		# Should not give back any messages, if it does, send it back
		if msgs is None or len(msgs) > 0:
			return_messages.extend(msgs)
			return return_messages
		msgs = yield self.cmd_cnot(cqc_header, cmd1, xtra_cnot)
		if msgs is None or len(msgs) > 0:
			return_messages.extend(msgs)
			return return_messages

		# Get entanglement id XXX lock here?
		ent_id = self.new_ent_id(host_app_id, remote_node, remote_app_id)

		# Prepare ent_info header with entanglement information
		ent_info = EntInfoHeader()
		ent_info.setVals(host_node, host_port, host_app_id, remote_node, remote_port, remote_app_id, ent_id, int(time.time()), int(time.time()), 0, 1)
		# Send second qubit
		succ = yield self.send_epr_half(cqc_header, cmd2, xtra, ent_info)
		if not succ:
			return False

		# Send message we created EPR pair
		msg_ok = self.create_return_message(cqc_header.app_id, CQC_TP_EPR_OK, length=CQC_NOTIFY_LENGTH+ENT_INFO_LENGTH)

		return_messages.append(msg_ok)

		# Send notify header with qubit ID
		hdr = CQCNotifyHeader()
		hdr.setVals(q_id1, 0, 0, 0, 0, 0)
		msg_notify = hdr.pack()
		return_messages.append(msg_notify)

		# self.protocol.transport.write(msg)
		logging.debug("CQC %s: Notify %s", self.name, hdr.printable())

		# Send entanglement info
		msg_ent_info = ent_info.pack()
		return_messages.append(msg_ent_info)
		# self.protocol.transport.write(msg)
		logging.debug("CQC %s: Entanglement information %s", self.name, ent_info.printable())

		logging.debug("CQC %s: EPR Pair ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
		return return_messages

	@inlineCallbacks
	def send_epr_half(self, cqc_header, cmd, xtra, ent_info):
		"""
		Send qubit to another node.
		"""
		# Lookup the virtual qubit from identifier
		virt_num = yield self.get_virt_qubit_indep(cqc_header, cmd.qubit_id)
		if virt_num < 0:
			logging.debug("CQC %s: No such qubit", self.name)
			return False

		# Lookup the name of the remote node used within SimulaQron
		target_name = self.factory.lookup(xtra.remote_node, xtra.remote_port)
		if target_name is None:
			logging.debug("CQC %s: Remote node not found %s", self.name, xtra.printable())
			return False

		# Prepare update raw entanglement information header
		updated_ent_info = EntInfoHeader(ent_info.pack())
		updated_ent_info.switch_nodes()
		raw_updated_ent_info = updated_ent_info.pack()
		# Send instruction to transfer the qubit
		yield self.factory.virtRoot.callRemote("cqc_send_epr_half", virt_num, target_name, cqc_header.app_id, xtra.remote_app_id, raw_updated_ent_info)
		logging.debug("CQC %s: Sent App ID %d half a EPR pair as qubit id %d to %s", self.name, cqc_header.app_id, cmd.qubit_id, target_name)
		# Remove from active mapped qubits
		del self.factory.qubitList[(cqc_header.app_id, cmd.qubit_id)]

		return True

	@inlineCallbacks
	def cmd_epr_recv(self, cqc_header, cmd, xtra):
		"""
		Receive half of epr from another node. Block until qubit is received.
		"""
		logging.debug("CQC %s: Asking to receive for App ID %d", self.name, cqc_header.app_id)

		# First get the app_id and q_id
		app_id = cqc_header.app_id
		q_id = self.new_qubit_id(app_id)

		# This will block until a qubit is received.
		no_qubit = True
		virt_qubit = None
		ent_info = None
		for _ in range(CQC_CONF_RECV_EPR_TIMEOUT):
			data = yield self.factory.virtRoot.callRemote("cqc_get_epr_recv", cqc_header.app_id)
			if data:
				no_qubit = False
				(virt_qubit, rawEntInfo) = data
				ent_info = EntInfoHeader(rawEntInfo)
				break
			else:
				time.sleep(0.1)
		if no_qubit:
			logging.debug("CQC %s: TIMEOUT, no qubit received.", self.name)
			# self.protocol._send_back_cqc(cqc_header, CQC_ERR_TIMEOUT)
			return self.create_return_message(cqc_header.app_id, CQC_ERR_TIMEOUT)

		logging.debug("CQC %s: Qubit received for app_id %d", self.name, cqc_header.app_id)

		# Once we have the qubit, add it to the local list and send a reply we received it. Note that we will
		# recheck whether it exists: it could have been added by another connection in the mean time
		try:
			self.factory._lock.acquire()

			if (app_id, q_id) in self.factory.qubitList:
				logging.debug("CQC %s: Qubit already in use (%d,%d)", self.name, app_id, q_id)
				# self.protocol._send_back_cqc(cqc_header, CQC_ERR_INUSE)
				return self.create_return_message(cqc_header.app_id, CQC_ERR_INUSE)

			q = CQCQubit(q_id, int(time.time()), virt_qubit)
			self.factory.qubitList[(app_id, q_id)] = q
		finally:
			self.factory._lock.release()

		# Send message we received a qubit back
		cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_EPR_OK, length=CQC_NOTIFY_LENGTH+ENT_INFO_LENGTH)

		# Send notify header with qubit ID
		hdr = CQCNotifyHeader()
		hdr.setVals(q_id, 0, 0, 0, 0, 0)
		notify_msg = hdr.pack()
		# self.protocol.transport.write(msg)
		logging.debug("CQC %s: Notify %s", self.name, hdr.printable())

		# Send entanglement info
		ent_info_msg = ent_info.pack()
		# self.protocol.transport.write(msg)
		logging.debug("CQC %s: Entanglement information %s", self.name, ent_info.printable())

		logging.debug("CQC %s: EPR Pair ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)

		return [cqc_msg, notify_msg, ent_info_msg]

	@inlineCallbacks
	def cmd_new(self, cqc_header, cmd, xtra, return_q_id=False, return_succ=False):
		"""
		Request a new qubit. Since we don't need it, this python CQC just provides very crude timing information.
		(return_q_id is used internally)
		"""
		app_id = cqc_header.app_id
		return_messages = []
		try:
			self.factory._lock.acquire()

			virt = yield self.factory.virtRoot.callRemote("new_qubit_inreg", self.factory.qReg)
			if not virt:  # if no more qubits
				raise quantumError("No more qubits available")

			q_id = self.new_qubit_id(app_id)
			q = CQCQubit(q_id, int(time.time()), virt)
			self.factory.qubitList[(app_id, q_id)] = q
			logging.debug("CQC %s: Requested new qubit (%d,%d)", self.name, app_id, q_id)

			if not return_q_id:
				# Send message we created a qubit back
				# logging.debug("GOO")
				cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_NEW_OK, length=CQC_NOTIFY_LENGTH)
				# self.protocol.transport.write(cqc_msg)
				return_messages.append(cqc_msg)

				# Send notify header with qubit ID
				hdr = CQCNotifyHeader()
				hdr.setVals(q_id, 0, 0, 0, 0, 0)
				msg = hdr.pack()
				# self.protocol.transport.write(msg)
				logging.debug("CQC %s: Notify %s", self.name, hdr.printable())
				return_messages.append(msg)

		except quantumError:  # if no more qubits
			logging.error("CQC %s: Maximum number of qubits reached.", self.name)
			msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT)
			return_messages.append(msg)
			self.factory._lock.release()
			if return_q_id:
				return return_messages, False, None
			elif return_succ:
				return False
			else:
				return msg
		self.factory._lock.release()
		if return_q_id:
			return return_messages, True, q_id
		elif return_succ:
			return return_messages, True
		else:
			return return_messages

	@inlineCallbacks
	def apply_single_qubit_gate(self, cqc_header, qubit_id, gate):
		logging.debug("CQC %s: Applying X to App ID %s qubit id %d", self.name, gate, qubit_id)
		virt_qubit = self.get_virt_qubit(cqc_header, qubit_id)
		if not virt_qubit:
			logging.debug("CQC %s: No such qubit", self.name)
			return self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT)

		yield virt_qubit.callRemote(gate)
		return []

	@inlineCallbacks
	def apply_two_qubit_gate(self, cqc_header, cmd, xtra, gate):
		if not xtra:
			logging.debug("CQC %s: Missing XTRA Header", self.name)
			return False
		#
		logging.debug("CQC %s: Applying %s to App ID %d qubit id %d target %d", self.name, gate, cqc_header.app_id, cmd.qubit_id, xtra.qubit_id)
		control = self.get_virt_qubit(cqc_header, cmd.qubit_id)
		target = self.get_virt_qubit(cqc_header, xtra.qubit_id)
		if not control or not target:
			return False

		yield control.callRemote(gate, target)
		# res = yield self.apply_two_qubit_gate(cqc_header, cmd.qubit_id, xtra.qubit.id, "cnot_onto")
		return []

	def get_virt_qubit(self, header, qubit_id):
		"""
		Get reference to the virtual qubit reference in SimulaQron given app and qubit id, if it exists.
		If not found, send back no qubit error.

		Caution: Twisted PB does not allow references to objects to be passed back between connections.
		If you need to pass a qubit reference back to the Twisted PB on a _different_ connection,
		then use get_virt_qubit_indep below.
		"""
		if not (header.app_id, qubit_id) in self.factory.qubitList:
			raise UnknownQubitError("CQC {}: Qubit not found".format(self.name))
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
			return -1

		num = yield general_ref.callRemote("get_virt_num")
		# logging.debug("GOT NUMBER %d XXX",num)
		return num

	@staticmethod
	def new_qubit_id(app_id):
		"""
		Returns a new unique qubit id for the specified app_id. Used by cmd_new and cmd_recv
		"""
		if app_id in SimulaqronCQCHandler._next_q_id:
			q_id = SimulaqronCQCHandler._next_q_id[app_id]
			SimulaqronCQCHandler._next_q_id[app_id] += 1
			return q_id
		else:
			"""
			Returns a new unique qubit id for the specified app_id. Used by cmd_new and cmd_recv
			"""
			if app_id in SimulaqronCQCHandler._next_q_id:
				q_id = SimulaqronCQCHandler._next_q_id[app_id]
				SimulaqronCQCHandler._next_q_id[app_id] += 1
				return q_id
			else:
				SimulaqronCQCHandler._next_q_id[app_id] = 1
				return 0

	@staticmethod
	def new_ent_id(host_app_id, remote_node, remote_app_id):
		"""
		Returns a new unique entanglement id for the specified host_app_id, remote_node and remote_app_id. Used by cmd_epr.
		"""
		pair_id = (host_app_id, remote_node, remote_app_id)
		if pair_id in SimulaqronCQCHandler._next_ent_id:
			ent_id = SimulaqronCQCHandler._next_ent_id[pair_id]
			SimulaqronCQCHandler._next_ent_id[pair_id] += 1
			return ent_id
		else:
			SimulaqronCQCHandler._next_ent_id[pair_id] = 1
			return 0


class UnknownQubitError(Exception):

	def __init__(self, message):
		super.__init__(message)
#######################################################################################################
#
# CQC Internal qubit object to translate to the native mode of SimulaQron
#

class CQCQubit:

	def __init__(self, qubit_id=0, timestamp=0, virt=0):
		self.qubit_id = qubit_id
		self.timestamp = timestamp
		self.virt = virt

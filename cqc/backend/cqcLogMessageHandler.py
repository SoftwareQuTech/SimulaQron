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

"""
This class interfaces cqcMessageHandler, and is for testing purposes only
"""

from SimulaQron.cqc.backend.cqcMessageHandler import CQCMessageHandler
from SimulaQron.cqc.backend.cqcHeader import *

import time
import os
import json

from SimulaQron.cqc.backend.entInfoHeader import EntInfoHeader, ENT_INFO_LENGTH


class CQCLogMessageHandler(CQCMessageHandler):
	file = None
	dir_path = os.path.dirname(os.path.realpath(__file__))
	cur_qubit_id = 0
	logData = []

	def __init__(self, factory):
		super().__init__(factory)
		self.factory = factory
		CQCLogMessageHandler.file = "{}/logFile{}.json".format(CQCLogMessageHandler.dir_path, factory.name)

	def _process_command(self, cqc_header, length, data):
		"""
			Process the commands - called recursively to also process additional command lists.
		"""
		cmd_data = data

		# Read in all the commands sent
		cur_length = 0
		should_notify = None
		return_messages = []
		while cur_length < length:
			cmd = CQCCmdHeader(cmd_data[cur_length:cur_length + CQC_CMD_HDR_LENGTH])
			newl = cur_length + cmd.HDR_LENGTH

			# Should we notify
			should_notify = should_notify or cmd.notify

			# Create the extra header if it exist
			try:
				xtra = self.create_extra_header(cmd, cmd_data[newl:], cqc_header.version)
			except IndexError:
				xtra = None
				logging.debug("CQC %s: Missing XTRA Header", self.name)

			if xtra is not None:
				newl += xtra.HDR_LENGTH
				logging.debug("CQC %s: Read XTRA Header: %s", self.name, xtra.printable())

			# Run this command
			logging.debug("CQC %s: Executing command: %s", self.name, cmd.printable())
			if cmd.instr not in self.commandHandlers:
				logging.debug("CQC {}: Unknown command {}".format(self.name, cmd.instr))
				msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP)
				return_messages.append(msg)
				return return_messages
			msgs = self.commandHandlers[cmd.instr](cqc_header, cmd, xtra)
			if msgs is None:
				return return_messages, False, 0

			return_messages.extend(msgs)

			# Check if there are additional commands to execute afterwards
			if cmd.action:
				sequence_header = CQCSequenceHeader(data[newl: newl +CQCSequenceHeader.HDR_LENGTH])
				newl += sequence_header.HDR_LENGTH
				logging.debug("CQC %s: Reading extra action commands", self.name)
				(msgs, succ, retNotify) = self._process_command(cqc_header, sequence_header.cmd_length,
																	  data[newl:newl + sequence_header.cmd_length])
				should_notify = (should_notify or retNotify)
				if not succ:
					return return_messages, False, 0
				return_messages.extend(msgs)
				newl = newl + sequence_header.cmd_length

			cur_length = newl
		return return_messages, True, should_notify

	@classmethod
	def parse_data(cls, header, cmd, xtra, comment):
		subdata = {}
		subdata['comment'] = comment
		subdata['cqc_header'] = cls.parse_header(header)
		subdata['cmd_header'] = cls.parse_cmd(cmd)
		if xtra:
			subdata['xtra_header'] = cls.parse_xtra(xtra)
		cls.logData.append(subdata)
		with open(cls.file, 'w') as outfile:
			json.dump(cls.logData, outfile)

	@classmethod
	def parse_handle_data(cls, header, data, comment):
		cmd_l = CQC_CMD_HDR_LENGTH
		xtra_l = CQC_CMD_XTRA_LENGTH
		subdata = {}
		subdata['comment'] = comment
		subdata['cqc_header'] = cls.parse_header(header)
		if len(data) >= cmd_l:
			subdata['cmd_header'] = cls.parse_cmd(CQCCmdHeader(data[:cmd_l]))
		if len(data) >= cmd_l + xtra_l:
			subdata['xtra_header'] = cls.parse_xtra(CQCXtraHeader(data[cmd_l:cmd_l + xtra_l]))
		cls.logData.append(subdata)
		with open(cls.file, 'w') as outfile:
			json.dump(cls.logData, outfile)

	@classmethod
	def parse_handle_factory(cls, header, data, comment):
		subdata = {}
		subdata['comment'] = comment
		subdata['cqc_header'] = cls.parse_header(header)
		fact_hdr = CQCFactoryHeader(data[:CQCFactoryHeader.HDR_LENGTH])
		subdata['factory_iterations'] = fact_hdr.num_iter
		subdata['notify'] = fact_hdr.notify
		cls.logData.append(subdata)
		with open(cls.file, 'w') as outfile:
			json.dump(cls.logData, outfile)

	@classmethod
	def parse_header(cls, header):
		header_data = {}
		header_data['type'] = header.tp
		header_data['app_id'] = header.app_id
		header_data['header_length'] = header.length
		header_data['is_set'] = header.is_set
		return header_data

	@classmethod
	def parse_cmd(cls, cmd):
		cmd_data = {}
		cmd_data['notify'] = cmd.notify
		cmd_data['block'] = cmd.block
		cmd_data['action'] = cmd.action
		cmd_data['is_set'] = cmd.is_set
		cmd_data['qubit_id'] = cmd.qubit_id
		cmd_data['instruction'] = cmd.instr
		return cmd_data

	@classmethod
	def parse_xtra(cls, xtra):
		if isinstance(xtra, CQCCommunicationHeader):
			return cls.parse_com_hdr(xtra)
		if isinstance(xtra, CQCXtraQubitHeader):
			return cls.parse_xtra_qubit_hdr(xtra)
		if isinstance(xtra, CQCRotationHeader):
			return cls.parse_rot_hdr(xtra)
		xtra_data = {}
		xtra_data['is_set'] = xtra.is_set
		xtra_data['qubit_id'] = xtra.qubit_id
		xtra_data['step'] = xtra.step
		xtra_data['remote_app_id'] = xtra.remote_app_id
		xtra_data['remote_node'] = xtra.remote_node
		xtra_data['remote_port'] = xtra.remote_port
		xtra_data['cmdLength'] = xtra.cmdLength
		return xtra_data


	@classmethod
	def parse_rot_hdr(cls, com_hdr):
		"""
		Communication header
		"""
		rot_data = {}
		rot_data['type'] = "Rotation header"
		rot_data['step'] = com_hdr.step
		return rot_data

	@classmethod
	def parse_com_hdr(cls, com_hdr):
		"""
		Communication header
		"""
		com_data = {}
		com_data['type'] = "Communication header"
		com_data['remote_app_id'] = com_hdr.remote_app_id
		com_data['remote_node'] = com_hdr.remote_node
		com_data['remote_port'] = com_hdr.remote_port
		return com_data

	@classmethod
	def parse_xtra_qubit_hdr(cls, com_hdr):
		"""
		Communication header
		"""
		com_data = {}
		com_data['type'] = "Extra qubit header"
		com_data['qubit_id'] = com_hdr.qubit_id
		return com_data

	def handle_hello(self, header, data):
		"""
		Hello just requires us to return hello - for testing availability.
		"""
		self.parse_handle_data(header, data, "Handle Hello")
		hdr = CQCHeader()
		hdr.setVals(CQC_VERSION, CQC_TP_HELLO, header.app_id, 0)
		msg = hdr.pack()
		return [msg]

	def handle_factory(self, header, data):
		# Calls process_command, which should also log
		self.parse_handle_factory(header, data, "Handle factory")
		fact_l = CQCFactoryHeader.HDR_LENGTH

		# Get factory header
		if len(data) < header.length:
			# logging.debug("CQC %s: Missing factory Header", self.name)
			return [self.create_return_message(header.app_id, CQC_ERR_UNSUPP)]
		fact_header = CQCFactoryHeader(data[:fact_l])

		num_iter = fact_header.num_iter

		# Perform operation multiple times
		all_succ = True
		should_notify = fact_header.notify
		return_messages = []
		for i in range(num_iter):
			msgs, succ, _ = self._process_command(header, header.length - fact_l, data[fact_l:])
			all_succ = all_succ and succ
			return_messages.extend(msgs)
		if all_succ:
			if should_notify:
				# Send a notification that we are done if successful
				return_messages.append(self.create_return_message(header.app_id, CQC_TP_DONE))
				# logging.debug("CQC %s: Command successful, sent done.", self.name)

		return return_messages

	def handle_time(self, header, data):
		self.parse_handle_data(header, data, "Handle time")
		# Read the command header to learn the qubit ID
		raw_cmd_header = data[:CQC_CMD_HDR_LENGTH]
		cmd_hdr = CQCCmdHeader(raw_cmd_header)
		# Craft reply
		# First send an appropriate CQC Header
		cqc_msg = self.create_return_message(header.app_id, CQC_TP_INF_TIME, length=CQC_NOTIFY_LENGTH)

		# Then we send a notify header with the timing details
		# We do not have a qubit, so no timestamp either.
		# So let's send back some random date
		datetime = 758505600
		notify = CQCNotifyHeader()
		notify.setVals(cmd_hdr.qubit_id, 0, 0, 0, 0, datetime)
		msg = notify.pack()
		return [cqc_msg, msg]

	def cmd_i(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Identity")
		return []

	def cmd_x(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "X gate")
		return []

	def cmd_y(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Y gate")
		return []

	def cmd_z(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Z gate")
		return []

	def cmd_t(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "T gate")
		return []

	def cmd_h(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "H gate")
		return []

	def cmd_k(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "K gate")
		return []

	def cmd_rotx(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Rotate x")
		return []

	def cmd_roty(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Rotate y")
		return []

	def cmd_rotz(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Rotate z")
		return []

	def cmd_cnot(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "CNOT gate")
		return []

	def cmd_cphase(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "CPhase gate")
		return []

	def cmd_measure(self, cqc_header, cmd, xtra, inplace=False):
		self.parse_data(cqc_header, cmd, xtra, "Measure")
		# We'll always have 2 as outcome
		cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_MEASOUT, length=CQC_NOTIFY_LENGTH)

		outcome = 2
		hdr = CQCNotifyHeader()
		hdr.setVals(cmd.qubit_id, outcome, 0, 0, 0, 0)
		msg = hdr.pack()
		return [cqc_msg, msg]

	def cmd_measure_inplace(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Measure in place")
		# We'll always have 2 as outcome
		cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_MEASOUT, length=CQC_NOTIFY_LENGTH)

		outcome = 2
		hdr = CQCNotifyHeader()
		hdr.setVals(cmd.qubit_id, outcome, 0, 0, 0, 0)
		msg = hdr.pack()
		return [cqc_msg, msg]

	def cmd_reset(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Rest")
		return []

	def cmd_send(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Send")
		return []

	def cmd_recv(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Receive")
		q_id = CQCLogMessageHandler.cur_qubit_id
		CQCLogMessageHandler.cur_qubit_id += 1

		recv_msg = self.create_return_message(cqc_header.app_id, CQC_TP_RECV, length=CQC_NOTIFY_LENGTH)
		hdr = CQCNotifyHeader()
		hdr.setVals(q_id, 0, 0, 0, 0, 0)
		msg = hdr.pack()
		return [recv_msg, msg]

	def cmd_epr(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Create EPR")

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
		(msgs, succ, q_id1) = self.cmd_new(cqc_header, cmd, xtra, return_q_id=True, return_succ=True)
		if not succ:
			return False
		return_messages.extend(msgs)

		# Create the second qubit
		(msgs, succ, q_id2) = self.cmd_new(cqc_header, cmd, xtra, return_q_id=True, return_succ=True)
		if not succ:
			return False
		return_messages.extend(msgs)

		# Create headers for qubits
		cmd1 = CQCCmdHeader()
		cmd1.setVals(q_id1, 0, 0, 0, 0)

		cmd2 = CQCCmdHeader()
		cmd2.setVals(q_id2, 0, 0, 0, 0)

		xtra_cnot = CQCXtraQubitHeader()
		xtra_cnot.setVals(q_id2)

		# Produce EPR-pair
		msgs = self.cmd_h(cqc_header, cmd1, None)
		# Should not give back any messages, if it does, send it back
		if msgs is None or len(msgs) > 0:
			return_messages.extend(msgs)
			return return_messages
		msgs = self.cmd_cnot(cqc_header, cmd1, xtra_cnot)
		if msgs is None or len(msgs) > 0:
			return_messages.extend(msgs)
			return return_messages

		msg_ok = self.create_return_message(cqc_header.app_id, CQC_TP_EPR_OK,
											length=CQC_NOTIFY_LENGTH + ENT_INFO_LENGTH)
		return_messages.append(msg_ok)

		hdr = CQCNotifyHeader()
		hdr.setVals(q_id1, 0, 0, 0, 0, 0)
		msg_notify = hdr.pack()
		return_messages.append(msg_notify)

		logging.debug("CQC %s: Notify %s", self.name, hdr.printable())

		# Send entanglement info
		ent_id = 1
		ent_info = EntInfoHeader()
		ent_info.setVals(host_node, host_port, host_app_id, remote_node, remote_port, remote_app_id, ent_id,
						 int(time.time()), int(time.time()), 0, 1)
		msg_ent_info = ent_info.pack()
		return_messages.append(msg_ent_info)

		return return_messages

	def cmd_epr_recv(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Receive EPR")
		q_id = CQCLogMessageHandler.cur_qubit_id
		CQCLogMessageHandler.cur_qubit_id += 1

		# We're not sending the entanglement info atm, because we do not have any

		cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_RECV, length=CQC_NOTIFY_LENGTH)
		hdr = CQCNotifyHeader()
		hdr.setVals(q_id, 0, 0, 0, 0, 0)
		msg = hdr.pack()

		return [cqc_msg, msg]

	def cmd_new(self, cqc_header, cmd, xtra, return_q_id=False, return_succ=False):
		self.parse_data(cqc_header, cmd, xtra, "Create new qubit")
		q_id = CQCLogMessageHandler.cur_qubit_id
		CQCLogMessageHandler.cur_qubit_id += 1
		return_messages = []
		if not return_q_id:
			# Send message we created a qubit back
			# logging.debug("GOO")
			cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_NEW_OK, length=CQC_NOTIFY_LENGTH)
			return_messages.append(cqc_msg)
			hdr = CQCNotifyHeader()
			hdr.setVals(q_id, 0, 0, 0, 0, 0)
			msg = hdr.pack()
			return_messages.append(msg)
		if return_q_id:
			return return_messages, True, q_id
		elif return_succ:
			return return_messages, True
		else:
			return return_messages

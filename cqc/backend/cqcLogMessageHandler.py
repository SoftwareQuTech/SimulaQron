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

from twisted.internet.defer import inlineCallbacks

from SimulaQron.cqc.backend.cqcMessageHandler import CQCMessageHandler
from SimulaQron.cqc.backend.cqcHeader import *

import time
import os
import json
import traceback

from SimulaQron.cqc.backend.entInfoHeader import EntInfoHeader, ENT_INFO_LENGTH


class CQCLogMessageHandler(CQCMessageHandler):
	dir_path = os.path.dirname(os.path.realpath(__file__))
	cur_qubit_id = 0
	logData = []
	log_index = 0

	def __init__(self, factory, protocol):
		super().__init__(factory, protocol)
		self.factory = factory
		CQCLogMessageHandler.file = "{}/logFile{}.json".format(CQCLogMessageHandler.dir_path, factory.name)

	@classmethod
	def parse_data(cls, header, cmd, xtra, comment):
		try:
			subdata = {}
			subdata['comment'] = comment
			subdata['cqc_header'] = cls.parse_header(header)
			subdata['cmd_header'] = cls.parse_cmd(cmd)
			if xtra:
				subdata['xtra_header'] = cls.parse_xtra(xtra)
			cls.logData.append(subdata)
			cls.log_index += 1
			with open(cls.file, 'w') as outfile:
				json.dump(cls.logData, outfile)
		except Exception as e:
			print(e)
			traceback.print_exc()

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
		xtra_data = {}
		xtra_data['is_set'] = xtra.is_set
		xtra_data['qubit_id'] = xtra.qubit_id
		xtra_data['step'] = xtra.step
		xtra_data['remote_app_id'] = xtra.remote_app_id
		xtra_data['remote_node'] = xtra.remote_node
		xtra_data['remote_port'] = xtra.remote_port
		xtra_data['cmdLength'] = xtra.cmdLength
		return xtra_data

	def handle_hello(self, header, data):
		return True

	def handle_factory(self, header, data):
		return True

	def handle_time(self, header, data):
		return True

	def cmd_i(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Identity")
		return True

	def cmd_x(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "X gate")
		return True

	def cmd_y(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Y gate")
		return True

	def cmd_z(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Z gate")
		return True

	def cmd_t(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "T gate")
		return True

	def cmd_h(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "H gate")
		return True

	def cmd_k(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "K gate")
		return True

	def cmd_rotx(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Rotate x")
		return True

	def cmd_roty(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Rotate y")
		return True

	def cmd_rotz(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Rotate z")
		return True

	def cmd_cnot(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "CNOT gate")
		return True

	def cmd_cphase(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "CPhase gate")
		return True

	def cmd_measure(self, cqc_header, cmd, xtra, inplace=False):
		self.parse_data(cqc_header, cmd, xtra, "Measure")
		# We'll always have 1 as outcome
		outcome = 1
		hdr = CQCNotifyHeader()
		hdr.setVals(cmd.qubit_id, outcome, 0, 0, 0, 0)
		msg = hdr.pack()
		self.protocol._send_back_cqc(cqc_header, CQC_TP_MEASOUT, length=CQC_NOTIFY_LENGTH)
		self.protocol.transport.write(msg)
		return True

	def cmd_measure_inplace(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Measure in place")
		outcome = 1
		hdr = CQCNotifyHeader()
		hdr.setVals(cmd.qubit_id, outcome, 0, 0, 0, 0)
		msg = hdr.pack()
		self.protocol._send_back_cqc(cqc_header, CQC_TP_MEASOUT, length=CQC_NOTIFY_LENGTH)
		self.protocol.transport.write(msg)
		return True

	def cmd_reset(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Rest")
		return True

	def cmd_send(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Send")
		return True

	def cmd_recv(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Receive")
		q_id = CQCLogMessageHandler.cur_qubit_id
		CQCLogMessageHandler.cur_qubit_id += 1

		self.protocol._send_back_cqc(cqc_header, CQC_TP_RECV, length=CQC_NOTIFY_LENGTH)
		hdr = CQCNotifyHeader()
		hdr.setVals(q_id, 0, 0, 0, 0, 0)
		msg = hdr.pack()
		self.protocol.transport.write(msg)
		return True

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

		# Create the first qubit
		(succ, q_id1) = self.cmd_new(cqc_header, cmd, xtra, return_q_id=True)
		if not succ:
			return False

		# Create the second qubit
		(succ, q_id2) = self.cmd_new(cqc_header, cmd, xtra, return_q_id=True)
		if not succ:
			return False

		# Create headers for qubits
		cmd1 = CQCCmdHeader()
		cmd1.setVals(q_id1, 0, 0, 0, 0)

		cmd2 = CQCCmdHeader()
		cmd2.setVals(q_id2, 0, 0, 0, 0)

		xtra_cnot = CQCXtraHeader()
		xtra_cnot.setVals(q_id2, 0, 0, 0, 0, 0)

		# Produce EPR-pair
		succ = self.cmd_h(cqc_header, cmd1, None)
		if not succ:
			return False
		succ = self.cmd_cnot(cqc_header, cmd1, xtra_cnot)
		if not succ:
			return False

		self.protocol._send_back_cqc(cqc_header, CQC_TP_EPR_OK, length=CQC_NOTIFY_LENGTH+ENT_INFO_LENGTH)
		hdr = CQCNotifyHeader()
		hdr.setVals(q_id1, 0, 0, 0, 0, 0)
		msg = hdr.pack()
		self.protocol.transport.write(msg)
		logging.debug("CQC %s: Notify %s", self.name, hdr.printable())

		# Send entanglement info
		ent_id = 1
		ent_info = EntInfoHeader()
		ent_info.setVals(host_node, host_port, host_app_id, remote_node, remote_port, remote_app_id, ent_id, int(time.time()), int(time.time()), 0, 1)

		msg = ent_info.pack()
		self.protocol.transport.write(msg)
		return True


	def cmd_epr_recv(self, cqc_header, cmd, xtra):
		self.parse_data(cqc_header, cmd, xtra, "Receive EPR")
		return True

	def cmd_new(self, cqc_header, cmd, xtra, return_q_id=False):
		self.parse_data(cqc_header, cmd, xtra, "Create new qubit")
		q_id = CQCLogMessageHandler.cur_qubit_id
		CQCLogMessageHandler.cur_qubit_id += 1
		if not return_q_id:
			# Send message we created a qubit back
			# logging.debug("GOO")
			self.protocol._send_back_cqc(cqc_header, CQC_TP_NEW_OK, length=CQC_NOTIFY_LENGTH)
			hdr = CQCNotifyHeader()
			hdr.setVals(q_id, 0, 0, 0, 0, 0)
			msg = hdr.pack()
			self.protocol.transport.write(msg)
		if return_q_id:
			return True, q_id
		return True

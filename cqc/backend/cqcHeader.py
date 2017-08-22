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
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES
# LOSS OF USE, DATA, OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys, logging

from struct import *

# Constant defining CQC version
CQC_VERSION=0

# Lengths of the headers in bytes
CQC_HDR_LENGTH=8	# Length of the CQC Header
CQC_CMD_HDR_LENGTH=4	# Length of a command header
CQC_CMD_XTRA_LENGTH=16	# Length of extra command information
CQC_NOTIFY_LENGTH=20	# Length of a notification send from the CQC upwards


# Constants defining the messages types
CQC_TP_HELLO=0		# Alive check
CQC_TP_COMMAND=1	# Execute a command list
CQC_TP_FACTORY=2 	# Start executing command list repeatedly
CQC_TP_EXPIRE=3		# Qubit has expired
CQC_TP_DONE=4		# Done with command
CQC_TP_RECV=5		# Received qubit
CQC_TP_EPR_OK=6		# Created EPR pair
CQC_TP_MEASOUT=7	# Measurement outcome
CQC_TP_GET_TIME=8	# Get creation time of qubit
CQC_TP_INF_TIME=9	# Return timinig information

CQC_ERR_GENERAL=20 	# General purpose error (no details
CQC_ERR_NOQUBIT=21 	# No more qubits available
CQC_ERR_UNSUPP=22 	# No sequence not supported
CQC_ERR_TIMEOUT=23 	# Timeout
CQC_ERR_INUSE=24	# Qubit ID in use (when creating new qubit)

# Possible commands
CQC_CMD_I=0		# Identity (do nothing, wait one step)
CQC_CMD_NEW=1		# Ask for a new qubit
CQC_CMD_MEASURE=2	# Measure qubit
CQC_CMD_RESET=3		# Reset qubit to |0>
CQC_CMD_SEND=4		# Send qubit to another node
CQC_CMD_RECV=5		# Ask to receive qubit
CQC_CMD_EPR=6		# Create EPR pair with the specified node

CQC_CMD_X=10		# Pauli X
CQC_CMD_Z=11		# Pauli Z
CQC_CMD_Y=12		# Pauli Y
CQC_CMD_T=13		# T Gate
CQC_CMD_ROT_X=14	# Rotation over angle around X in 2pi/256 increments
CQC_CMD_ROT_Y=15	# Rotation over angle around Y in 2pi/256 increments
CQC_CMD_ROT_Z=16	# Rotation over angle around Z in 2pi/256 increments
CQC_CMD_H=17		# Hadamard H

CQC_CMD_CNOT=20		# CNOT Gate with this as control
CQC_CMD_CPHASE=21	# CPHASE Gate with this as control

# Command options
CQC_OPT_NOTIFY=0x01	# Send a notification when cmd done
CQC_OPT_ACTION=0x02	# On if there are actions to execute when done
CQC_OPT_BLOCK=0x04	# Block until command is done

class CQCHeader:
	"""
		Definition of the general CQC header.
	"""

	def __init__(self, headerBytes = None):
		"""
			Initialize using values received from a packet.
		"""
		if headerBytes == None:
			self.is_set = False
			self.version = 0
			self.tp = -1
			self.app_id = 0
			self.length = 0
		else:
			self.unpack(headerBytes)

	def setVals(self, version, tp, app_id, length):
		"""
			Set using given values.
		"""
		self.version = version
		self.tp = tp
		self.app_id = app_id
		self.length = length
		self.is_set = True

	def pack(self):
		"""
			Pack data into packet format. For defnitions see cLib/cgc.h
		"""
		if not self.is_set:
			return(0)

		cqcH = pack("=BBHL",self.version, self.tp, self.app_id, self.length)
		return(cqcH)


	def unpack(self, headerBytes):
		"""
			Unpack packet data. For definitions see cLib/cqc.h
		"""
		cqcH = unpack("=BBHL", headerBytes)

		self.version = cqcH[0]
		self.tp = cqcH[1]
		self.app_id = cqcH[2]
		self.length = cqcH[3]
		self.is_set = True

	def printable(self):
		"""
			Produce a printable string for information purposes.
		"""
		if not self.is_set:
			return(" ")

		toPrint = "Version: " + str(self.version) + " "
		toPrint = toPrint + "Type: " + str(self.tp) + " "
		toPrint = toPrint + "App ID: " + str(self.app_id)
		return(toPrint)

class CQCCmdHeader:
	"""
		Header for a command instruction packet.
	"""

	def __init__(self, headerBytes = None):
		"""
		Initialize using values received from a packet, if available.
		"""
		self.notify = False
		self.block = False
		self.action = False

		if headerBytes == None:
			self.is_set = False
			self.qubit_id = 0
			self.instr = 0
		else:
			self.unpack(headerBytes)

	def setVals(self, qubit_id, instr, notify, block, action):
		"""
		Set using given values.
		"""
		self.qubit_id = qubit_id
		self.instr = instr
		self.notify = notify
		self.block = block
		self.action = action
		self.is_set = True

	def pack(self):
		"""
		Pack data into packet format. For defnitions see cLib/cgc.h
		"""

		if not self.is_set:
			return(0)

		opt = 0
		if self.notify:
			opt = opt | CQC_OPT_NOTIFY
		if self.block:
			opt = opt | CQC_OPT_BLOCK
		if self.action:
			opt = opt | CQC_OPT_ACTION

		cmdH = pack("=HBB",self.qubit_id, self.instr, opt)
		return(cmdH)

	def unpack(self, headerBytes):
		"""
		Unpack packet data. For definitions see cLib/cqc.h
		"""
		cmdH = unpack("=HBB", headerBytes)

		self.qubit_id = cmdH[0]
		self.instr = cmdH[1]

		if cmdH[2] & CQC_OPT_NOTIFY:
			self.notify = True
		if cmdH[2] & CQC_OPT_BLOCK:
			self.block = True
		if cmdH[2] & CQC_OPT_ACTION:
			self.action = True

		self.is_set = True

	def printable(self):
		"""
		Produce a printable string for information purposes.
		"""
		if not self.is_set:
			return(" ")

		toPrint = "Qubit ID: " + str(self.qubit_id) + " "
		toPrint = toPrint + "Instruction: " + str(self.instr) + " "
		toPrint = toPrint + "Notify: " + str(self.notify) + " "
		toPrint = toPrint + "Block: " + str(self.block) + " "
		toPrint = toPrint + "Action: " + str(self.action)
		return(toPrint)

class CQCXtraHeader:
	"""
	Optional addtional cmd header information. Only relevant for certain commands.
	"""

	def __init__(self, headerBytes = None):
		"""
		Initialize using values received from a packet.
		"""
		if headerBytes == None:
			self.is_set = False
			self.qubit_id = 0
			self.step = 0
			self.remote_app_id = 0
			self.remote_node = 0
			self.remote_port = 0
			self.cmdLength = 0
		else:
			self.unpack(headerBytes)

	def setVals(self, xtra_qubit_id, step, remote_app_id, remote_node, remote_port, cmdLength):
		"""
			Set using given values.
		"""
		self.qubit_id = xtra_qubit_id
		self.step = step
		self.remote_app_id = remote_app_id
		self.remote_node = remote_node
		self.remote_port = remote_port
		self.cmdLength = cmdLength
		self.is_set = True

	def pack(self):
		"""
			Pack data into packet form. For definitions see cLib/cqc.h
		"""
		if not self.is_set:
			return(0)

		xtraH = pack("=HHLLHBB", self.qubit_id, self.remote_app_id, self.remote_node, self.cmdLength, self.remote_port, self.step, 0)
		return(xtraH)

	def unpack(self, headerBytes):
		"""
			Unpack packet data. For defnitions see cLib/cqc.h
		"""
		xtraH = unpack("=HHLLHBB", headerBytes)

		self.qubit_id = xtraH[0]
		self.remote_app_id = xtraH[1]
		self.remote_node = xtraH[2]
		self.cmdLength = xtraH[3]
		self.remote_port = xtraH[4]
		self.step = xtraH[5]
		self.is_set = True

	def printable(self):
		"""
			Produce a printable string for information purposes.
		"""
		if not self.is_set:
			return(" ")

		toPrint = "Xtra Qubit: " + str(self.qubit_id) + " "
		toPrint = toPrint + "Angle Step: " + str(self.step) + " "
		toPrint = toPrint + "Remote App ID: " + str(self.remote_app_id) + " "
		toPrint = toPrint + "Remote Node: " + str(self.remote_node) + " "
		toPrint = toPrint + "Remote Port: " + str(self.remote_port) + " "
		toPrint = toPrint + "Command Length: " + str(self.cmdLength)

		return(toPrint)

class CQCNotifyHeader:
	"""
		Header used to specify notification details.
	"""

	def __init__(self, headerBytes = None):
		"""
			Initialize from packet data.
		"""
		if headerBytes == None:
			self.is_set = False
			self.qubit_id = 0
			self.outcome = 0
			self.remote_app_id = 0
			self.remote_node = 0
			self.remote_port = 0
			self.datetime = 0
		else:
			self.unpack(headerBytes)

	def setVals(self, qubit_id, outcome, remote_app_id, remote_node, remote_port, datetime):
		"""
		Set using given values.
		"""
		self.qubit_id = qubit_id
		self.outcome = outcome
		self.remote_app_id = remote_app_id
		self.remote_node = remote_node
		self.remote_port = remote_port
		self.datetime = datetime
		self.is_set=True

	def pack(self):
		"""
		Pack data into packet form. For definitions see cLib/cqc.h
		"""
		if not self.is_set:
			return 0

		xtraH = pack("=HHLQHBB", self.qubit_id, self.remote_app_id, self.remote_node, self.datetime, self.remote_port, self.outcome, 0)
		return(xtraH)

	def unpack(self, headerBytes):
		"""
			Unpack packet data. For defnitions see cLib/cqc.h
		"""
		xtraH = unpack("=HHLQHBB", headerBytes)

		self.qubit_id = xtraH[0]
		self.remote_app_id = xtraH[1]
		self.remote_node = xtraH[2]
		self.datetime = xtraH[3]
		self.remote_port = xtraH[4]
		self.outcome = xtraH[5]
		self.is_set = True

	def printable(self):
		"""
			Produce a printable string for information purposes.
		"""
		if not self.is_set:
			return(" ")

		toPrint = "Qubit ID: "  + str(self.qubit_id) + " "
		toPrint = toPrint + "Outcome: " + str(self.outcome) + " "
		toPrint = toPrint + "Remote App ID: " + str(self.remote_app_id) + " "
		toPrint = toPrint + "Remote Node: " + str(self.remote_node) + " "
		toPrint = toPrint + "Remote Port: " + str(self.remote_port) + " "
		toPrint = toPrint + "Datetime: " + str(self.datetime)
		return(toPrint)

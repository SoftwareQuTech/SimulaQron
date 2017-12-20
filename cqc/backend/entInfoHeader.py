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
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES
# LOSS OF USE, DATA, OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys, logging

from struct import *

# Lengths of the headers in bytes
ENT_INFO_LENGTH=40		# Length of a entanglement information header

class EntInfoHeader:
	"""
		Header for a entanglement information packet.
	"""

	def __init__(self, headerBytes = None):
		"""
		Initialize using values received from a packet, if available.
		"""

		if headerBytes == None:
			self.node_A=0
			self.port_A=0
			self.app_id_A=0

			self.node_B=0
			self.port_B=0
			self.app_id_B=0

			self.id_AB=0

			self.timestamp=0
			self.ToG=0
			self.goodness=0
			self.DF=0
		else:
			self.unpack(headerBytes)

	def setVals(self, node_A, port_A, app_id_A, node_B, port_B, app_id_B, id_AB, timestamp, ToG, goodness, DF):
		"""
		Set using given values.
		"""
		self.node_A=node_A
		self.port_A=port_A
		self.app_id_A=app_id_A

		self.node_B=node_B
		self.port_B=port_B
		self.app_id_B=app_id_B

		self.id_AB=id_AB

		self.timestamp=timestamp
		self.ToG=ToG
		self.goodness=goodness
		self.DF=DF

		self.is_set = True

	def pack(self):
		"""
		Pack data into packet format. For defnitions see cLib/cgc.h
		"""

		if not self.is_set:
			return(0)

		ent_info = pack("=LHHLHHLQQHBB", self.node_A, self.port_A, self.app_id_A, self.node_B, self.port_B, self.app_id_B, self.id_AB, self.timestamp, self.ToG, self.goodness, self.DF, 0)
		return(ent_info)

	def unpack(self, headerBytes):
		"""
		Unpack packet data. For definitions see cLib/cqc.h
		"""
		ent_info = unpack("=LHHLHHLQQHBB", headerBytes)

		self.node_A=ent_info[0]
		self.port_A=ent_info[1]
		self.app_id_A=ent_info[2]

		self.node_B=ent_info[3]
		self.port_B=ent_info[4]
		self.app_id_B=ent_info[5]

		self.id_AB=ent_info[6]

		self.timestamp=ent_info[7]
		self.ToG=ent_info[8]
		self.goodness=ent_info[9]
		self.DF=ent_info[10]

		self.is_set = True

	def printable(self):
		"""
		Produce a printable string for information purposes.
		"""
		if not self.is_set:
			return(" ")

		toPrint  = "A: ({}, {}, {})".format(self.node_A,self.port_A,self.app_id_A) + " "
		toPrint += "B: ({}, {}, {})".format(self.node_B,self.port_B,self.app_id_B) + " "
		toPrint = toPrint + "Entanglement ID: " + str(self.id_AB) + " "
		toPrint = toPrint + "Timestamp: " + str(self.timestamp) + " "
		toPrint = toPrint + "Time of Goodness: " + str(self.ToG) + " "
		toPrint = toPrint + "Goodness: " + str(self.goodness) + " "
		toPrint = toPrint + "Directionality Flag: " + str(self.DF)
		return(toPrint)

	def switch_nodes(self):
		"""
		Switches the ip and port of the nodes and flips the directionality flag.
		Used to give correct message to both nodes.
		"""

		# Get current info
		node_A=self.node_A
		port_A=self.port_A
		app_id_A=self.app_id_A
		node_B=self.node_B
		port_B=self.port_B
		app_id_B=self.app_id_B
		DF=self.DF

		# Update
		self.node_A=node_B
		self.port_A=port_B
		self.app_id_A=app_id_B
		self.node_B=node_A
		self.port_B=port_A
		self.app_id_B=app_id_A
		if DF==0:
			self.DF=0
		elif DF==1:
			self.DF=2
		elif DF==2:
			self.DF=1
		else:
			logging.warning("Unknown directionality flag")
			self.DF=DF

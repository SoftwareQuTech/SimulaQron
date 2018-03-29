#
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

#####################################################################################################
#
# main
#
import sys
import unittest

from cqc.backend.cqcHeader import *
from cqc.pythonLib.cqc import CQCConnection, qubit, CQCNoQubitError, CQCGeneralError, CQCUnsuppError


class CQCFactoryTest(unittest.TestCase):
	_cqc = None
	iterations = 8

	def tearDown(self):
		self.cqc.close()

	def setUp(self):
		self.cqc = CQCConnection("Alice", appID=0)

	def testNew(self):
		qubits = self.cqc.sendFactory(2, CQC_CMD_NEW, self.iterations)
		self.assertEqual(len(qubits), self.iterations)
		for q in qubits:
			q.X(print_info=False)
			self.assertEqual(1, q.measure(print_info=False))

	def testMeasure(self):
		q = qubit(self.cqc, print_info=False)
		q.X(print_info=False)  # Let's do an X so all measurement outcomes should be 1
		# (to show no reinitialisation)
		with self.assertRaises(CQCNoQubitError):
			self.cqc.sendFactory(q._qID, CQC_CMD_MEASURE, self.iterations)
		self.assertFalse(q.check_active())

	def testMeasureInplace(self):
		q = qubit(self.cqc, print_info=False)
		q.X(print_info=False)  # Let's do an X so all measurement outcomes should be 1
		# (to show no reinitialisation)
		m = self.cqc.sendFactory(q._qID, CQC_CMD_MEASURE_INPLACE, self.iterations)
		self.assertEqual(len(m), self.iterations)
		self.assertTrue(x == 1 for x in m)
		q.measure(print_info=False)

	def testReset(self):
		q1 = qubit(self.cqc, print_info=False)
		q1.X(print_info=False)
		self.cqc.sendFactory(q1._qID, CQC_CMD_RESET, self.iterations)
		self.assertEqual(q1.measure(print_info=False), 0)

	def testSend(self):
		q = qubit(self.cqc, print_info=False)
		bob = CQCConnection("Bob", appID=1)
		# Get receiving host
		hostDict = self.cqc._cqcNet.hostDict
		if "Bob" in hostDict:
			recvHost = hostDict["Bob"]
		else:
			raise ValueError("Host name 'Bob' is not in the cqc network")
		with self.assertRaises(CQCNoQubitError):
			self.cqc.sendFactory(q._qID, CQC_CMD_SEND, self.iterations, remote_appID=1, remote_node=recvHost.ip,
								 remote_port=recvHost.port)

		self.assertFalse(q.check_active())
		bob.close()

	def testRecv(self):
		bob = CQCConnection("Bob", appID=1)
		for _ in range(self.iterations):
			q = qubit(bob, print_info=False)
			q.X(print_info=False)
			bob.sendQubit(q, "Alice", remote_appID=0, print_info=False)
		qubits = self.cqc.sendFactory(2, CQC_CMD_RECV, self.iterations)
		self.assertEqual(self.iterations, len(qubits))
		for q in qubits:
			q.X(print_info=False)
			self.assertEqual(0, q.measure(print_info=False))
		bob.close()

	def testEPRFail(self):
		with self.assertRaises(CQCUnsuppError):
			self.cqc.sendFactory(2, CQC_CMD_EPR, 4)

	def testEPR(self):
		bob = CQCConnection("Bob", appID=1)
		# Get receiving host
		hostDict = self.cqc._cqcNet.hostDict
		if "Bob" in hostDict:
			recvHost = hostDict["Bob"]
		else:
			raise ValueError("Host name 'Bob' is not in the cqc network")
		# We'll only create 5 EPR pairs, more is not possible
		qubitsAlice = self.cqc.sendFactory(2, CQC_CMD_EPR, 4, remote_appID=1, remote_node=recvHost.ip,
										   remote_port=recvHost.port)
		qubitsBob = bob.sendFactory(2, CQC_CMD_EPR_RECV, 4)
		self.assertEqual(len(qubitsBob), 4)
		self.assertEqual(len(qubitsAlice), len(qubitsBob))
		for i in range(4):
			# Each pair should have the same measurement outcomes
			# if measured in the same basis, test this
			self.assertEqual(qubitsAlice[i].measure(print_info=False), qubitsBob[i].measure(print_info=False))

		bob.close()



if __name__ == '__main__':
	unittest.main()

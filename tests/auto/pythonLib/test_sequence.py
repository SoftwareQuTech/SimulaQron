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
import unittest

from cqc.backend.cqcHeader import *
from cqc.pythonLib.cqc import CQCConnection, qubit


class sequenceTest(unittest.TestCase):
	_alice = None
	_bob = None

	@classmethod
	def setUpClass(cls):
		print("Starting testing sendSequence")
		cls._alice = CQCConnection("Alice")
		cls._bob = CQCConnection("Bob", appID=1)

	@classmethod
	def tearDownClass(cls):
		cls._alice.close()
		cls._bob.close()

	def testNoSequence(self):
		q = qubit(self._alice, print_info=False)
		res = self._alice.sendSequence(q, [], print_info=False)
		self.assertEqual(q.measure(print_info=False), 0)
		self.assertEqual(res, [])

	def testSingleGates(self):
		q = qubit(self._alice, print_info=False)
		r = self._alice.sendSequence(q, [CQC_CMD_X], print_info=False)
		self.assertEqual(q.measure(inplace=True, print_info=False), 1)
		self.assertEqual(r, [])
		q.reset(print_info=False)
		r = self._alice.sendSequence(q, [CQC_CMD_Y], print_info=False)
		q.Y(print_info=False)
		self.assertEqual(q.measure(inplace=True, print_info=False), 0)
		self.assertEqual(r, [])
		q.reset(print_info=False)
		r = self._alice.sendSequence(q, [CQC_CMD_Z], print_info=False)
		q.Z(print_info=False)
		self.assertEqual(q.measure(inplace=True, print_info=False), 0)
		self.assertEqual(r, [])
		q.reset(print_info=False)
		r = self._alice.sendSequence(q, [CQC_CMD_H], print_info=False)
		q.H(print_info=False)
		self.assertEqual(q.measure(inplace=True, print_info=False), 0)
		self.assertEqual(r, [])
		q.measure(print_info=False)

	def testSimpleSequence(self):
		q = qubit(self._alice, print_info=False)
		self._alice.sendSequence(q, [CQC_CMD_H, CQC_CMD_Z, CQC_CMD_H], print_info=False)
		self.assertEqual(q.measure(print_info=False), 1)

	def testMultipleNewQubits(self):
		qs = self._alice.sendSequence(None, [CQC_CMD_NEW] * 10, print_info=False)
		self.assertEqual(len(qs), 10)
		for i in range(1, 10):
			self.assertEqual(qs[i]._qID, qs[i - 1]._qID + 1)
		for q in qs:
			self.assertEqual(q.measure(print_info=False), 0)

	def testMeasuringMultipleQubits(self):
		qs = self._alice.sendSequence(None, [CQC_CMD_NEW] * 10, print_info=False)
		ms = self._alice.sendSequence(qs, [CQC_CMD_MEASURE] * 10, print_info=False)
		self.assertEqual(ms, [0] * 10)

	def testCNOT(self):
		qs = self._alice.sendSequence(None, [CQC_CMD_NEW] * 10, print_info=False)
		self._alice.sendSequence(qs[0], [CQC_CMD_X] + [CQC_CMD_CNOT]*9, xtra_qubits=qs, print_info=False)
		ms = self._alice.sendSequence(qs, [CQC_CMD_MEASURE] * 10, print_info=False)
		self.assertEqual(ms, [1]*10)  # all outcomes should be one

	def testCreatingGHZ(self):
		qs = self._alice.sendSequence(None, [CQC_CMD_NEW] * 10, print_info=False)
		self._alice.sendSequence(qs[0], [CQC_CMD_H] + [CQC_CMD_CNOT]*9, xtra_qubits=qs, print_info=False)
		ms = self._alice.sendSequence(qs, [CQC_CMD_MEASURE] * 10, print_info=False)
		self.assertEqual(len(set(ms)), 1)  # all outcomes should be the same

	def testAlternating(self):
		q = qubit(self._alice, print_info=False)
		res = self._alice.sendSequence(q, [CQC_CMD_X, CQC_CMD_MEASURE_INPLACE] * 10, print_info=False)
		q.measure(print_info=False)
		self.assertEqual(res, [1, 0]*5)

	def testMultipleTypes(self):
		q = qubit(self._alice, print_info=False)
		res = self._alice.sendSequence(q, [CQC_CMD_X, CQC_CMD_NEW, CQC_CMD_MEASURE_INPLACE] * 8, print_info=False)
		q.measure(print_info=False)
		ms = res[1::2]
		qs = res[::2]
		for qu in qs:
			self.assertEqual(qu.measure(print_info=False), 0)
		self.assertEqual(len(res), 16)
		self.assertEqual(ms, [1, 0] * 4)

	def testEPR(self):
		qAs = self._alice.sendSequence(None, [CQC_CMD_EPR] * 5, remote_app_id=1, remote_name="Bob", print_info=False)
		qBs = self._bob.sendSequence(None, [CQC_CMD_EPR_RECV] * 5, print_info=False)
		for i in range(5):
			self.assertEqual(qAs[i].measure(print_info=False), qBs[i].measure(print_info=False))

	def testSend(self):
		qs = self._alice.sendFactory(0, CQC_CMD_NEW, 10)
		# duplicate every item in the list
		qs_duplicated = [q for q in qs for _ in (0,1)]
		res = self._alice.sendSequence(qs_duplicated, [CQC_CMD_X, CQC_CMD_SEND] * 10, remote_app_id=1, remote_name="Bob", print_info=False)
		qsB = self._bob.sendSequence(None, )


if __name__ == '__main__':
	unittest.main()

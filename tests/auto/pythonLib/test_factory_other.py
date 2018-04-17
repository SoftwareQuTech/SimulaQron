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
		self.assertEqual(len(self.cqc.pending_messages), 0)
		self.cqc.close()

	def setUp(self):
		self.cqc = CQCConnection("Alice", appID=0, pend_messages=True)

	def testNew(self):
		qubit(self.cqc, print_info=False)
		qubits = self.cqc.flush_factory(self.iterations, print_info=False)
		self.assertEqual(len(qubits), self.iterations)
		for q in qubits:
			q.X(print_info=False)
			q.measure(print_info=False)
		results = self.cqc.flush(print_info=False)
		self.assertEqual(results, [1]*self.iterations)

	def testMeasure(self):
		q = qubit(self.cqc, print_info=False)
		q.X(print_info=False)  # Let's do an X so all measurement outcomes should be 1
		# (to show no reinitialisation)
		q2 = self.cqc.flush(print_info=False)
		self.assertEqual([q], q2)
		q.measure(print_info=False)
		with self.assertRaises(CQCNoQubitError):
			self.cqc.flush_factory(self.iterations, print_info=False)
		self.assertFalse(q._active)

	def testMeasureInplace(self):
		q = qubit(self.cqc, print_info=False)
		q.X(print_info=False)  # Let's do an X so all measurement outcomes should be 1
		# (to show no reinitialisation)
		q2 = self.cqc.flush(print_info=False)
		self.assertEqual([q], q2)
		q.measure(inplace=True, print_info=False)
		m = self.cqc.flush_factory(self.iterations, print_info=False)
		self.assertEqual(len(m), self.iterations)
		self.assertTrue(x == 1 for x in m)
		q.measure(print_info=False)
		self.cqc.flush(print_info=False)

	def testReset(self):
		q1 = qubit(self.cqc, print_info=False)
		self.cqc.flush(print_info=False)
		q1.X(print_info=False)
		q1.reset(print_info=False)
		self.cqc.flush_factory(self.iterations, print_info=False)
		q1.measure(print_info=False)
		m = self.cqc.flush(print_info=False)
		self.assertEqual(m, [0])

	def testSend(self):
		q = qubit(self.cqc, print_info=False)
		q.X(print_info=False)
		self.cqc.flush(print_info=False)
		bob = CQCConnection("Bob", appID=1)
		# Get receiving host
		self.cqc.sendQubit(q, "Bob", remote_appID=1, print_info=False)
		with self.assertRaises(CQCNoQubitError):
			self.cqc.flush_factory(self.iterations, print_info=False)
		qB = bob.recvQubit(print_info=False)
		self.assertTrue(qB.measure(print_info=False), 1)
		self.assertFalse(q._active)
		bob.close()

	def testRecv(self):
		bob = CQCConnection("Bob", appID=1, pend_messages=True)
		for _ in range(self.iterations):
			q = qubit(bob, print_info=False)
			q.X(print_info=False)
			bob.sendQubit(q, "Alice", remote_appID=0, print_info=False)
			bob.flush(print_info=False)
		self.cqc.recvQubit(print_info=False)
		qubits = self.cqc.flush_factory(self.iterations, print_info=False)
		self.assertEqual(self.iterations, len(qubits))
		for q in qubits:
			self.assertTrue(q._active)
			q.X(print_info=False)
			q.measure(print_info=False)
		f = self.cqc.flush(self.iterations, print_info=False)
		self.assertEqual([0]*self.iterations, f)
		bob.close()

	def testEPR(self):
		bob = CQCConnection("Bob", appID=1, pend_messages=True)
		self.cqc.createEPR("Bob", 1, print_info=False)
		bob.recvEPR(print_info=False)

		it = int(self.iterations/2)

		qubitsAlice = self.cqc.flush_factory(it, print_info=False)
		qubitsBob = bob.flush_factory(it, print_info=False)
		self.assertEqual(len(qubitsBob), it)
		self.assertEqual(len(qubitsAlice), len(qubitsBob))
		for i in range(it):
			# Each pair should have the same measurement outcomes
			# if measured in the same basis, test this
			qubitsAlice[i].measure(print_info=False)
			qubitsBob[i].measure(print_info=False)
		mAlice = self.cqc.flush(print_info=False)
		mBob = bob.flush(print_info=False)
		self.assertEqual(len(mAlice), it)
		self.assertEqual(mAlice, mBob)
		bob.close()


if __name__ == '__main__':
	unittest.main()

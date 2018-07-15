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

from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit


class sequenceTest(unittest.TestCase):
	_alice = None
	_bob = None

	@classmethod
	def setUpClass(cls):
		print("Starting testing sendSequence")
		cls._alice = CQCConnection("Alice", pend_messages=True)
		cls._bob = CQCConnection("Bob", appID=1, pend_messages=True)

	@classmethod
	def tearDownClass(cls):
		cls._alice.close()
		cls._bob.close()

	def tearDown(self):
		self.assertEqual(self._alice.pending_messages, [])
		self.assertEqual(self._bob.pending_messages, [])
		self._alice.flush()
		self._bob.flush()

	def testNoSequence(self):
		res = self._alice.flush()
		self.assertEqual(res, [])

	def testSingleGates(self):
		q = qubit(self._alice)
		q.X()
		q.measure(inplace=True)
		r = self._alice.flush()
		self.assertEqual(len(r), 2)
		self.assertEqual(r[1], 1)
		q.reset()
		q.Y()
		q.measure(inplace=True)
		r = self._alice.flush()
		self.assertEqual(r, [1])
		q.reset()
		q.Z()
		q.measure(inplace=True)
		r = self._alice.flush()
		self.assertEqual(r, [0])
		q.reset()
		q.H()
		q.H()
		q.measure()
		r = self._alice.flush()
		self.assertEqual(r, [0])

	def testSimpleSequence(self):
		q = qubit(self._alice)
		q.H()
		q.Z()
		q.H()
		q.measure()
		r = self._alice.flush()[1]
		self.assertEqual(r, 1)

	def testMultipleNewQubits(self):
		qA = qubit(self._alice)
		qs = self._alice.flush_factory(10)
		self.assertEqual(len(qs), 10)
		self.assertIsNone(qA._qID)
		self.assertFalse(qA.check_active())
		for i in range(1, 10):
			self.assertEqual(qs[i]._qID, qs[i - 1]._qID + 1)
		self._alice.set_pending(False)
		for q in qs:
			self.assertNotEqual(qA, q)
			self.assertEqual(q.measure(), 0)
		self._alice.set_pending(True)

	def testMeasuringMultipleQubits(self):
		qA = qubit(self._alice)
		qs = self._alice.flush_factory(10)
		self.assertIsNone(qA._qID)
		self.assertFalse(qA.check_active())
		for q in qs:
			q.measure()
		ms = self._alice.flush()
		self.assertEqual(ms, [0] * 10)

	def testCNOT(self):
		qA = qubit(self._alice)
		qs = self._alice.flush_factory(10)
		self.assertIsNone(qA._qID)
		self.assertFalse(qA.check_active())
		qs[0].X()
		for i in range(1, 10):
			qs[i-1].cnot(qs[i])
		[q.measure() for q in qs]
		ms = self._alice.flush()
		self.assertEqual(ms, [1]*10)  # all outcomes should be one

	def testCreatingGHZ(self):
		qA = qubit(self._alice)
		qs = self._alice.flush_factory(10)
		self.assertIsNone(qA._qID)
		self.assertFalse(qA.check_active())
		qs[0].H()
		for i in range(1, 10):
			qs[i-1].cnot(qs[i])
		[q.measure() for q in qs]
		ms = self._alice.flush()
		self.assertEqual(len(set(ms)), 1)  # all outcomes should be the same

	def testAlternating(self):
		q = qubit(self._alice)
		self._alice.flush()
		q.X()
		q.measure(inplace=True)
		res = self._alice.flush_factory(10)
		q.measure()
		self._alice.flush()
		self.assertEqual(res, [1, 0]*5)

	def testMultipleTypes(self):
		q = qubit(self._alice)
		self._alice.flush()
		q.X()
		qubit(self._alice)
		q.measure(inplace=True)
		res = self._alice.flush_factory(8)
		self._alice.set_pending(False)
		q.measure()
		ms = res[1::2]
		qs = res[::2]
		for qu in qs:
			self.assertEqual(qu.measure(), 0)
		self.assertEqual(len(res), 16)
		self.assertEqual(ms, [1, 0] * 4)
		self._alice.set_pending(True)

	def testEPR(self):
		self._alice.createEPR(name="Bob", remote_appID=1)
		self._bob.recvEPR()
		qAs = self._alice.flush_factory(5)
		qBs = self._bob.flush_factory(5)
		self._alice.set_pending(False)
		self._bob.set_pending(False)
		for i in range(5):
			self.assertEqual(qAs[i].measure(), qBs[i].measure())
		self._alice.set_pending(True)
		self._bob.set_pending(True)

	def testSend(self):
		qA = qubit(self._alice)
		qAs = self._alice.flush_factory(10)
		self.assertIsNone(qA._qID)
		self.assertFalse(qA.check_active())

		for q in qAs:
			self.assertTrue(q._active)
			self._alice.sendQubit(q, name="Bob", remote_appID=1)
			self.assertTrue(q._active)

		self._alice.flush()
		qB = self._bob.recvQubit()
		qBs = self._bob.flush_factory(10)
		self.assertIsNone(qB._qID)
		self.assertFalse(qB.check_active())

		for q in qAs:
			self.assertFalse(q._active)

		for i in range(1, 10):
			self.assertEqual(qBs[i-1]._qID + 1, qBs[i]._qID)
		self._bob.set_pending(False)
		for q in qBs:
			self.assertEqual(q.measure(), 0)
		self._bob.set_pending(True)


if __name__ == '__main__':
	unittest.main()

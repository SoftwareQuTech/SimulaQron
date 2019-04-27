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

from cqc.pythonLib import CQCConnection, qubit
from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings


class sequenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._alice = None
        cls._bob = None

        simulaqron_settings.default_settings()
        cls.network = Network(nodes=["Alice", "Bob"], force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def testNoSequence(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                res = alice.flush()
                self.assertEqual(res, [])
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testSingleGates(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                q = qubit(alice)
                q.X()
                q.measure(inplace=True)
                r = alice.flush()
                self.assertEqual(len(r), 2)
                self.assertEqual(r[1], 1)
                q.reset()
                q.Y()
                q.measure(inplace=True)
                r = alice.flush()
                self.assertEqual(r, [1])
                q.reset()
                q.Z()
                q.measure(inplace=True)
                r = alice.flush()
                self.assertEqual(r, [0])
                q.reset()
                q.H()
                q.H()
                q.measure()
                r = alice.flush()
                self.assertEqual(r, [0])
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testSimpleSequence(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                q = qubit(alice)
                q.H()
                q.Z()
                q.H()
                q.measure()
                r = alice.flush()[1]
                self.assertEqual(r, 1)
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testMultipleNewQubits(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                qA = qubit(alice)
                qs = alice.flush_factory(10)
                self.assertEqual(len(qs), 10)
                self.assertIsNone(qA._qID)
                self.assertFalse(qA.check_active())
                for i in range(1, 10):
                    self.assertEqual(qs[i]._qID, qs[i - 1]._qID + 1)
                alice.set_pending(False)
                for q in qs:
                    self.assertNotEqual(qA, q)
                    self.assertEqual(q.measure(), 0)
                alice.set_pending(True)
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testMeasuringMultipleQubits(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                qA = qubit(alice)
                qs = alice.flush_factory(10)
                self.assertIsNone(qA._qID)
                self.assertFalse(qA.check_active())
                for q in qs:
                    q.measure()
                ms = alice.flush()
                self.assertEqual(ms, [0] * 10)
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testCNOT(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                qA = qubit(alice)
                qs = alice.flush_factory(10)
                self.assertIsNone(qA._qID)
                self.assertFalse(qA.check_active())
                qs[0].X()
                for i in range(1, 10):
                    qs[i - 1].cnot(qs[i])
                [q.measure() for q in qs]
                ms = alice.flush()
                self.assertEqual(ms, [1] * 10)  # all outcomes should be one
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testCreatingGHZ(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                qA = qubit(alice)
                qs = alice.flush_factory(10)
                self.assertIsNone(qA._qID)
                self.assertFalse(qA.check_active())
                qs[0].H()
                for i in range(1, 10):
                    qs[i - 1].cnot(qs[i])
                [q.measure() for q in qs]
                ms = alice.flush()
                self.assertEqual(len(set(ms)), 1)  # all outcomes should be the same
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testAlternating(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                q = qubit(alice)
                alice.flush()
                q.X()
                q.measure(inplace=True)
                res = alice.flush_factory(10)
                q.measure()
                alice.flush()
                self.assertEqual(res, [1, 0] * 5)
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testMultipleTypes(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                q = qubit(alice)
                alice.flush()
                q.X()
                qubit(alice)
                q.measure(inplace=True)
                res = alice.flush_factory(8)
                alice.set_pending(False)
                q.measure()
                ms = res[1::2]
                qs = res[::2]
                for qu in qs:
                    self.assertEqual(qu.measure(), 0)
                self.assertEqual(len(res), 16)
                self.assertEqual(ms, [1, 0] * 4)
                alice.set_pending(True)
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testEPR(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                alice.createEPR(name="Bob", remote_appID=1)
                bob.recvEPR()
                qAs = alice.flush_factory(5)
                qBs = bob.flush_factory(5)
                alice.set_pending(False)
                bob.set_pending(False)
                for i in range(5):
                    self.assertEqual(qAs[i].measure(), qBs[i].measure())
                alice.set_pending(True)
                bob.set_pending(True)
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()

    def testSend(self):
        with CQCConnection("Alice", pend_messages=True) as alice:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                qA = qubit(alice)
                qAs = alice.flush_factory(10)
                self.assertIsNone(qA._qID)
                self.assertFalse(qA.check_active())

                for q in qAs:
                    self.assertTrue(q._active)
                    alice.sendQubit(q, name="Bob", remote_appID=1)
                    self.assertTrue(q._active)

                alice.flush()
                qB = bob.recvQubit()
                qBs = bob.flush_factory(10)
                self.assertIsNone(qB._qID)
                self.assertFalse(qB.check_active())

                for q in qAs:
                    self.assertFalse(q._active)

                for i in range(1, 10):
                    self.assertEqual(qBs[i - 1]._qID + 1, qBs[i]._qID)
                bob.set_pending(False)
                for q in qBs:
                    self.assertEqual(q.measure(), 0)
                bob.set_pending(True)
                self.assertEqual(alice.pending_messages, [])
                self.assertEqual(bob.pending_messages, [])
                alice.flush()
                bob.flush()


if __name__ == "__main__":
    unittest.main()

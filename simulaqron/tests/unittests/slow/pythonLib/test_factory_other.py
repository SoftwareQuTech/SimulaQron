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

from cqc.pythonLib import CQCConnection, CQCNoQubitError, qubit
from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings


class CQCFactoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iterations = 8

        simulaqron_settings.default_settings()
        cls.network = Network(nodes=["Alice", "Bob"], force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def testNew(self):
        with CQCConnection("Alice", appID=0, pend_messages=True) as cqc:
            qubit(cqc)
            qubits = cqc.flush_factory(self.iterations)
            self.assertEqual(len(qubits), self.iterations)
            for q in qubits:
                q.X()
                q.measure()
            results = cqc.flush()
            self.assertEqual(results, [1] * self.iterations)
            self.assertEqual(len(cqc.pending_messages), 0)

    def testMeasure(self):
        with CQCConnection("Alice", appID=0, pend_messages=True) as cqc:
            q = qubit(cqc)
            q.X()  # Let's do an X so all measurement outcomes should be 1
            # (to show no reinitialisation)
            q2 = cqc.flush()
            self.assertEqual([q], q2)
            q.measure()
            with self.assertRaises(CQCNoQubitError):
                cqc.flush_factory(self.iterations)
            self.assertFalse(q._active)
            self.assertEqual(len(cqc.pending_messages), 0)

    def testMeasureInplace(self):
        with CQCConnection("Alice", appID=0, pend_messages=True) as cqc:
            q = qubit(cqc)
            q.X()  # Let's do an X so all measurement outcomes should be 1
            # (to show no reinitialisation)
            q2 = cqc.flush()
            self.assertEqual([q], q2)
            q.measure(inplace=True)
            m = cqc.flush_factory(self.iterations)
            self.assertEqual(len(m), self.iterations)
            self.assertTrue(x == 1 for x in m)
            q.measure()
            cqc.flush()
            self.assertEqual(len(cqc.pending_messages), 0)

    def testReset(self):
        with CQCConnection("Alice", appID=0, pend_messages=True) as cqc:
            q1 = qubit(cqc)
            cqc.flush()
            q1.X()
            q1.reset()
            cqc.flush_factory(self.iterations)
            q1.measure()
            m = cqc.flush()
            self.assertEqual(m, [0])
            self.assertEqual(len(cqc.pending_messages), 0)

    def testSend(self):
        with CQCConnection("Alice", appID=0, pend_messages=True) as cqc:
            q = qubit(cqc)
            q.X()
            cqc.flush()
            with CQCConnection("Bob", appID=1) as bob:
                # Get receiving host
                cqc.sendQubit(q, "Bob", remote_appID=1)
                with self.assertRaises(CQCNoQubitError):
                    cqc.flush_factory(self.iterations)
                qB = bob.recvQubit()
                self.assertTrue(qB.measure(), 1)
                self.assertFalse(q._active)
            self.assertEqual(len(cqc.pending_messages), 0)

    def testRecv(self):
        with CQCConnection("Alice", appID=0, pend_messages=True) as cqc:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                for _ in range(self.iterations):
                    q = qubit(bob)
                    q.X()
                    bob.sendQubit(q, "Alice", remote_appID=0)
                    bob.flush()
                cqc.recvQubit()
                qubits = cqc.flush_factory(self.iterations)
                self.assertEqual(self.iterations, len(qubits))
                for q in qubits:
                    self.assertTrue(q._active)
                    q.X()
                    q.measure()
                f = cqc.flush(self.iterations)
                self.assertEqual([0] * self.iterations, f)
            self.assertEqual(len(cqc.pending_messages), 0)

    def testEPR(self):
        with CQCConnection("Alice", appID=0, pend_messages=True) as cqc:
            with CQCConnection("Bob", appID=1, pend_messages=True) as bob:
                cqc.createEPR("Bob", 1)
                bob.recvEPR()

                it = int(self.iterations / 2)

                qubitsAlice = cqc.flush_factory(it)
                qubitsBob = bob.flush_factory(it)
                self.assertEqual(len(qubitsBob), it)
                self.assertEqual(len(qubitsAlice), len(qubitsBob))
                for i in range(it):
                    # Each pair should have the same measurement outcomes
                    # if measured in the same basis, test this
                    qubitsAlice[i].measure()
                    qubitsBob[i].measure()
                mAlice = cqc.flush()
                mBob = bob.flush()
                self.assertEqual(len(mAlice), it)
                self.assertEqual(mAlice, mBob)
            self.assertEqual(len(cqc.pending_messages), 0)


if __name__ == "__main__":
    unittest.main()

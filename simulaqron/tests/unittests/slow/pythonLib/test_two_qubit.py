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
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import sys
import unittest
import numpy as np

from cqc.pythonLib import CQCConnection, qubit
from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings


def calc_exp_values(q):
    """
    Calculates the expected value for measurements in the X,Y and Z basis and returns these in a tuple.
    q should be a numpy array representing a qubit density matrix
    """
    # eigenvectors
    z0 = np.array([[1], [0]])
    z1 = np.array([[0], [1]])
    x1 = 1 / np.sqrt(2) * (z0 - z1)
    y1 = 1 / np.sqrt(2) * (z0 - 1j * z1)

    # projectors
    P_X1 = np.dot(x1, np.transpose(np.conj(x1)))
    P_Y1 = np.dot(y1, np.transpose(np.conj(y1)))
    P_Z1 = np.dot(z1, np.transpose(np.conj(z1)))

    # probabilities
    p_x = np.real(np.trace(np.dot(P_X1, q)))
    p_y = np.real(np.trace(np.dot(P_Y1, q)))
    p_z = np.real(np.trace(np.dot(P_Z1, q)))

    return p_x, p_y, p_z


def prep_CNOT_control_CQC(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    q1.cnot(q2)
    q2.measure()
    return q1


def prep_CNOT_target_CQC(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    q1.cnot(q2)
    q1.measure()
    return q2


def prep_CPHASE_control_CQC(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    q2.H()
    q1.cphase(q2)
    q2.H()
    q2.measure()
    return q1


def prep_CPHASE_target_CQC(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    q2.H()
    q1.cphase(q2)
    q2.H()
    q1.measure()
    return q2


def prep_EPR1_CQC(cqc):
    with CQCConnection("Alice", appID=1) as Alice:
        qA = Alice.createEPR("Bob")
        qB = cqc.recvEPR()
        qA.measure()
    return qB


def prep_EPR2_CQC(cqc):
    with CQCConnection("Alice", appID=1) as Alice:
        qB = cqc.createEPR("Alice", remote_appID=1)
        qA = Alice.recvEPR()
        qA.measure()
    return qB


def prep_send_CQC(cqc):
    with CQCConnection("Alice", appID=1) as Alice:
        qA = qubit(cqc)
        qB = qubit(cqc)
        qA.H()
        qA.cnot(qB)
        cqc.sendQubit(qA, "Alice", remote_appID=1)
        qA = Alice.recvQubit()
        m = qA.measure()
        if m == 1:
            qB.X()
        qB.H()
    return qB


def prep_recv_CQC(cqc):
    with CQCConnection("Alice", appID=1) as Alice:
        qA = qubit(Alice)
        qA.H()
        Alice.sendQubit(qA, "Bob")
        qB = cqc.recvQubit()
    return qB


def prep_mixed_state():
    q = np.eye(2) / 2
    return q


def prep_H_state():
    q = np.array([[1], [0]])
    H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    q2 = np.dot(H, q)
    return np.dot(q2, np.transpose(np.conj(q2)))


#####################################################################################################
class TwoQubitGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iterations = 100
        sys.stdout.write("Testing two qubit gates gates with {} iterations \r\n".format(cls.iterations))

        simulaqron_settings.default_settings()
        cls.network = Network(nodes=["Alice", "Bob"], force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def testCNOTControl(self):
        with CQCConnection("Bob", appID=0) as cqc:
            # Test CNOT control
            sys.stdout.write("Testing CNOT control:")
            exp_values = calc_exp_values(prep_mixed_state())
            ans = cqc.test_preparation(prep_CNOT_control_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testCNOTTarget(self):
        with CQCConnection("Bob", appID=0) as cqc:
            # Test CNOT target
            sys.stdout.write("Testing CNOT target:")
            exp_values = calc_exp_values(prep_mixed_state())
            ans = cqc.test_preparation(prep_CNOT_target_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testCPHASEControl(self):
        with CQCConnection("Bob", appID=0) as cqc:
            # Test CPHASE control
            sys.stdout.write("Testing CPHASE control:")
            exp_values = calc_exp_values(prep_mixed_state())
            ans = cqc.test_preparation(prep_CPHASE_control_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testCPHASETarget(self):
        with CQCConnection("Bob", appID=0) as cqc:
            # Test CPHASE target
            sys.stdout.write("Testing CPHASE target:")
            exp_values = calc_exp_values(prep_mixed_state())
            ans = cqc.test_preparation(prep_CPHASE_target_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testEPR1(self):
        with CQCConnection("Bob", appID=0) as cqc:
            # Test EPR1
            sys.stdout.write("Testing EPR1:")
            exp_values = calc_exp_values(prep_mixed_state())
            ans = cqc.test_preparation(prep_EPR1_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testEPR2(self):
        with CQCConnection("Bob", appID=0) as cqc:
            # Test EPR2
            sys.stdout.write("Testing EPR2:")
            exp_values = calc_exp_values(prep_mixed_state())
            ans = cqc.test_preparation(prep_EPR2_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testSendControl(self):
        with CQCConnection("Bob", appID=0) as cqc:
            # Test send control
            sys.stdout.write("Testing send:")
            exp_values = calc_exp_values(prep_H_state())
            ans = cqc.test_preparation(prep_send_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testRevTarget(self):
        with CQCConnection("Bob", appID=0) as cqc:
            # Test recv target
            sys.stdout.write("Testing recv:")
            exp_values = calc_exp_values(prep_H_state())
            ans = cqc.test_preparation(prep_recv_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)


##################################################################################################

if __name__ == "__main__":
    unittest.main()

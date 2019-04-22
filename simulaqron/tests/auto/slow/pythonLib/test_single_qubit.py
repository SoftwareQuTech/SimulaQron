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
import unittest
import numpy as np
from scipy.linalg import expm
import sys

from cqc.pythonLib import CQCConnection, qubit, CQCUnsuppError
from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network


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
    d_dag = np.transpose(np.conj(q))
    p_x = np.real(np.dot(d_dag, np.dot(P_X1, q))[0, 0])
    p_y = np.real(np.dot(d_dag, np.dot(P_Y1, q))[0, 0])
    p_z = np.real(np.dot(d_dag, np.dot(P_Z1, q))[0, 0])

    return (p_x, p_y, p_z)


def prep_I_CQC(cqc):
    q = qubit(cqc)
    q.I()
    return q


def prep_X_CQC(cqc):
    q = qubit(cqc)
    q.X()
    return q


def prep_X_state():
    q = np.array([[0], [1]])
    return q


def prep_Y_CQC(cqc):
    q = qubit(cqc)
    q.Y()
    return q


def prep_Y_state():
    q = np.array([[0], [1j]])
    return q


def prep_Z_CQC(cqc):
    q = qubit(cqc)
    q.Z()
    return q


def prep_Z_state():
    q = np.array([[1], [0]])
    return q


def prep_H_CQC(cqc):
    q = qubit(cqc)
    q.H()
    return q


def prep_H_state():
    q = np.array([[1], [1]]) / np.sqrt(2)
    return q


def prep_T_CQC(cqc):
    q = qubit(cqc)
    q.T()
    return q


def prep_T_state():
    q = np.array([[1], [0]])
    return q


def prep_K_CQC(cqc):
    q = qubit(cqc)
    q.K()
    return q


def prep_K_state():
    q = np.array([[1], [1j]]) / np.sqrt(2)
    return q


def prep_rotx1_CQC(cqc):  # pi/8
    q = qubit(cqc)
    q.rot_X(16)
    return q


def prep_rotx2_CQC(cqc):  # 5*pi/8
    q = qubit(cqc)
    q.rot_X(80)
    return q


def prep_roty1_CQC(cqc):  # pi/8
    q = qubit(cqc)
    q.rot_Y(16)
    return q


def prep_roty2_CQC(cqc):  # 5*pi/8
    q = qubit(cqc)
    q.rot_Y(80)
    return q


def prep_rotz1_CQC(cqc):  # pi/8
    q = qubit(cqc)
    q.rot_Z(16)
    return q


def prep_rotz2_CQC(cqc):  # 5*pi/8
    q = qubit(cqc)
    q.rot_Z(80)
    return q


def prep_rot_state(n, a):
    q = np.array([[1], [0]])
    nNorm = np.linalg.norm(n)
    X = np.array([[0, 1], [1, 0]])
    Y = np.array([[0, -1j], [1j, 0]])
    Z = np.array([[1, 0], [0, -1]])
    R = expm(-1j * a / (2 * nNorm) * (n[0] * X + n[1] * Y + n[2] * Z))
    return np.dot(R, q)


def prep_reset_CQC(cqc):
    q = qubit(cqc)
    q.H()
    q.reset()
    return q


def prep_I_state():
    q = np.array([[1], [0]])
    return q


#####################################################################################################
class SingleQubitGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iterations = 100
        sys.stdout.write("Testing single qubit gates gates with {} iterations \r\n".format(cls.iterations))

        simulaqron_settings.default_settings()
        cls.network = Network(nodes=["Alice"], force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def testIGate(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test I
            sys.stdout.write("Testing I gate:")
            exp_values = calc_exp_values(prep_I_state())
            ans = cqc.test_preparation(prep_I_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testXGate(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test X
            sys.stdout.write("Testing X gate:")
            exp_values = calc_exp_values(prep_X_state())
            ans = cqc.test_preparation(prep_X_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testYGate(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test Y
            sys.stdout.write("Testing Y gate:")
            exp_values = calc_exp_values(prep_Y_state())
            ans = cqc.test_preparation(prep_Y_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testZGate(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test Z
            sys.stdout.write("Testing Z gate:")
            exp_values = calc_exp_values(prep_Z_state())
            ans = cqc.test_preparation(prep_Z_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testHGate(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test H
            sys.stdout.write("Testing H gate:")
            exp_values = calc_exp_values(prep_H_state())
            ans = cqc.test_preparation(prep_H_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testTGate(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test T
            sys.stdout.write("Testing T gate:")
            exp_values = calc_exp_values(prep_T_state())
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(prep_T_CQC, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = cqc.test_preparation(prep_T_CQC, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testKGate(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test K
            sys.stdout.write("Testing K gate:")
            exp_values = calc_exp_values(prep_K_state())
            ans = cqc.test_preparation(prep_K_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testXpi8Rot(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test ROT_X pi/8
            sys.stdout.write("Testing rotation (X,pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([1, 0, 0], np.pi / 8))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(prep_rotx1_CQC, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = cqc.test_preparation(prep_rotx1_CQC, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testX5pi8Rot(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test ROT_X 5*pi/8
            sys.stdout.write("Testing rotation (X,5*pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([1, 0, 0], 5 * np.pi / 8))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(prep_rotx2_CQC, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = cqc.test_preparation(prep_rotx2_CQC, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testYpi8Rot(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test ROT_Y pi/8
            sys.stdout.write("Testing rotation (Y,pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([0, 1, 0], np.pi / 8))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(prep_roty1_CQC, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = cqc.test_preparation(prep_roty1_CQC, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testY5pi8Rot(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test ROT_Y 5*pi/8
            sys.stdout.write("Testing rotation (Y,5*pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([0, 1, 0], 5 * np.pi / 8))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(prep_roty2_CQC, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = cqc.test_preparation(prep_roty2_CQC, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testZpi8Rot(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test ROT_Z pi/8
            sys.stdout.write("Testing rotation (Z,pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([0, 0, 1], np.pi / 8))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(prep_rotz1_CQC, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = cqc.test_preparation(prep_rotz1_CQC, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testZ5pi8Rot(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test ROT_Z 5*pi/8
            sys.stdout.write("Testing rotation (Z,5*pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([0, 0, 1], 5 * np.pi / 8))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(prep_rotz2_CQC, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = cqc.test_preparation(prep_rotz2_CQC, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testReset(self):
        with CQCConnection("Alice", appID=0) as cqc:
            # Test RESET
            sys.stdout.write("Testing RESET:")
            exp_values = calc_exp_values(prep_I_state())
            ans = cqc.test_preparation(prep_reset_CQC, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)


##################################################################################################

if __name__ == "__main__":
    unittest.main()

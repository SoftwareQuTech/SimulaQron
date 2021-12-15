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

from netqasm.sdk.qubit import Qubit

from simulaqron.settings import simulaqron_settings, SimBackend
from simulaqron.network import Network
from simulaqron.sdk.connection import SimulaQronConnection
from simulaqron.general import SimUnsupportedError


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


def prep_I(conn):
    q = Qubit(conn)
    q.I()
    return q


def prep_X(conn):
    q = Qubit(conn)
    q.X()
    return q


def prep_X_state():
    q = np.array([[0], [1]])
    return q


def prep_Y(conn):
    q = Qubit(conn)
    q.Y()
    return q


def prep_Y_state():
    q = np.array([[0], [1j]])
    return q


def prep_Z(conn):
    q = Qubit(conn)
    q.Z()
    return q


def prep_Z_state():
    q = np.array([[1], [0]])
    return q


def prep_H(conn):
    q = Qubit(conn)
    q.H()
    return q


def prep_H_state():
    q = np.array([[1], [1]]) / np.sqrt(2)
    return q


def prep_T(conn):
    q = Qubit(conn)
    q.T()
    return q


def prep_T_state():
    q = np.array([[1], [0]])
    return q


def prep_K(conn):
    q = Qubit(conn)
    q.K()
    return q


def prep_K_state():
    q = np.array([[1], [1j]]) / np.sqrt(2)
    return q


def prep_rotx1(conn):  # pi/8
    q = Qubit(conn)
    q.rot_X(16)
    return q


def prep_rotx2(conn):  # 5*pi/8
    q = Qubit(conn)
    q.rot_X(80)
    return q


def prep_roty1(conn):  # pi/8
    q = Qubit(conn)
    q.rot_Y(16)
    return q


def prep_roty2(conn):  # 5*pi/8
    q = Qubit(conn)
    q.rot_Y(80)
    return q


def prep_rotz1(conn):  # pi/8
    q = Qubit(conn)
    q.rot_Z(16)
    return q


def prep_rotz2(conn):  # 5*pi/8
    q = Qubit(conn)
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


def prep_reset(conn):
    q = Qubit(conn)
    q.H()
    q.reset()
    return q


def prep_I_state():
    q = np.array([[1], [0]])
    return q


@unittest.skip("We can test these things better when we have implemented a get_qubit_state function for simulaqron")
class SingleQubitGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iterations = 1
        sys.stdout.write("Testing single qubit gates gates with {} iterations \r\n".format(cls.iterations))

        simulaqron_settings.default_settings()
        cls.network = Network(nodes=["Alice"], force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def testXGate(self):
        with SimulaQronConnection("Alice") as conn:
            # Test X
            sys.stdout.write("Testing X gate:")
            exp_values = calc_exp_values(prep_X_state())
            ans = conn.test_preparation(prep_X, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testYGate(self):
        with SimulaQronConnection("Alice") as conn:
            # Test Y
            sys.stdout.write("Testing Y gate:")
            exp_values = calc_exp_values(prep_Y_state())
            ans = conn.test_preparation(prep_Y, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testZGate(self):
        with SimulaQronConnection("Alice") as conn:
            # Test Z
            sys.stdout.write("Testing Z gate:")
            exp_values = calc_exp_values(prep_Z_state())
            ans = conn.test_preparation(prep_Z, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testHGate(self):
        with SimulaQronConnection("Alice") as conn:
            # Test H
            sys.stdout.write("Testing H gate:")
            exp_values = calc_exp_values(prep_H_state())
            ans = conn.test_preparation(prep_H, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testTGate(self):
        with SimulaQronConnection("Alice") as conn:
            # Test T
            sys.stdout.write("Testing T gate:")
            exp_values = calc_exp_values(prep_T_state())
            if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
                with self.assertRaises(SimUnsupportedError):
                    conn.test_preparation(prep_T, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = conn.test_preparation(prep_T, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testKGate(self):
        with SimulaQronConnection("Alice") as conn:
            # Test K
            sys.stdout.write("Testing K gate:")
            exp_values = calc_exp_values(prep_K_state())
            ans = conn.test_preparation(prep_K, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testXpi8Rot(self):
        with SimulaQronConnection("Alice") as conn:
            # Test ROT_X pi/8
            sys.stdout.write("Testing rotation (X,pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([1, 0, 0], np.pi / 8))
            if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
                with self.assertRaises(SimUnsupportedError):
                    conn.test_preparation(prep_rotx1, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = conn.test_preparation(prep_rotx1, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testX5pi8Rot(self):
        with SimulaQronConnection("Alice") as conn:
            # Test ROT_X 5*pi/8
            sys.stdout.write("Testing rotation (X,5*pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([1, 0, 0], 5 * np.pi / 8))
            if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
                with self.assertRaises(SimUnsupportedError):
                    conn.test_preparation(prep_rotx2, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = conn.test_preparation(prep_rotx2, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testYpi8Rot(self):
        with SimulaQronConnection("Alice") as conn:
            # Test ROT_Y pi/8
            sys.stdout.write("Testing rotation (Y,pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([0, 1, 0], np.pi / 8))
            if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
                with self.assertRaises(SimUnsupportedError):
                    conn.test_preparation(prep_roty1, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = conn.test_preparation(prep_roty1, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testY5pi8Rot(self):
        with SimulaQronConnection("Alice") as conn:
            # Test ROT_Y 5*pi/8
            sys.stdout.write("Testing rotation (Y,5*pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([0, 1, 0], 5 * np.pi / 8))
            if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
                with self.assertRaises(SimUnsupportedError):
                    conn.test_preparation(prep_roty2, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = conn.test_preparation(prep_roty2, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testZpi8Rot(self):
        with SimulaQronConnection("Alice") as conn:
            # Test ROT_Z pi/8
            sys.stdout.write("Testing rotation (Z,pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([0, 0, 1], np.pi / 8))
            if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
                with self.assertRaises(SimUnsupportedError):
                    conn.test_preparation(prep_rotz1, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = conn.test_preparation(prep_rotz1, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testZ5pi8Rot(self):
        with SimulaQronConnection("Alice") as conn:
            # Test ROT_Z 5*pi/8
            sys.stdout.write("Testing rotation (Z,5*pi/8) gate:")
            exp_values = calc_exp_values(prep_rot_state([0, 0, 1], 5 * np.pi / 8))
            if simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
                with self.assertRaises(SimUnsupportedError):
                    conn.test_preparation(prep_rotz2, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = conn.test_preparation(prep_rotz2, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testReset(self):
        with SimulaQronConnection("Alice") as conn:
            # Test RESET
            sys.stdout.write("Testing RESET:")
            exp_values = calc_exp_values(prep_I_state())
            ans = conn.test_preparation(prep_reset, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)


##################################################################################################

if __name__ == "__main__":
    unittest.main()

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

import sys
import unittest
import numpy as np
from scipy.linalg import expm

from cqc.pythonLib import CQCConnection, qubit, CQCUnsuppError
from simulaqron.settings import simulaqron_settings
from simulaqron.network import Network


def calc_exp_values_single(q):
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

    return p_x, p_y, p_z


def calc_exp_values_two(q):
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


def prep_I_CQC_FACTORY(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.I()
    cqc.flush_factory(3)
    cqc.set_pending(False)
    return q


def prep_I_state():
    q = np.array([[1], [0]])
    return q


def prep_X_CQC_FACTORY_ODD(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.X()
    cqc.flush_factory(3)
    cqc.set_pending(False)
    return q


def prep_X_CQC_FACTORY_EVEN(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.X()
    cqc.flush_factory(4)
    cqc.set_pending(False)
    return q


def prep_X_state():
    q = np.array([[0], [1]])
    return q


def prep_Y_CQC_FACTORY_ODD(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.Y()
    cqc.flush_factory(3)
    cqc.set_pending(False)
    return q


def prep_Y_CQC_FACTORY_EVEN(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.Y()
    cqc.flush_factory(4)
    cqc.set_pending(False)
    return q


def prep_Y_state():
    q = np.array([[0], [1j]])
    return q


def prep_Z_CQC_FACTORY_ODD(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.Z()
    cqc.flush_factory(3)
    cqc.set_pending(False)
    return q


def prep_Z_CQC_FACTORY_EVEN(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.Z()
    cqc.flush_factory(4)
    cqc.set_pending(False)
    return q


def prep_Z_state():
    q = np.array([[1], [0]])
    return q


def prep_T_CQC_FACTORY_QUARTER(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.T()
    cqc.flush_factory(5)
    cqc.set_pending(False)
    return q


def prep_T_CQC_FACTORY_HALF(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.T()
    cqc.flush_factory(6)
    cqc.set_pending(False)
    return q


def prep_T_CQC_FACTORY_THREE_QUARTER(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.T()
    cqc.flush_factory(7)
    cqc.set_pending(False)
    return q


def prep_T_CQC_FACTORY_FULL(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.T()
    cqc.flush_factory(8)
    cqc.set_pending(False)
    return q


def prep_T_state(amount):
    q = np.array([[1], [0]])
    T = np.array([[1, 0], [0, np.exp(amount * np.pi / 4)]])
    return np.dot(T, q)


def prep_H_CQC_FACTORY_ODD(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.H()
    cqc.flush_factory(3)
    cqc.set_pending(False)
    return q


def prep_H_CQC_FACTORY_EVEN(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.H()
    cqc.flush_factory(4)
    cqc.set_pending(False)
    return q


def prep_H_state():
    q = np.array([[1], [1]]) / np.sqrt(2)
    return q


def prep_K_CQC_FACTORY_ODD(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.K()
    cqc.flush_factory(3)
    cqc.set_pending(False)
    return q


def prep_K_CQC_FACTORY_EVEN(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.K()
    cqc.flush_factory(4)
    cqc.set_pending(False)
    return q


def prep_K_state():
    q = np.array([[1], [1j]]) / np.sqrt(2)
    return q


def prep_ROT_X(cqc):
    q = qubit(cqc)
    cqc.set_pending(True)
    q.rot_X(step=4)
    cqc.flush_factory(4)
    cqc.set_pending(False)
    return q


def prep_ROT_X_state():
    theta = np.pi / 8
    return prep_rot_state([1, 0, 0], theta)


def prep_rot_state(n, a):
    q = np.array([[1], [0]])
    nNorm = np.linalg.norm(n)
    X = np.array([[0, 1], [1, 0]])
    Y = np.array([[0, -1j], [1j, 0]])
    Z = np.array([[1, 0], [0, -1]])
    R = expm(-1j * a / (2 * nNorm) * (n[0] * X + n[1] * Y + n[2] * Z))
    return R * q


def prep_mixed_state():
    q = np.eye(2) / 2
    return q


def prep_CNOT_control_CQC_FACTORY_even(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    cqc.set_pending(True)
    q1.cnot(q2)
    cqc.flush_factory(4)
    cqc.set_pending(False)
    q2.measure()
    return q1


def prep_CNOT_control_CQC_FACTORY_odd(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    cqc.set_pending(True)
    q1.cnot(q2)
    cqc.flush_factory(3)
    cqc.set_pending(False)
    q2.measure()
    return q1


def prep_CNOT_target_CQC_FACTORY_even(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    cqc.set_pending(True)
    q1.cnot(q2)
    cqc.flush_factory(4)
    cqc.set_pending(False)
    q1.measure()
    return q2


def prep_CNOT_target_CQC_FACTORY_odd(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    cqc.set_pending(True)
    q1.cnot(q2)
    cqc.flush_factory(3)
    cqc.set_pending(False)
    q1.measure()
    return q2


def prep_CPHASE_control_CQC_FACTORY_even(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    q2.H()
    cqc.set_pending(True)
    q1.cphase(q2)
    cqc.flush_factory(4)
    cqc.set_pending(False)
    q2.H()
    q2.measure()
    return q1


def prep_CPHASE_control_CQC_FACTORY_odd(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    q2.H()
    cqc.set_pending(True)
    q1.cphase(q2)
    cqc.flush_factory(3)
    cqc.set_pending(False)
    q2.H()
    q2.measure()
    return q1


def prep_CPHASE_target_CQC_FACTORY_even(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    q2.H()
    cqc.set_pending(True)
    q1.cphase(q2)
    cqc.flush_factory(4)
    cqc.set_pending(False)
    q2.H()
    q1.measure()
    return q2


def prep_CPHASE_target_CQC_FACTORY_odd(cqc):
    q1 = qubit(cqc)
    q2 = qubit(cqc)
    q1.H()
    q2.H()
    cqc.set_pending(True)
    q1.cphase(q2)
    cqc.flush_factory(3)
    cqc.set_pending(False)
    q2.H()
    q1.measure()
    return q2


class FactoryGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iterations = 100
        sys.stdout.write("Testing factory gates with {} iterations \r\n".format(cls.iterations))

        simulaqron_settings.default_settings()
        cls.network = Network(force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def testIFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test I factory
            sys.stdout.write("Testing I factory:")
            exp_values = calc_exp_values_single(prep_I_state())
            ans = cqc.test_preparation(prep_I_CQC_FACTORY, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testXFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            sys.stdout.write("Testing X factory (odd):")
            exp_values = calc_exp_values_single(prep_X_state())
            ans = cqc.test_preparation(prep_X_CQC_FACTORY_ODD, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test X factory even
            sys.stdout.write("Testing X factory (even):")
            exp_values = calc_exp_values_single(prep_I_state())
            ans = cqc.test_preparation(prep_X_CQC_FACTORY_EVEN, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testYFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test Y factory odd
            sys.stdout.write("Testing Y factory (odd):")
            exp_values = calc_exp_values_single(prep_Y_state())
            ans = cqc.test_preparation(prep_Y_CQC_FACTORY_ODD, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test Y factory even
            sys.stdout.write("Testing Y factory (even):")
            exp_values = calc_exp_values_single(prep_I_state())
            ans = cqc.test_preparation(prep_Y_CQC_FACTORY_EVEN, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testZFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test Z factory odd
            sys.stdout.write("Testing Z factory (odd):")
            exp_values = calc_exp_values_single(prep_Z_state())
            ans = cqc.test_preparation(prep_Z_CQC_FACTORY_ODD, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test Z factory even
            sys.stdout.write("Testing Z factory (even):")
            exp_values = calc_exp_values_single(prep_I_state())
            ans = cqc.test_preparation(prep_Z_CQC_FACTORY_EVEN, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testTFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test T factory quarter
            sys.stdout.write("Testing T factory (quarter):")
            exp_values = calc_exp_values_single(prep_T_state(1))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(
                        prep_T_CQC_FACTORY_QUARTER, exp_values, iterations=self.iterations, progress=False
                    )
            else:
                ans = cqc.test_preparation(prep_T_CQC_FACTORY_QUARTER, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

            # Test T factory half
            sys.stdout.write("Testing T factory (half):")
            exp_values = calc_exp_values_single(prep_T_state(2))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(
                        prep_T_CQC_FACTORY_HALF, exp_values, iterations=self.iterations, progress=False
                    )
            else:
                ans = cqc.test_preparation(prep_T_CQC_FACTORY_HALF, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

            # Test T factory half
            sys.stdout.write("Testing T factory (three quarters):")
            exp_values = calc_exp_values_single(prep_T_state(3))
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(
                        prep_T_CQC_FACTORY_THREE_QUARTER, exp_values, iterations=self.iterations, progress=False
                    )
            else:
                ans = cqc.test_preparation(prep_T_CQC_FACTORY_THREE_QUARTER, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

            # Test T factory half
            sys.stdout.write("Testing T factory (full):")
            exp_values = calc_exp_values_single(prep_I_state())
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(
                        prep_T_CQC_FACTORY_FULL, exp_values, iterations=self.iterations, progress=False
                    )
            else:
                ans = cqc.test_preparation(prep_T_CQC_FACTORY_FULL, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testHFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test H factory odd
            sys.stdout.write("Testing H factory (odd):")
            exp_values = calc_exp_values_single(prep_H_state())
            ans = cqc.test_preparation(prep_H_CQC_FACTORY_ODD, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test H factory even
            sys.stdout.write("Testing H factory (even):")
            exp_values = calc_exp_values_single(prep_I_state())
            ans = cqc.test_preparation(prep_H_CQC_FACTORY_EVEN, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testKFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test K factory odd
            sys.stdout.write("Testing K factory (odd):")
            exp_values = calc_exp_values_single(prep_K_state())
            ans = cqc.test_preparation(prep_K_CQC_FACTORY_ODD, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test K factory even
            sys.stdout.write("Testing K factory (even):")
            exp_values = calc_exp_values_single(prep_I_state())
            ans = cqc.test_preparation(prep_K_CQC_FACTORY_EVEN, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testRot_X_Factory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test ROT_X factory pi/8
            # TODO, add these tests when decided that we make it possible to do this
            # (As of writing at 2018/03/27 the angle of rotation is (up to a factor 2pi/256)
            # To the amount of times this rotation is done
            sys.stdout.write("Testing CNOT rotation of 4 times 1/32:")
            exp_values = calc_exp_values_single(prep_ROT_X_state())
            if simulaqron_settings.backend == "stabilizer":
                with self.assertRaises(CQCUnsuppError):
                    cqc.test_preparation(prep_ROT_X, exp_values, iterations=self.iterations, progress=False)
            else:
                ans = cqc.test_preparation(prep_ROT_X, exp_values, iterations=self.iterations)
                sys.stdout.write("\r")
                self.assertTrue(ans)

    def testCNOTFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test CNOT Factory Control even
            sys.stdout.write("Testing CNOT factory control even:")
            exp_values = calc_exp_values_single(prep_H_state())
            ans = cqc.test_preparation(prep_CNOT_control_CQC_FACTORY_even, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test CNOT Factory Control odd
            sys.stdout.write("Testing CNOT factory control odd:")
            exp_values = calc_exp_values_two(prep_mixed_state())
            ans = cqc.test_preparation(prep_CNOT_control_CQC_FACTORY_odd, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test CNOT Factory target even
            sys.stdout.write("Testing CNOT factory target even:")
            exp_values = calc_exp_values_single(prep_I_state())
            ans = cqc.test_preparation(prep_CNOT_target_CQC_FACTORY_even, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test CNOT Factory target odd
            sys.stdout.write("Testing CNOT factory target odd:")
            exp_values = calc_exp_values_two(prep_mixed_state())
            ans = cqc.test_preparation(prep_CNOT_target_CQC_FACTORY_odd, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def testCPhaseFactory(self):
        with CQCConnection("Alice", appID=1) as cqc:
            # Test CPHASE Factory Control even
            sys.stdout.write("Testing CPHASE factory control even:")
            exp_values = calc_exp_values_single(prep_H_state())
            ans = cqc.test_preparation(prep_CPHASE_control_CQC_FACTORY_even, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test CPHASE Factory Control odd
            sys.stdout.write("Testing CPHASE factory control odd:")
            exp_values = calc_exp_values_two(prep_mixed_state())
            ans = cqc.test_preparation(prep_CPHASE_control_CQC_FACTORY_odd, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test CPHASE Factory target even
            sys.stdout.write("Testing CPHASE factory target even:")
            exp_values = calc_exp_values_single(prep_I_state())
            ans = cqc.test_preparation(prep_CPHASE_target_CQC_FACTORY_even, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

            # Test CPHASE Factory target odd
            sys.stdout.write("Testing CPHASE factory target odd:")
            exp_values = calc_exp_values_two(prep_mixed_state())
            ans = cqc.test_preparation(prep_CPHASE_target_CQC_FACTORY_odd, exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)


if __name__ == "__main__":
    unittest.main()

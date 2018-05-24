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

from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *
from SimulaQron.cqc.pythonLib.cqc import *
import qutip
import numpy as np
import sys


def calc_exp_values(q):
	"""
	Calculates the expected value for measurements in the X,Y and Z basis and returns these in a tuple.
	q should be a qutip object
	"""
	# eigenvectors
	z0 = qutip.basis(2, 0)
	z1 = qutip.basis(2, 1)
	x1 = 1 / np.sqrt(2) * (z0 - z1)
	y1 = 1 / np.sqrt(2) * (z0 - 1j * z1)

	# projectors
	P_X1 = x1 * x1.dag()
	P_Y1 = y1 * y1.dag()
	P_Z1 = z1 * z1.dag()

	# probabilities
	p_x = (q.dag() * P_X1 * q).tr()
	p_y = (q.dag() * P_Y1 * q).tr()
	p_z = (q.dag() * P_Z1 * q).tr()

	return (p_x, p_y, p_z)


def prep_I_CQC(cqc):
	q = qubit(cqc, print_info=False)
	q.I(print_info=False)
	return q


def prep_X_CQC(cqc):
	q = qubit(cqc, print_info=False)
	q.X(print_info=False)
	return q


def prep_X_qutip():
	q = qutip.basis(2)
	X = qutip.sigmax()
	return X * q


def prep_Y_CQC(cqc):
	q = qubit(cqc, print_info=False)
	q.Y(print_info=False)
	return q


def prep_Y_qutip():
	q = qutip.basis(2)
	Y = qutip.sigmay()
	return Y * q


def prep_Z_CQC(cqc):
	q = qubit(cqc, print_info=False)
	q.Z(print_info=False)
	return q


def prep_Z_qutip():
	q = qutip.basis(2)
	Z = qutip.sigmaz()
	return Z * q


def prep_H_CQC(cqc):
	q = qubit(cqc, print_info=False)
	q.H(print_info=False)
	return q


def prep_H_qutip():
	q = qutip.basis(2)
	X = 1 / np.sqrt(2) * (qutip.sigmax() + qutip.sigmaz())
	return X * q


def prep_T_CQC(cqc):
	q = qubit(cqc, print_info=False)
	q.T(print_info=False)
	return q


def prep_T_qutip():
	q = qutip.basis(2)
	T = qutip.Qobj([[1, 0], [0, np.exp(1j * np.pi / 4)]], dims=[[2], [2]])
	return T * q


def prep_K_CQC(cqc):
	q = qubit(cqc, print_info=False)
	q.K(print_info=False)
	return q


def prep_K_qutip():
	q = qutip.basis(2)
	K = 1 / np.sqrt(2) * (qutip.sigmay() + qutip.sigmaz())
	return K * q


def prep_rotx1_CQC(cqc):  # pi/8
	q = qubit(cqc, print_info=False)
	q.rot_X(16, print_info=False)
	return q


def prep_rotx2_CQC(cqc):  # 5*pi/8
	q = qubit(cqc, print_info=False)
	q.rot_X(80, print_info=False)
	return q


def prep_roty1_CQC(cqc):  # pi/8
	q = qubit(cqc, print_info=False)
	q.rot_Y(16, print_info=False)
	return q


def prep_roty2_CQC(cqc):  # 5*pi/8
	q = qubit(cqc, print_info=False)
	q.rot_Y(80, print_info=False)
	return q


def prep_rotz1_CQC(cqc):  # pi/8
	q = qubit(cqc, print_info=False)
	q.rot_Z(16, print_info=False)
	return q


def prep_rotz2_CQC(cqc):  # 5*pi/8
	q = qubit(cqc, print_info=False)
	q.rot_Z(80, print_info=False)
	return q


def prep_rot_qutip(n, a):
	q = qutip.basis(2)
	nNorm = np.linalg.norm(n)
	R = (-1j * a / (2 * nNorm) * (n[0] * qutip.sigmax() + n[1] * qutip.sigmay() + n[2] * qutip.sigmaz())).expm()
	return R * q


def prep_reset_CQC(cqc):
	q = qubit(cqc, print_info=False)
	q.H(print_info=False)
	q.reset(print_info=False)
	return q


def prep_I_qutip():
	q = qutip.basis(2)
	return q


#####################################################################################################
class TwoQubitGateTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.iterations = 100
		sys.stdout.write("Testing two qubit gates gates with {} iterations \r\n".format(cls.iterations))

	def tearDown(self):
		self.cqc.close()

	def setUp(self):
		# Initialize the connection
		self.cqc = CQCConnection("Alice", appID=0, print_info=False)

	def testIGate(self):
		# Test I
		sys.stdout.write("Testing I gate:")
		exp_values = calc_exp_values(prep_I_qutip())
		ans = self.cqc.test_preparation(prep_I_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testXGate(self):
		# Test X
		sys.stdout.write("Testing X gate:")
		exp_values = calc_exp_values(prep_X_qutip())
		ans = self.cqc.test_preparation(prep_X_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testYGate(self):
		# Test Y
		sys.stdout.write("Testing Y gate:")
		exp_values = calc_exp_values(prep_Y_qutip())
		ans = self.cqc.test_preparation(prep_Y_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testZGate(self):
		# Test Z
		sys.stdout.write("Testing Z gate:")
		exp_values = calc_exp_values(prep_Z_qutip())
		ans = self.cqc.test_preparation(prep_Z_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testHGate(self):
		# Test H
		sys.stdout.write("Testing H gate:")
		exp_values = calc_exp_values(prep_H_qutip())
		ans = self.cqc.test_preparation(prep_H_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testTGate(self):
		# Test T
		sys.stdout.write("Testing T gate:")
		exp_values = calc_exp_values(prep_T_qutip())
		ans = self.cqc.test_preparation(prep_T_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testKGate(self):
		# Test K
		sys.stdout.write("Testing K gate:")
		exp_values = calc_exp_values(prep_K_qutip())
		ans = self.cqc.test_preparation(prep_K_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testXpi8Rot(self):
		# Test ROT_X pi/8
		sys.stdout.write("Testing rotation (X,pi/8) gate:")
		exp_values = calc_exp_values(prep_rot_qutip([1, 0, 0], np.pi / 8))
		ans = self.cqc.test_preparation(prep_rotx1_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testX5pi8Rot(self):
		# Test ROT_X 5*pi/8
		sys.stdout.write("Testing rotation (X,5*pi/8) gate:")
		exp_values = calc_exp_values(prep_rot_qutip([1, 0, 0], 5 * np.pi / 8))
		ans = self.cqc.test_preparation(prep_rotx2_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testYpi8Rot(self):
		# Test ROT_Y pi/8
		sys.stdout.write("Testing rotation (Y,pi/8) gate:")
		exp_values = calc_exp_values(prep_rot_qutip([0, 1, 0], np.pi / 8))
		ans = self.cqc.test_preparation(prep_roty1_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testY5pi8Rot(self):
		# Test ROT_Y 5*pi/8
		sys.stdout.write("Testing rotation (Y,5*pi/8) gate:")
		exp_values = calc_exp_values(prep_rot_qutip([0, 1, 0], 5 * np.pi / 8))
		ans = self.cqc.test_preparation(prep_roty2_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testZpi8Rot(self):
		# Test ROT_Z pi/8
		sys.stdout.write("Testing rotation (Z,pi/8) gate:")
		exp_values = calc_exp_values(prep_rot_qutip([0, 0, 1], np.pi / 8))
		ans = self.cqc.test_preparation(prep_rotz1_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testZ5pi8Rot(self):
		# Test ROT_Z 5*pi/8
		sys.stdout.write("Testing rotation (Z,5*pi/8) gate:")
		exp_values = calc_exp_values(prep_rot_qutip([0, 0, 1], 5 * np.pi / 8))
		ans = self.cqc.test_preparation(prep_rotz2_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)

	def testReset(self):
		# Test RESET
		sys.stdout.write("Testing RESET:")
		exp_values = calc_exp_values(prep_I_qutip())
		ans = self.cqc.test_preparation(prep_reset_CQC, exp_values, iterations=self.iterations)
		sys.stdout.write('\r')
		self.assertTrue(ans)


##################################################################################################

if __name__ == '__main__':
	unittest.main()


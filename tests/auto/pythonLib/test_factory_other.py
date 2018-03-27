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
from cqc.pythonLib.cqc import CQCConnection, qubit, CQCNoQubitError


class CQCFactoryTest(unittest.TestCase):
	_cqc = None
	iterations = 8

	def tearDown(self):
		self.cqc.close()

	def setUp(self):
		self.cqc = CQCConnection("Alice", appID=1)

	def testNew(self):
		qubits = self.cqc.sendFactory(2, CQC_CMD_NEW, self.iterations)
		self.assertEqual(len(qubits), self.iterations)
		for q in qubits:
			self.assertEqual(0, q.measure(print_info=False))

	def testMeasure(self):
		q = qubit(self.cqc)
		q.X()  # Let's do an X so all measurement outcomes should be 1
		# (to show no reinitialisation)
		with self.assertRaises(CQCNoQubitError):
			self.cqc.sendFactory(q._qID, CQC_CMD_MEASURE, self.iterations)

	def testMeasureInplace(self):
		q = qubit(self.cqc)
		q.X()  # Let's do an X so all measurement outcomes should be 1
		# (to show no reinitialisation)
		m = self.cqc.sendFactory(q._qID, CQC_CMD_MEASURE_INPLACE, self.iterations)
		self.assertEqual(len(m), self.iterations)
		self.assertTrue(x == 1 for x in m)
		q.measure(print_info=False)


if __name__ == '__main__':
	unittest.main()

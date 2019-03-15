#
# Copyright (c) 2017, Stephanie Wehner
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

from simulaqron.toolbox import has_module

if has_module.main("qutip"):

    from simulaqron.virtNode.qutipSimulator import qutipEngine

    _has_module = True

else:

    _has_module = False


def if_has_module(test):
    def new_test(self):
        if _has_module:
            test(self)

    return new_test


class TestQutipEngine(unittest.TestCase):
    @if_has_module
    def test_tracing(self):
        se = qutipEngine("alice", 0, 10)
        se2 = qutipEngine("Alice", 0, 10)

        se.add_fresh_qubit()
        se.add_fresh_qubit()
        se.add_fresh_qubit()

        se2.add_fresh_qubit()
        se2.add_fresh_qubit()
        se2.add_fresh_qubit()

        se.apply_X(0)
        se.apply_X(2)
        se2.apply_X(0)
        se2.apply_X(1)

        se.remove_qubit(1)
        se2.remove_qubit(2)

        self.assertEqual(se.qubitReg, se2.qubitReg)

    @if_has_module
    def test_gates(self):
        se = qutipEngine("alice", 0, 10)
        se.add_fresh_qubit()
        savedQubit = se.qubitReg

        se.apply_H(0)
        se.apply_Z(0)
        se.apply_H(0)
        se.apply_X(0)

        self.assertEqual(savedQubit, se.qubitReg)

    @if_has_module
    def test_measure(self):
        se = qutipEngine("alice", 0)

        se.add_fresh_qubit()
        outcome = se.measure_qubit(0)
        self.assertEqual(outcome, 0)

        se.add_fresh_qubit()
        se.apply_X(0)
        outcome = se.measure_qubit(0)
        self.assertEqual(outcome, 1)


if __name__ == '__main__':
    if _has_module:
        unittest.main()

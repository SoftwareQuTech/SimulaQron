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
import logging
from threading import Thread
from time import sleep

import virtNode
from defer import Deferred
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.spread import pb
from SimulaQron.virtNode.basics import QuantumError
from SimulaQron.virtNode.crudeSimulator import SimpleEngine
from SimulaQron.virtNode.quantum import SimulatedQubit, DeferredList
from SimulaQron.virtNode.virtual import VirtualQubit
from twisted.trial import unittest


# make sure to run the test using twisted trial


class TempRoot:
    def __init__(self, register):
        self.register = register

    def _remove_sim_qubit(self, sim_qubit):
        self.register.remove_qubit(sim_qubit.num)


class TempNode:
    def __init__(self, register):
        self.name = "TempTestNode"
        self.root = TempRoot(register)


class TempRegister(SimpleEngine):
    """
    Overwrites the actual register to simulate artificial delays in operations
    """

    def apply_X(self, qubitNum):
        sleep(0.1)
        super().apply_X(qubitNum)

    def apply_H(self, qubitNum):
        super().apply_H(qubitNum)


class FakeSimulatedQubit(SimulatedQubit):

    def remote_apply_H(self):
        self._do_operation("H", self.register.apply_H)

    def remote_apply_X(self):
        self._do_operation("X", self.register.apply_X)

    def remote_apply_Y(self):
        self._do_operation("Y", self.register.apply_Y)

    def remote_apply_Z(self):
        self._do_operation("Z", self.register.apply_Z)


class SingleQubitGateTest(unittest.TestCase):
    """
    Tests the _single_gate function of virtual, with artificial delays to make sure operations are done in correct order
    """

    def setUp(self):
        self.register = TempRegister()
        num = self.register.add_fresh_qubit()
        temp_node = TempNode(self.register)
        sim_qubit = SimulatedQubit(temp_node, self.register, num)
        fake_sim_qubit = FakeSimulatedQubit(temp_node, self.register, num)

        self.virtual_qubit = VirtualQubit(temp_node, temp_node, sim_qubit, num)
        # For testing if wrong implementation goes wrong
        self.fake_qubit = VirtualQubit(temp_node, temp_node, fake_sim_qubit, num)

    def tearDown(self):
        a = self.flushLoggedErrors(Exception)

    @inlineCallbacks
    def test_measure(self):
        outcome = yield self.virtual_qubit.remote_measure(inplace=True)
        self.assertEqual(outcome, 0)
        outcome = yield self.virtual_qubit.remote_measure(inplace=False)
        self.assertEqual(outcome, 0)
        self.assertRaises(QuantumError, self.virtual_qubit.remote_measure, inplace=False)

    @inlineCallbacks
    def test_simple_X(self):
        self.virtual_qubit._single_gate("apply_X")
        outcome = yield self.virtual_qubit.remote_measure(inplace=True)
        self.assertEqual(outcome, 1)
        self.virtual_qubit._single_gate("apply_X")
        outcome = yield self.virtual_qubit.remote_measure(inplace=False)
        self.assertEqual(outcome, 0)

    def test_locking_order(self):
        """
        This test checks if the qubit/register is correctly locked, by artificially delaying operations
        """

        def do_op(operation, delay=0):
            sleep(delay)
            self.virtual_qubit._single_gate(operation)

        t1 = Thread(target=do_op, kwargs={"operation": "apply_H", "delay": 0})
        t2 = Thread(target=do_op, kwargs={"operation": "apply_X", "delay": 0.01})
        t3 = Thread(target=do_op, kwargs={"operation": "apply_H", "delay": 0.02})
        t4 = Thread(target=do_op, kwargs={"operation": "apply_X", "delay": 0.03})

        # # self.virtual_qubit._single_gate("apply_H")
        # self.virtual_qubit._single_gate("apply_X")
        # self.virtual_qubit._single_gate("apply_H")
        # self.virtual_qubit._single_gate("apply_X")

        @inlineCallbacks
        def test_outcome():
            outcome = yield self.virtual_qubit.remote_measure(inplace=False)
            self.assertEqual(outcome, 1)

        t5 = Thread(target=test_outcome)

        t1.start()
        t2.start()
        t3.start()
        t4.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()

        t5.start()
        t5.join()

    def test_order_without_lock(self):
        """
        This test checks if the qubit/register is correctly locked, by artificially delaying operations
        """

        def do_op(operation, delay=0):
            sleep(delay)
            self.fake_qubit._single_gate(operation)

        t1 = Thread(target=do_op, kwargs={"operation": "apply_H", "delay": 0})
        t2 = Thread(target=do_op, kwargs={"operation": "apply_X", "delay": 0.01})
        t3 = Thread(target=do_op, kwargs={"operation": "apply_H", "delay": 0.02})
        t4 = Thread(target=do_op, kwargs={"operation": "apply_X", "delay": 0.03})

        # # self.virtual_qubit._single_gate("apply_H")
        # self.virtual_qubit._single_gate("apply_X")
        # self.virtual_qubit._single_gate("apply_H")
        # self.virtual_qubit._single_gate("apply_X")

        @inlineCallbacks
        def test_outcome():
            outcome = yield self.fake_qubit.remote_measure(inplace=False)
            self.assertEqual(outcome, 0)

        t5 = Thread(target=test_outcome)

        t1.start()
        t2.start()
        t3.start()
        t4.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()

        t5.start()
        t5.join()

    def test_measure_order(self):
        @inlineCallbacks
        def meas(delay, expected_outcome):
            sleep(delay)
            outcome = yield self.virtual_qubit.remote_measure(inplace=True)
            self.assertEqual(outcome, expected_outcome)

        def do_op(operation, delay=0):
            sleep(delay)
            self.virtual_qubit._single_gate(operation)

        t1 = Thread(target=meas, kwargs={"delay": 0, "expected_outcome": 0})
        t2 = Thread(target=do_op, kwargs={"operation": "apply_X", "delay": 0.01})
        t3 = Thread(target=meas, kwargs={"delay": 0.02, "expected_outcome": 1})
        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()


logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.WARNING)
#
if __name__ == '__main__':
    # unittest.main()
    logging.warning("Run this test using twisted trial! not regular python")

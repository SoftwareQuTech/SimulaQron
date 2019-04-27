####################################################################################
# Here we test the optional noise when T1 is much smaller than the time
# the qubit spent in the memory. The qubit should therefore be completely mixed,
# independently of the original state.
#
# Author: Axel Dahlberg
####################################################################################

import unittest
import sys

from cqc.pythonLib import CQCConnection, qubit
from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings


def prep_z0(cqc):
    q = qubit(cqc)
    return q


def prep_z1(cqc):
    q = qubit(cqc)
    q.X()
    return q


def prep_x0(cqc):
    q = qubit(cqc)
    q.H()
    return q


def prep_x1(cqc):
    q = qubit(cqc)
    q.X()
    q.H()
    return q


def prep_y0(cqc):
    q = qubit(cqc)
    q.K()
    return q


def prep_y1(cqc):
    q = qubit(cqc)
    q.X()
    q.K()
    return q


class TestOptionalNoise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exp_values = (1 / 2, 1 / 2, 1 / 2)
        cls.iterations = 100

        simulaqron_settings.default_settings()
        simulaqron_settings.noisy_qubits = True
        simulaqron_settings.t1 = 0.0001

        cls.network = Network(nodes=["Alice"], force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        simulaqron_settings.default_settings()

    def test_z0(self):
        with CQCConnection("Alice") as cqc:
            sys.stdout.write("Testing noise on state |0>")
            ans = cqc.test_preparation(prep_z0, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_z1(self):
        with CQCConnection("Alice") as cqc:
            sys.stdout.write("Testing noise on state |1>")
            ans = cqc.test_preparation(prep_z1, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_x0(self):
        with CQCConnection("Alice") as cqc:
            sys.stdout.write("Testing noise on state (|0>+|1>)/sqrt(2)")
            ans = cqc.test_preparation(prep_x0, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_x1(self):
        with CQCConnection("Alice") as cqc:
            sys.stdout.write("Testing noise on state (|0>-|1>)/sqrt(2)")
            ans = cqc.test_preparation(prep_x1, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_y0(self):
        with CQCConnection("Alice") as cqc:
            sys.stdout.write("Testing noise on state (|0>+i|1>)/sqrt(2)")
            ans = cqc.test_preparation(prep_y0, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_y1(self):
        with CQCConnection("Alice") as cqc:
            sys.stdout.write("Testing noise on state (|0>-i|1>)/sqrt(2)")
            ans = cqc.test_preparation(prep_y1, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)


if __name__ == "__main__":
    unittest.main()

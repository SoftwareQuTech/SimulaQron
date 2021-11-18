####################################################################################
# Here we test the optional noise when T1 is much smaller than the time
# the qubit spent in the memory. The qubit should therefore be completely mixed,
# independently of the original state.
#
# Author: Axel Dahlberg
####################################################################################

import unittest
import sys

from simulaqron.sdk.connection import SimulaQronConnection
from netqasm.sdk import Qubit
from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings


def prep_z0(conn):
    q = Qubit(conn)
    return q


def prep_z1(conn):
    q = Qubit(conn)
    q.X()
    return q


def prep_x0(conn):
    q = Qubit(conn)
    q.H()
    return q


def prep_x1(conn):
    q = Qubit(conn)
    q.X()
    q.H()
    return q


def prep_y0(conn):
    q = Qubit(conn)
    q.K()
    return q


def prep_y1(conn):
    q = Qubit(conn)
    q.X()
    q.K()
    return q


@unittest.skip("Optional noise is currenlty not supported in the new version of simulaqron")
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
        with SimulaQronConnection("Alice") as conn:
            sys.stdout.write("Testing noise on state |0>")
            ans = conn.test_preparation(prep_z0, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_z1(self):
        with SimulaQronConnection("Alice") as conn:
            sys.stdout.write("Testing noise on state |1>")
            ans = conn.test_preparation(prep_z1, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_x0(self):
        with SimulaQronConnection("Alice") as conn:
            sys.stdout.write("Testing noise on state (|0>+|1>)/sqrt(2)")
            ans = conn.test_preparation(prep_x0, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_x1(self):
        with SimulaQronConnection("Alice") as conn:
            sys.stdout.write("Testing noise on state (|0>-|1>)/sqrt(2)")
            ans = conn.test_preparation(prep_x1, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_y0(self):
        with SimulaQronConnection("Alice") as conn:
            sys.stdout.write("Testing noise on state (|0>+i|1>)/sqrt(2)")
            ans = conn.test_preparation(prep_y0, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)

    def test_y1(self):
        with SimulaQronConnection("Alice") as conn:
            sys.stdout.write("Testing noise on state (|0>-i|1>)/sqrt(2)")
            ans = conn.test_preparation(prep_y1, exp_values=self.exp_values, iterations=self.iterations)
            sys.stdout.write("\r")
            self.assertTrue(ans)


if __name__ == "__main__":
    unittest.main()

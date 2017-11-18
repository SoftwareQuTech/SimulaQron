from SimulaQron.virtNode.crudeSimulator import simpleEngine
from SimulaQron.local.setup import prepare_qubit

import numpy as np
import nose


def check_probabilities(alpha, beta):
    se = simpleEngine()
    expected_pa = abs(alpha) ** 2
    expected_pb = abs(beta) ** 2
    a, b = 0, 0

    for i in range(1000):
        qb = prepare_qubit(alpha, beta)
        se.add_qubit(qb)

        outcome = se.measure_qubit(0)
        a += outcome == 0
        b += outcome == 1

    pa = a / 1000
    pb = b / 1000

    nose.tools.assert_almost_equal(pa, expected_pa, delta=0.1 * expected_pa)
    nose.tools.assert_almost_equal(pb, expected_pb, delta=0.1 * expected_pb)


def test_prepare_qubit_0():
    yield check_probabilities, 1, 0


def test_prepare_qubit_1():
    yield check_probabilities, 0, 1


def test_prepare_qubit_equal():
    yield check_probabilities, 1 / np.sqrt(2), 1 / np.sqrt(2)


def test_prepare_qubit_unequal():
    yield check_probabilities, 1 / np.sqrt(3), np.sqrt(2 / 3)


def test_prepare_qubit_exception():
    nose.tools.assert_raises(ValueError, prepare_qubit, 1, 1)


nose.main(argv=['','-v']).runTests()
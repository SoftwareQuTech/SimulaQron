import unittest
import numpy as np

from simulaqron.toolbox import has_module

if has_module.main("pyqrack"):

    from simulaqron.virtNode.pyqrackSimulator import pyqrackEngine
    from simulaqron.virtNode.basics import noQubitError, quantumError

    _has_module = True

else:

    _has_module = False


def if_has_module(test):
    def new_test(self):
        if _has_module:
            test(self)

    return new_test


class TestPyQrackEngine_init(unittest.TestCase):
    @if_has_module
    def test_init(self):
        eng = pyqrackEngine("Alice", 0)
        self.assertEqual(eng.maxQubits, 10)
        self.assertEqual(eng.activeQubits, 0)
        self.assertEqual(len(eng.qubitReg), 0)

        eng = pyqrackEngine("Alice", 0, 5)
        self.assertEqual(eng.maxQubits, 5)
        self.assertEqual(eng.activeQubits, 0)
        self.assertEqual(len(eng.qubitReg), 0)


class TestPyQrackEngine(unittest.TestCase):
    @if_has_module
    def setUp(self):
        self.eng = pyqrackEngine("Alice", 0)

    @staticmethod
    def abs_inner_product(state, ref):
        comb_state = np.array(state[0]) + 1j * np.array(state[1])
        inner = np.dot(comb_state, np.array(ref).conj())
        return np.abs(inner)

    @if_has_module
    def test_add_fresh_qubit(self):
        num = self.eng.add_fresh_qubit()
        self.assertEqual(num, 0)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        self.assertTrue(isinstance(self.eng.qubitReg[num], int))

    @if_has_module
    def test_add_to_many_fresh_qubits(self):
        for _ in range(10):
            self.eng.add_fresh_qubit()
        with self.assertRaises(noQubitError):
            self.eng.add_fresh_qubit()

    @if_has_module
    def test_add_qubit(self):
        new_state = [1, 0]
        num = self.eng.add_qubit(new_state)
        self.assertEqual(num, 0)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [0] * 10)

    @if_has_module
    def test_add_qubit_H(self):
        new_state = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        num = self.eng.add_qubit(new_state)
        self.assertEqual(num, 0)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        self.eng.apply_H(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [0] * 10)

    @if_has_module
    def test_add_unphysical_qubit(self):
        new_state = [1, 1]
        with self.assertRaises(quantumError):
            self.eng.add_qubit(new_state)

    @if_has_module
    def test_remove_qubit(self):
        num = self.eng.add_fresh_qubit()
        self.eng.remove_qubit(num)
        self.assertEqual(self.eng.activeQubits, 0)
        self.assertEqual(len(self.eng.qubitReg), 0)
        with self.assertRaises(quantumError):
            self.eng.remove_qubit(num)

    @if_has_module
    def test_get_register_RI(self):
        self.eng.add_fresh_qubit()
        self.eng.add_fresh_qubit()
        with self.assertRaises(NotImplementedError):
            self.eng.get_register_RI()

    @if_has_module
    def test_H(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.engine.z(num)
        self.eng.engine.h(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [1] * 10)

    @if_has_module
    def test_K(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_K(num)
        self.eng.apply_Z(num)
        self.eng.apply_H(num)
        self.eng.engine.adjs(num)
        self.eng.apply_H(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [0] * 10)

    @if_has_module
    def test_X(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [1] * 10)

    @if_has_module
    def test_Y(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_Y(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [1] * 10)
        self.eng.apply_H(num)
        self.eng.apply_Y(num)
        self.eng.engine.h(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [0] * 10)

    @if_has_module
    def test_Z(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Z(num)
        self.eng.engine.h(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [1] * 10)

    @if_has_module
    def test_Rx(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_rotation(num, (1, 0, 0), np.pi / 2)
        self.eng.engine.adjs(0)
        self.eng.apply_H(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [1] * 10)

    @if_has_module
    def test_Ry(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_rotation(num, (0, 1, 0), np.pi / 2)
        self.eng.apply_H(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [0] * 10)

    @if_has_module
    def test_Rz(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_rotation(num, (0, 0, 1), np.pi / 2)
        self.eng.engine.s(0)
        self.eng.apply_H(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [1] * 10)

    @if_has_module
    def test_faulty_rot(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        with self.assertRaises(NotImplementedError):
            self.eng.apply_rotation(num, (1, 0, 1), np.pi / 2)

    @if_has_module
    def test_cnot(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_X(num1)
        self.eng.apply_CNOT(num1, num2)
        results = self.eng.engine.measure_shots([num1, num2], 10)
        self.assertEqual(results, [3] * 10)

    @if_has_module
    def test_cz(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_X(num1)
        self.eng.apply_H(num2)
        self.eng.apply_CPHASE(num1, num2)
        self.eng.apply_H(num2)
        results = self.eng.engine.measure_shots([num1, num2], 10)
        self.assertEqual(results, [3] * 10)

    @if_has_module
    def test_measure0(self):
        num = self.eng.add_fresh_qubit()
        m = self.eng.measure_qubit(num)
        self.assertEqual(m, 0)
        self.assertEqual(self.eng.activeQubits, 0)

    @if_has_module
    def test_measure1(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        m = self.eng.measure_qubit(num)
        self.assertEqual(m, 1)
        self.assertEqual(self.eng.activeQubits, 0)

    @if_has_module
    def test_measure_inplace(self):
        num = self.eng.add_fresh_qubit()
        m = self.eng.measure_qubit_inplace(num)
        self.assertEqual(m, 0)
        self.assertEqual(self.eng.activeQubits, 1)

    @if_has_module
    def test_absorb_both_empty(self):
        eng2 = pyqrackEngine("Alice", 0)
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 0)
        self.assertEqual(len(self.eng.qubitReg), 0)

    @if_has_module
    def test_absorb_other_empty(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        eng2 = pyqrackEngine("Alice", 0)
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        self.eng.apply_Z(num)
        self.eng.apply_H(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [1] * 10)

    @if_has_module
    def test_absorb_this_empty_H(self):
        eng2 = pyqrackEngine("Alice", 0)
        num = eng2.add_fresh_qubit()
        eng2.apply_H(num)
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        self.eng.apply_Z(num)
        self.eng.apply_H(num)
        results = self.eng.engine.measure_shots([0], 10)
        self.assertEqual(results, [1] * 10)

    @if_has_module
    def test_absorb_this_empty_CNOT(self):
        eng2 = pyqrackEngine("Alice", 0)
        num1 = eng2.add_fresh_qubit()
        num2 = eng2.add_fresh_qubit()
        eng2.apply_X(num1)
        eng2.apply_CNOT(num1, num2)
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 2)
        self.assertEqual(len(self.eng.qubitReg), 2)
        results = self.eng.engine.measure_shots([num1, num2], 10)
        self.assertEqual(results, [3] * 10)

    @if_has_module
    def test_absorb_2GHZ(self):
        n = 5
        eng2 = pyqrackEngine("Alice", 0)
        for eng in [self.eng, eng2]:
            qubits = [eng.add_fresh_qubit() for _ in range(n)]
            eng.apply_H(qubits[0])
            for i in range(1, n):
                eng.apply_CNOT(qubits[0], qubits[i])
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 2 * n)
        self.assertEqual(len(self.eng.qubitReg), 2 * n)

    @if_has_module
    def test_absorb_to_big_this_empty(self):
        eng2 = pyqrackEngine("Alice", 0, 11)
        for _ in range(11):
            eng2.add_fresh_qubit()
        with self.assertRaises(quantumError):
            self.eng.absorb(eng2)

    @if_has_module
    def test_absorb_to_big(self):
        self.eng.add_fresh_qubit()
        eng2 = pyqrackEngine("Alice", 0)
        for _ in range(10):
            eng2.add_fresh_qubit()
        with self.assertRaises(quantumError):
            self.eng.absorb(eng2)

    @if_has_module
    def test_absorb_parts(self):
        self.eng.add_fresh_qubit()
        eng2 = pyqrackEngine("Alice", 0)
        eng2.add_fresh_qubit()
        with self.assertRaises(NotImplementedError):
            self.eng.absorb_parts([], [], eng2.activeQubits)


if __name__ == "__main__":
    if _has_module:
        unittest.main()

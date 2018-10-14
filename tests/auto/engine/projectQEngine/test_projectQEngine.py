import unittest
import numpy as np

from SimulaQron.virtNode.projectQSimulator import projectQEngine
from SimulaQron.virtNode.basics import noQubitError, quantumError

from projectq.types._qubit import Qureg


class TestProjectQEngine_init(unittest.TestCase):
    def test_init(self):
        eng = projectQEngine()
        self.assertEqual(eng.maxQubits, 10)
        self.assertEqual(eng.activeQubits, 0)
        self.assertEqual(len(eng.qubitReg), 0)

        eng = projectQEngine(5)
        self.assertEqual(eng.maxQubits, 5)
        self.assertEqual(eng.activeQubits, 0)
        self.assertEqual(len(eng.qubitReg), 0)


class TestProjectQEngine(unittest.TestCase):
    def setUp(self):
        self.eng = projectQEngine()

    def tearDown(self):
        for _ in range(self.eng.activeQubits):
            self.eng.measure_qubit(0)
        self.eng.eng.flush()

    @staticmethod
    def abs_inner_product(state, ref):
        comb_state = np.array(state[0]) + 1j * np.array(state[1])
        inner = np.dot(comb_state, np.array(ref).conj())
        return np.abs(inner)

    def test_add_fresh_qubit(self):
        num = self.eng.add_fresh_qubit()
        self.assertEqual(num, 0)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        self.assertTrue(isinstance(self.eng.qubitReg[num], Qureg))

    def test_add_to_many_qubits(self):
        for _ in range(10):
            self.eng.add_fresh_qubit()
        with self.assertRaises(noQubitError):
            self.eng.add_fresh_qubit()

    def test_remove_qubit(self):
        num = self.eng.add_fresh_qubit()
        self.eng.remove_qubit(num)
        self.assertEqual(self.eng.activeQubits, 0)
        self.assertEqual(len(self.eng.qubitReg), 0)
        with self.assertRaises(quantumError):
            self.eng.remove_qubit(num)

    def test_get_register_RI(self):
        self.eng.add_fresh_qubit()
        self.eng.add_fresh_qubit()
        state = self.eng.get_register_RI()
        self.assertAlmostEqual(self.abs_inner_product(state, [1, 0, 0, 0]), 1)

    def test_H(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        state = self.eng.get_register_RI()
        self.assertAlmostEqual(self.abs_inner_product(state, [1 / np.sqrt(2), 1 / np.sqrt(2)]), 1)

    def test_K(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_K(num)
        state = self.eng.get_register_RI()
        self.assertAlmostEqual(self.abs_inner_product(state, [1 / np.sqrt(2), 1j / np.sqrt(2)]), 1)

    def test_X(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        state = self.eng.get_register_RI()
        self.assertAlmostEqual(self.abs_inner_product(state, [0, 1]), 1)

    def test_Y(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Y(num)
        state = self.eng.get_register_RI()
        ref = [-1j / np.sqrt(2), 1j / np.sqrt(2)]
        self.assertAlmostEqual(self.abs_inner_product(state, ref), 1)

    def test_Z(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Z(num)
        state = self.eng.get_register_RI()
        ref = [1 / np.sqrt(2), -1 / np.sqrt(2)]
        self.assertAlmostEqual(self.abs_inner_product(state, ref), 1)

    def test_Rx(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_rotation(num, (1, 0, 0), np.pi/2)
        state = self.eng.get_register_RI()
        ref = [1 / np.sqrt(2), -1j / np.sqrt(2)]
        self.assertAlmostEqual(self.abs_inner_product(state, ref), 1)

    def test_Ry(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_rotation(num, (0, 1, 0), np.pi/2)
        state = self.eng.get_register_RI()
        ref = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        self.assertAlmostEqual(self.abs_inner_product(state, ref), 1)

    def test_Rz(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_rotation(num, (0, 0, 1), np.pi/2)
        state = self.eng.get_register_RI()
        ref = [1 / np.sqrt(2), 1j / np.sqrt(2)]
        self.assertAlmostEqual(self.abs_inner_product(state, ref), 1)

    def test_faulty_rot(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        with self.assertRaises(NotImplementedError):
            self.eng.apply_rotation(num, (1, 0, 1), np.pi/2)

    def test_cnot(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_H(num1)
        self.eng.apply_CNOT(num1, num2)
        state = self.eng.get_register_RI()
        ref = [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)]
        self.assertAlmostEqual(self.abs_inner_product(state, ref), 1)

    def test_cz(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_H(num1)
        self.eng.apply_H(num2)
        self.eng.apply_CPHASE(num1, num2)
        state = self.eng.get_register_RI()
        ref = [1 / 2, 1 / 2, 1 / 2, -1 / 2]
        self.assertAlmostEqual(self.abs_inner_product(state, ref), 1)

    def test_measure0(self):
        num = self.eng.add_fresh_qubit()
        m = self.eng.measure_qubit(num)
        self.assertEqual(m, 0)
        self.assertEqual(self.eng.activeQubits, 0)

    def test_measure1(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        m = self.eng.measure_qubit(num)
        self.assertEqual(m, 1)
        self.assertEqual(self.eng.activeQubits, 0)

    def test_measure_inplace(self):
        num = self.eng.add_fresh_qubit()
        m = self.eng.measure_qubit_inplace(num)
        self.assertEqual(m, 0)
        self.assertEqual(self.eng.activeQubits, 1)




if __name__ == '__main__':
    unittest.main()

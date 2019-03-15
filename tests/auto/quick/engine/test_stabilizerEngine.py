import unittest
import numpy as np

from simulaqron.virtNode.stabilizerSimulator import stabilizerEngine
from simulaqron.virtNode.basics import noQubitError, quantumError
from simulaqron.toolbox.stabilizerStates import StabilizerState


class TestStabilizerEngine_init(unittest.TestCase):
    def test_init(self):
        eng = stabilizerEngine("Alice", 0)
        self.assertEqual(eng.maxQubits, 10)
        self.assertEqual(eng.activeQubits, 0)
        self.assertEqual(len(eng.qubitReg), 0)

        eng = stabilizerEngine("Alice", 0, 5)
        self.assertEqual(eng.maxQubits, 5)
        self.assertEqual(eng.activeQubits, 0)
        self.assertEqual(len(eng.qubitReg), 0)


class TestStabilizerEngine(unittest.TestCase):
    def setUp(self):
        self.eng = stabilizerEngine("Alice", 0)

    def test_add_fresh_qubit(self):
        num = self.eng.add_fresh_qubit()
        self.assertEqual(num, 0)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)

    def test_add_to_many_fresh_qubits(self):
        for _ in range(10):
            self.eng.add_fresh_qubit()
        with self.assertRaises(noQubitError):
            self.eng.add_fresh_qubit()

    def test_add_qubit(self):
        new_state = [[0, 1]]
        num = self.eng.add_qubit(new_state)
        self.assertEqual(num, 0)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        state, _ = self.eng.get_register_RI()
        self.assertEqual(StabilizerState(state), StabilizerState(new_state))

    def test_add_qubit_H(self):
        new_state = [[1, 0]]
        num = self.eng.add_qubit(new_state)
        self.assertEqual(num, 0)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        state, _ = self.eng.get_register_RI()
        self.assertEqual(StabilizerState(state), StabilizerState(new_state))

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
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState(2))

    def test_H(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 0]]))

    def test_K(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_K(num)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 1]]))

    def test_X(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[0, 1, 1]]))

    def test_Y(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Y(num)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 0, 1]]))

    def test_Z(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Z(num)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 0, 1]]))

    def test_Rx(self):
        num = self.eng.add_fresh_qubit()
        with self.assertRaises(AttributeError):
            self.eng.apply_rotation(num, (1, 0, 0), np.pi / 2)

    def test_Ry(self):
        num = self.eng.add_fresh_qubit()
        with self.assertRaises(AttributeError):
            self.eng.apply_rotation(num, (0, 1, 0), np.pi / 2)

    def test_Rz(self):
        num = self.eng.add_fresh_qubit()
        with self.assertRaises(AttributeError):
            self.eng.apply_rotation(num, (0, 0, 1), np.pi / 2)

    def test_cnot(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_H(num1)
        self.eng.apply_CNOT(num1, num2)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]]))

    def test_cz(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_H(num1)
        self.eng.apply_H(num2)
        self.eng.apply_CPHASE(num1, num2)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 0, 0, 1], [0, 1, 1, 0]]))

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

    def test_absorb_both_empty(self):
        eng2 = stabilizerEngine("Alice", 0)
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 0)
        self.assertEqual(len(self.eng.qubitReg), 0)

    def test_absorb_other_empty(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        eng2 = stabilizerEngine("Alice", 0)
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 0]]))

    def test_absorb_this_empty_H(self):
        eng2 = stabilizerEngine("Alice", 0)
        num = eng2.add_fresh_qubit()
        eng2.apply_H(num)
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 0]]))

    def test_absorb_this_empty_CNOT(self):
        eng2 = stabilizerEngine("Alice", 0)
        num1 = eng2.add_fresh_qubit()
        num2 = eng2.add_fresh_qubit()
        eng2.apply_H(num1)
        eng2.apply_CNOT(num1, num2)
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 2)
        self.assertEqual(len(self.eng.qubitReg), 2)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]]))

    def test_absorb_this_empty_GHZ(self):
        n = 5
        eng2 = stabilizerEngine("Alice", 0)
        qubits = [eng2.add_fresh_qubit() for _ in range(n)]
        eng2.apply_H(qubits[0])
        for i in range(1, n):
            eng2.apply_CNOT(qubits[0], qubits[i])
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, n)
        self.assertEqual(len(self.eng.qubitReg), n)
        state, _ = self.eng.get_register_RI()
        ref = [1 / np.sqrt(2)] + [0] * (2 ** n - 2) + [1 / np.sqrt(2)]
        ref = [[1] * n + [0] * n]
        for i in range(n - 1):
            ref += [[0] * n + [0] * i + [1] * 2 + [0] * (n - i - 2)]
        self.assertTrue(StabilizerState(state) == StabilizerState(ref))

    def test_absorb_2GHZ(self):
        n = 5
        eng2 = stabilizerEngine("Alice", 0)
        for eng in [self.eng, eng2]:
            qubits = [eng.add_fresh_qubit() for _ in range(n)]
            eng.apply_H(qubits[0])
            for i in range(1, n):
                eng.apply_CNOT(qubits[0], qubits[i])
        self.eng.absorb(eng2)
        self.assertEqual(self.eng.activeQubits, 2 * n)
        self.assertEqual(len(self.eng.qubitReg), 2 * n)

    def test_absorb_to_big_this_empty(self):
        eng2 = stabilizerEngine("Alice", 0, 11)
        for _ in range(11):
            eng2.add_fresh_qubit()
        with self.assertRaises(quantumError):
            self.eng.absorb(eng2)

    def test_absorb_to_big(self):
        self.eng.add_fresh_qubit()
        eng2 = stabilizerEngine("Alice", 0)
        for _ in range(10):
            eng2.add_fresh_qubit()
        with self.assertRaises(quantumError):
            self.eng.absorb(eng2)

    def test_absorb_parts_both_empty(self):
        eng2 = stabilizerEngine("Alice", 0)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        self.assertEqual(self.eng.activeQubits, 0)
        self.assertEqual(len(self.eng.qubitReg), 0)

    def test_absorb_parts(self):
        self.eng.add_fresh_qubit()
        eng2 = stabilizerEngine("Alice", 0)
        eng2.add_fresh_qubit()
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        self.assertEqual(self.eng.activeQubits, 2)
        self.assertEqual(len(self.eng.qubitReg), 2)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]]))

    def test_absorb_parts_EPR(self):
        eng2 = stabilizerEngine("Alice", 0)
        num1 = eng2.add_fresh_qubit()
        num2 = eng2.add_fresh_qubit()
        eng2.apply_H(num1)
        eng2.apply_CNOT(num1, num2)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        self.assertEqual(self.eng.activeQubits, 2)
        self.assertEqual(len(self.eng.qubitReg), 2)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]]))

    def test_absorb_parts_other_empty(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        eng2 = stabilizerEngine("Alice", 0)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        self.assertEqual(self.eng.activeQubits, 1)
        self.assertEqual(len(self.eng.qubitReg), 1)
        state, _ = self.eng.get_register_RI()
        self.assertTrue(StabilizerState(state) == StabilizerState([[1, 0]]))


if __name__ == "__main__":
    unittest.main()

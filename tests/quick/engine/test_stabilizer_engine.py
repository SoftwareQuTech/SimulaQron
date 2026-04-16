import pytest
import numpy as np

from simulaqron.virtual_node.stabilizer_simulator import StabilizerEngine
from simulaqron.virtual_node.basics import NoQubitError, QuantumError
from simulaqron.toolbox.stabilizer_states import StabilizerState
from simulaqron.general import SimUnsupportedError


class TestStabilizerEngineInit:
    def test_init(self):
        eng = StabilizerEngine("Alice", 0)
        assert eng.maxQubits == 10
        assert eng.activeQubits == 0
        assert len(eng.qubitReg) == 0

        eng = StabilizerEngine("Alice", 0, 5)
        assert eng.maxQubits == 5
        assert eng.activeQubits == 0
        assert len(eng.qubitReg) == 0


class TestStabilizerEngine:
    @pytest.fixture(autouse=True)
    def engine(self):
        self.eng = StabilizerEngine("Alice", 0)

    def test_add_fresh_qubit(self):
        num = self.eng.add_fresh_qubit()
        assert num == 0
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1

    def test_add_to_many_fresh_qubits(self):
        for _ in range(10):
            self.eng.add_fresh_qubit()
        with pytest.raises(NoQubitError):
            self.eng.add_fresh_qubit()

    def test_add_qubit(self):
        new_state = [[0, 1]]
        num = self.eng.add_qubit(new_state)
        assert num == 0
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState(new_state)

    def test_add_qubit_H(self):
        new_state = [[1, 0]]
        num = self.eng.add_qubit(new_state)
        assert num == 0
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState(new_state)

    def test_remove_qubit(self):
        num = self.eng.add_fresh_qubit()
        self.eng.remove_qubit(num)
        assert self.eng.activeQubits == 0
        assert len(self.eng.qubitReg) == 0
        with pytest.raises(QuantumError):
            self.eng.remove_qubit(num)

    def test_get_register_RI(self):
        self.eng.add_fresh_qubit()
        self.eng.add_fresh_qubit()
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState(2)

    def test_H(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 0]])

    def test_K(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_K(num)
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 1]])

    def test_X(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[0, 1, 1]])

    def test_Y(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Y(num)
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 0, 1]])

    def test_Z(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Z(num)
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 0, 1]])

    def test_Rx(self):
        num = self.eng.add_fresh_qubit()
        with pytest.raises(SimUnsupportedError):
            self.eng.apply_rotation(num, (1, 0, 0), np.pi / 2)

    def test_Ry(self):
        num = self.eng.add_fresh_qubit()
        with pytest.raises(SimUnsupportedError):
            self.eng.apply_rotation(num, (0, 1, 0), np.pi / 2)

    def test_Rz(self):
        num = self.eng.add_fresh_qubit()
        with pytest.raises(SimUnsupportedError):
            self.eng.apply_rotation(num, (0, 0, 1), np.pi / 2)

    def test_cnot(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_H(num1)
        self.eng.apply_CNOT(num1, num2)
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])

    def test_cz(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_H(num1)
        self.eng.apply_H(num2)
        self.eng.apply_CPHASE(num1, num2)
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 0, 0, 1], [0, 1, 1, 0]])

    def test_measure0(self):
        num = self.eng.add_fresh_qubit()
        m = self.eng.measure_qubit(num)
        assert m == 0
        assert self.eng.activeQubits == 0

    def test_measure1(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        m = self.eng.measure_qubit(num)
        assert m == 1
        assert self.eng.activeQubits == 0

    def test_measure_inplace(self):
        num = self.eng.add_fresh_qubit()
        m = self.eng.measure_qubit_inplace(num)
        assert m == 0
        assert self.eng.activeQubits == 1

    def test_absorb_both_empty(self):
        eng2 = StabilizerEngine("Alice", 0)
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 0
        assert len(self.eng.qubitReg) == 0

    def test_absorb_other_empty(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        eng2 = StabilizerEngine("Alice", 0)
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 0]])

    def test_absorb_this_empty_H(self):
        eng2 = StabilizerEngine("Alice", 0)
        num = eng2.add_fresh_qubit()
        eng2.apply_H(num)
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 0]])

    def test_absorb_this_empty_CNOT(self):
        eng2 = StabilizerEngine("Alice", 0)
        num1 = eng2.add_fresh_qubit()
        num2 = eng2.add_fresh_qubit()
        eng2.apply_H(num1)
        eng2.apply_CNOT(num1, num2)
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 2
        assert len(self.eng.qubitReg) == 2
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])

    def test_absorb_this_empty_GHZ(self):
        n = 5
        eng2 = StabilizerEngine("Alice", 0)
        qubits = [eng2.add_fresh_qubit() for _ in range(n)]
        eng2.apply_H(qubits[0])
        for i in range(1, n):
            eng2.apply_CNOT(qubits[0], qubits[i])
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == n
        assert len(self.eng.qubitReg) == n
        state, _ = self.eng.get_register_RI()
        ref = [1 / np.sqrt(2)] + [0] * (2 ** n - 2) + [1 / np.sqrt(2)]
        ref = [[1] * n + [0] * n]
        for i in range(n - 1):
            ref += [[0] * n + [0] * i + [1] * 2 + [0] * (n - i - 2)]
        assert StabilizerState(state) == StabilizerState(ref)

    def test_absorb_2GHZ(self):
        n = 5
        eng2 = StabilizerEngine("Alice", 0)
        for eng in [self.eng, eng2]:
            qubits = [eng.add_fresh_qubit() for _ in range(n)]
            eng.apply_H(qubits[0])
            for i in range(1, n):
                eng.apply_CNOT(qubits[0], qubits[i])
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 2 * n
        assert len(self.eng.qubitReg) == 2 * n

    def test_absorb_to_big_this_empty(self):
        eng2 = StabilizerEngine("Alice", 0, 11)
        for _ in range(11):
            eng2.add_fresh_qubit()
        with pytest.raises(QuantumError):
            self.eng.absorb(eng2)

    def test_absorb_to_big(self):
        self.eng.add_fresh_qubit()
        eng2 = StabilizerEngine("Alice", 0)
        for _ in range(10):
            eng2.add_fresh_qubit()
        with pytest.raises(QuantumError):
            self.eng.absorb(eng2)

    def test_absorb_parts_both_empty(self):
        eng2 = StabilizerEngine("Alice", 0)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        assert self.eng.activeQubits == 0
        assert len(self.eng.qubitReg) == 0

    def test_absorb_parts(self):
        self.eng.add_fresh_qubit()
        eng2 = StabilizerEngine("Alice", 0)
        eng2.add_fresh_qubit()
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        assert self.eng.activeQubits == 2
        assert len(self.eng.qubitReg) == 2
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]])

    def test_absorb_parts_EPR(self):
        eng2 = StabilizerEngine("Alice", 0)
        num1 = eng2.add_fresh_qubit()
        num2 = eng2.add_fresh_qubit()
        eng2.apply_H(num1)
        eng2.apply_CNOT(num1, num2)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        assert self.eng.activeQubits == 2
        assert len(self.eng.qubitReg) == 2
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])

    def test_absorb_parts_other_empty(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        eng2 = StabilizerEngine("Alice", 0)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state, _ = self.eng.get_register_RI()
        assert StabilizerState(state) == StabilizerState([[1, 0]])

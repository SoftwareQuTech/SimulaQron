import numpy as np
import pytest

from importlib.util import find_spec

if find_spec("projectq") is not None:
    from simulaqron.virtual_node.project_q_simulator import ProjectQEngine
    from simulaqron.virtual_node.basics import NoQubitError, QuantumError

    from projectq.types._qubit import Qubit

enable_if_projectq = pytest.mark.skipif(
    find_spec("projectq") is None,
    reason="ProjectQ tests require the 'projectq' module"
)


class TestProjectQEnginInit:
    @enable_if_projectq
    def test_init(self):
        eng = ProjectQEngine("Alice", 0)
        assert eng.maxQubits == 10
        assert eng.activeQubits == 0
        assert len(eng.qubitReg) == 0

        eng = ProjectQEngine("Alice", 0, 5)
        assert eng.maxQubits == 5
        assert eng.activeQubits == 0
        assert len(eng.qubitReg) == 0


class TestProjectQEngine:
    @pytest.fixture(autouse=True)
    def engine(self):
        self.eng = ProjectQEngine("Alice", 0)
        yield
        del self.eng

    @staticmethod
    def _abs_inner_product(state, ref):
        comb_state = np.array(state[0]) + 1j * np.array(state[1])
        inner = np.dot(comb_state, np.array(ref).conj())
        return np.abs(inner)

    @enable_if_projectq
    def test_add_fresh_qubit(self):
        num = self.eng.add_fresh_qubit()
        assert num == 0
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        assert isinstance(self.eng.qubitReg[num], Qubit) is True

    @enable_if_projectq
    def test_add_to_many_fresh_qubits(self):
        for _ in range(10):
            self.eng.add_fresh_qubit()
        with pytest.raises(NoQubitError):
            self.eng.add_fresh_qubit()

    @enable_if_projectq
    def test_add_qubit(self):
        new_state = [1, 0]
        num = self.eng.add_qubit(new_state)
        assert num == 0
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state = self.eng.get_register_RI()[1]
        assert self._abs_inner_product(state, new_state) == pytest.approx(1)

    @enable_if_projectq
    def test_add_qubit_H(self):
        new_state = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        num = self.eng.add_qubit(new_state)
        assert num == 0
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state = self.eng.get_register_RI()[1]
        assert self._abs_inner_product(state, new_state) == pytest.approx(1)

    @enable_if_projectq
    def test_add_unphysical_qubit(self):
        new_state = [1, 1]
        with pytest.raises(QuantumError):
            self.eng.add_qubit(new_state)

    @enable_if_projectq
    def test_remove_qubit(self):
        num = self.eng.add_fresh_qubit()
        self.eng.remove_qubit(num)
        assert self.eng.activeQubits == 0
        assert len(self.eng.qubitReg) == 0
        with pytest.raises(QuantumError):
            self.eng.remove_qubit(num)

    @enable_if_projectq
    def test_get_register_RI(self):
        self.eng.add_fresh_qubit()
        self.eng.add_fresh_qubit()
        state = self.eng.get_register_RI()[1]
        assert self._abs_inner_product(state, [1, 0, 0, 0]) == pytest.approx(1)

    @enable_if_projectq
    def test_H(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        state = self.eng.get_register_RI()[1]
        assert self._abs_inner_product(state, [1 / np.sqrt(2), 1 / np.sqrt(2)]) == pytest.approx(1)

    @enable_if_projectq
    def test_K(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_K(num)
        state = self.eng.get_register_RI()[1]
        assert self._abs_inner_product(state, [1 / np.sqrt(2), 1j / np.sqrt(2)]) == pytest.approx(1)

    @enable_if_projectq
    def test_X(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        state = self.eng.get_register_RI()[1]
        assert self._abs_inner_product(state, [0, 1]) == pytest.approx(1)

    @enable_if_projectq
    def test_Y(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Y(num)
        state = self.eng.get_register_RI()[1]
        ref = [-1j / np.sqrt(2), 1j / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_Z(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_Z(num)
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), -1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_Rx(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_rotation(num, (1, 0, 0), np.pi / 2)
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), -1j / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_Ry(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_rotation(num, (0, 1, 0), np.pi / 2)
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_Rz(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        self.eng.apply_rotation(num, (0, 0, 1), np.pi / 2)
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), 1j / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_faulty_rot(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        with pytest.raises(NotImplementedError):
            self.eng.apply_rotation(num, (1, 0, 1), np.pi / 2)

    @enable_if_projectq
    def test_cnot(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_H(num1)
        self.eng.apply_CNOT(num1, num2)
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_cz(self):
        num1 = self.eng.add_fresh_qubit()
        num2 = self.eng.add_fresh_qubit()
        self.eng.apply_H(num1)
        self.eng.apply_H(num2)
        self.eng.apply_CPHASE(num1, num2)
        state = self.eng.get_register_RI()[1]
        ref = [1 / 2, 1 / 2, 1 / 2, -1 / 2]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_measure0(self):
        num = self.eng.add_fresh_qubit()
        m = self.eng.measure_qubit(num)
        assert m == 0
        assert self.eng.activeQubits == 0

    @enable_if_projectq
    def test_measure1(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_X(num)
        m = self.eng.measure_qubit(num)
        assert m == 1
        assert self.eng.activeQubits == 0

    @enable_if_projectq
    def test_measure_inplace(self):
        num = self.eng.add_fresh_qubit()
        m = self.eng.measure_qubit_inplace(num)
        assert m == 0
        assert self.eng.activeQubits == 1

    @enable_if_projectq
    def test_absorb_both_empty(self):
        eng2 = ProjectQEngine("Alice", 0)
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 0
        assert len(self.eng.qubitReg) == 0

    @enable_if_projectq
    def test_absorb_other_empty(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        eng2 = ProjectQEngine("Alice", 0)
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_absorb_this_empty_H(self):
        eng2 = ProjectQEngine("Alice", 0)
        num = eng2.add_fresh_qubit()
        eng2.apply_H(num)
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_absorb_this_empty_CNOT(self):
        eng2 = ProjectQEngine("Alice", 0)
        num1 = eng2.add_fresh_qubit()
        num2 = eng2.add_fresh_qubit()
        eng2.apply_H(num1)
        eng2.apply_CNOT(num1, num2)
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 2
        assert len(self.eng.qubitReg) == 2
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_absorb_this_empty_GHZ(self):
        n = 5
        eng2 = ProjectQEngine("Alice", 0)
        qubits = [eng2.add_fresh_qubit() for _ in range(n)]
        eng2.apply_H(qubits[0])
        for i in range(1, n):
            eng2.apply_CNOT(qubits[0], qubits[i])
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == n
        assert len(self.eng.qubitReg) == n
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2)] + [0] * (2 ** n - 2) + [1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_absorb_2GHZ(self):
        n = 5
        eng2 = ProjectQEngine("Alice", 0)
        for eng in [self.eng, eng2]:
            qubits = [eng.add_fresh_qubit() for _ in range(n)]
            eng.apply_H(qubits[0])
            for i in range(1, n):
                eng.apply_CNOT(qubits[0], qubits[i])
        self.eng.absorb(eng2)
        assert self.eng.activeQubits == 2 * n
        assert len(self.eng.qubitReg) == 2 * n

    @enable_if_projectq
    def test_absorb_to_big_this_empty(self):
        eng2 = ProjectQEngine("Alice", 0, 11)
        for _ in range(11):
            eng2.add_fresh_qubit()
        with pytest.raises(QuantumError):
            self.eng.absorb(eng2)

    @enable_if_projectq
    def test_absorb_to_big(self):
        self.eng.add_fresh_qubit()
        eng2 = ProjectQEngine("Alice", 0)
        for _ in range(10):
            eng2.add_fresh_qubit()
        with pytest.raises(QuantumError):
            self.eng.absorb(eng2)

    @enable_if_projectq
    def test_absorb_parts_both_empty(self):
        eng2 = ProjectQEngine("Alice", 0)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        assert self.eng.activeQubits == 0
        assert len(self.eng.qubitReg) == 0

    @enable_if_projectq
    def test_absorb_parts(self):
        self.eng.add_fresh_qubit()
        eng2 = ProjectQEngine("Alice", 0)
        eng2.add_fresh_qubit()
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        assert self.eng.activeQubits == 2
        assert len(self.eng.qubitReg) == 2
        state = self.eng.get_register_RI()[1]
        ref = [1, 0, 0, 0]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_absorb_parts_EPR(self):
        eng2 = ProjectQEngine("Alice", 0)
        num1 = eng2.add_fresh_qubit()
        num2 = eng2.add_fresh_qubit()
        eng2.apply_H(num1)
        eng2.apply_CNOT(num1, num2)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        assert self.eng.activeQubits == 2
        assert len(self.eng.qubitReg) == 2
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

    @enable_if_projectq
    def test_absorb_parts_other_empty(self):
        num = self.eng.add_fresh_qubit()
        self.eng.apply_H(num)
        eng2 = ProjectQEngine("Alice", 0)
        self.eng.absorb_parts(*eng2.get_register_RI(), eng2.activeQubits)
        assert self.eng.activeQubits == 1
        assert len(self.eng.qubitReg) == 1
        state = self.eng.get_register_RI()[1]
        ref = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        assert self._abs_inner_product(state, ref) == pytest.approx(1)

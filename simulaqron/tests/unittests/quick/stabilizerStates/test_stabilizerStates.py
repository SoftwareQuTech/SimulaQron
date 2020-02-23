import unittest
import numpy as np
import networkx as nx

from simulaqron.toolbox.stabilizerStates import StabilizerState


class TestStabilizerStates(unittest.TestCase):
    def test_faulty_init(self):
        with self.assertRaises(ValueError):
            StabilizerState([1])

        with self.assertRaises(ValueError):
            StabilizerState([[[1]]])

    def test_correct_init(self):

        state = StabilizerState([[0, 1]])
        self.assertAlmostEqual(state.num_qubits, 1)

        state = StabilizerState([[0, 1, 0]])
        self.assertAlmostEqual(state.num_qubits, 1)

        state = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
        self.assertAlmostEqual(state.num_qubits, 2)

        state = StabilizerState([[1, 1, 0, 0, 0], [0, 0, 1, 1, 1]])
        self.assertAlmostEqual(state.num_qubits, 2)

        self.assertTrue(state == StabilizerState(state))

    def test_symplectic_check(self):
        StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])

        with self.assertRaises(ValueError):
            StabilizerState([[1, 0, 0, 0], [0, 0, 1, 0]])

        with self.assertRaises(ValueError):
            StabilizerState([[1, 1, 0, 0], [0, 0, 1, 0]])

        with self.assertRaises(ValueError):
            StabilizerState([[1, 1, 1, 0, 0, 0], [0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 0, 0]])

    def test_networkx_init(self):
        n = 5
        G = nx.complete_graph(n)
        graph_state = StabilizerState(G)
        self.assertEqual(graph_state.num_qubits, n)

        # Create a star graph state and check that this is SQC equiv to the GHZ state
        G = nx.star_graph(n - 1)
        graph_state = StabilizerState(G)
        for i in range(1, n):
            graph_state.apply_H(i)

        GHZ_state = StabilizerState(n)
        GHZ_state.apply_H(0)
        for i in range(1, n):
            GHZ_state.apply_CNOT(0, i)

        self.assertTrue(graph_state == GHZ_state)

    def test_list_of_str_init(self):
        phip = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
        phim = StabilizerState([[1, 1, 0, 0, 0], [0, 0, 1, 1, 1]])

        data = ["XX", "ZZ"]
        s1 = StabilizerState(data)
        self.assertTrue(s1 == phip)

        data = ["+1XX", "+1ZZ"]
        s1 = StabilizerState(data)
        self.assertTrue(s1 == phip)

        data = ["+1XX", "-1ZZ"]
        s1 = StabilizerState(data)
        self.assertTrue(s1 == phim)

        # Test faulty input
        data = ["XX", "-2ZZ"]
        with self.assertRaises(ValueError):
            StabilizerState(data)

        data = ["XX", "ZZZ"]
        with self.assertRaises(ValueError):
            StabilizerState(data)

    def test_init_of_class(self):
        state = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])

        self.assertTrue(state == StabilizerState(state))

    def test_add_qubit(self):
        s = StabilizerState()
        self.assertEqual(s.num_qubits, 0)

        z0 = StabilizerState([[0, 1]])
        s.add_qubit()
        self.assertTrue(s == z0)

    def test_init_of_number_of_qubits(self):
        s = StabilizerState(1)
        z0 = StabilizerState([[0, 1]])
        self.assertEqual(s.num_qubits, 1)
        self.assertTrue(s == z0)

        s = StabilizerState(2)
        self.assertEqual(s.num_qubits, 2)
        self.assertTrue(s == z0.tensor_product(z0))

    def test_eq(self):
        state1 = StabilizerState([[0, 1]])
        state2 = StabilizerState([[0, 1]])
        state3 = StabilizerState([[0, 1, 0]])
        state4 = StabilizerState([[0, 1, 1]])
        state5 = StabilizerState([[1, 1, 0]])
        state6 = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])

        self.assertTrue(state1 == state1)
        self.assertTrue(state1 == state2)
        self.assertTrue(state1 == state3)
        self.assertFalse(state1 == state4)
        self.assertFalse(state1 == state5)
        self.assertFalse(state5 == state6)

    def test_repr(self):
        s1 = StabilizerState([[0, 0, 1, 0, 0], [0, 0, 0, 1, 1]])
        s2 = StabilizerState(eval(repr(s1)))

        self.assertTrue(s1 == s2)

    def test_to_array(self):
        s1 = StabilizerState([[0, 0, 1, 0, 0], [0, 0, 0, 1, 1]])
        s2 = StabilizerState(s1.to_array())

        self.assertTrue(s1 == s2)

    def test_tensor_product(self):
        s1 = StabilizerState([[0, 1]])  # The state |0>
        s2 = StabilizerState([[0, 1]])  # The state |0>

        s3 = s1 * s2  # This is then the state |00>
        s4 = StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]])
        self.assertEqual(s3.num_qubits, 2)
        self.assertTrue(s3 == s4)

        s1 = StabilizerState([[0, 1]])  # The state |0>
        s2 = StabilizerState([[0, 1, 1]])  # The state |1>

        s3 = s1 * s2  # This is then the state |01>
        s4 = StabilizerState([[0, 0, 1, 0, 0], [0, 0, 0, 1, 1]])
        self.assertEqual(s3.num_qubits, 2)
        self.assertTrue(s3 == s4)

    def test_Pauli_phase_tracking(self):
        S = StabilizerState()
        self.assertFalse(S.Pauli_phase_tracking([False, False], [False, False]))
        self.assertFalse(S.Pauli_phase_tracking([True, True], [True, True]))
        self.assertFalse(S.Pauli_phase_tracking([True, False], [True, False]))
        self.assertFalse(S.Pauli_phase_tracking([False, True], [False, True]))

        self.assertTrue(S.Pauli_phase_tracking([True, True], [True, False]))
        self.assertTrue(S.Pauli_phase_tracking([False, True], [True, True]))
        self.assertTrue(S.Pauli_phase_tracking([True, False], [False, True]))

        self.assertEqual(
            S.Pauli_phase_tracking([True, False], [True, True]), S.Pauli_phase_tracking([True, True], [False, True])
        )
        self.assertEqual(
            S.Pauli_phase_tracking([False, True], [True, False]), S.Pauli_phase_tracking([True, True], [False, True])
        )

    def test_gaussian_elimination(self):
        S = StabilizerState(["XZZ", "YIX", "IXX"])
        S.put_in_standard_form()
        self.assertTrue(np.array_equal(S.to_array(), StabilizerState(["+1XZZ", "-1ZYZ", "-1ZZY"]).to_array()))

    def test_apply_Pauli(self):
        s1 = StabilizerState([[0, 1]])
        s2 = StabilizerState([[0, 1, 1]])

        s1.apply_Z(0)
        self.assertFalse(s1 == s2)

        s1.apply_X(0)
        self.assertTrue(s1 == s2)

        s3 = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
        s4 = StabilizerState([[1, 1, 0, 0, 0], [0, 0, 1, 1, 1]])
        s3.apply_X(0)
        self.assertTrue(s3 == s4)

    def test_apply_H(self):
        s1 = StabilizerState([[0, 1]])
        s2 = StabilizerState([[1, 0]])
        s3 = StabilizerState([[0, 1]])
        s4 = StabilizerState([[1, 1]])
        s5 = StabilizerState([[1, 1, 1]])

        s1.apply_H(0)
        self.assertTrue(s1 == s2)

        s1.apply_H(0)
        self.assertTrue(s1 == s3)

        s4.apply_H(0)
        self.assertTrue(s4 == s5)

    def test_apply_K(self):
        z0 = StabilizerState([[0, 1]])
        x0 = StabilizerState([[1, 0]])
        x1 = StabilizerState([[1, 0, 1]])
        y0 = StabilizerState([[1, 1]])
        s1 = StabilizerState(z0)
        s2 = StabilizerState(x0)

        s1.apply_K(0)
        self.assertTrue(s1 == y0)

        s1.apply_K(0)
        self.assertTrue(s1 == z0)

        s2.apply_K(0)
        self.assertTrue(s2 == x1)

    def test_apply_S(self):
        z0 = StabilizerState([[0, 1]])
        x0 = StabilizerState([[1, 0]])
        x1 = StabilizerState([[1, 0, 1]])
        y0 = StabilizerState([[1, 1]])
        s1 = StabilizerState(z0)
        s2 = StabilizerState(x0)

        s1.apply_S(0)
        self.assertTrue(s1 == z0)

        s2.apply_S(0)
        self.assertTrue(s2 == y0)

        s2.apply_S(0)
        self.assertTrue(s2 == x1)

    def test_standard_form(self):
        s1 = StabilizerState([[1, 0, 0, 0], [0, 1, 0, 0]])
        s2 = StabilizerState([[1, 0, 0, 0], [1, 1, 0, 0]])
        s3 = StabilizerState([[1, 0, 0, 0, 1], [1, 1, 0, 0, 0]])
        s4 = StabilizerState([[1, 0, 0, 0, 1], [0, 1, 0, 0, 1]])

        self.assertTrue(s1 == s2)
        self.assertFalse(s1 == s3)
        self.assertTrue(s3 == s4)

    def test_apply_CNOT(self):

        # Classical CNOT
        z0z0 = StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]])
        z1z1 = StabilizerState([[0, 0, 1, 0, 1], [0, 0, 0, 1, 1]])
        z0z0.apply_X(0)
        z0z0.apply_CNOT(0, 1)
        self.assertTrue(z0z0 == z1z1)

        # EPR pair
        z0z0 = StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]])
        epr = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
        z0z0.apply_H(0)
        z0z0.apply_CNOT(0, 1)
        self.assertTrue(z0z0 == epr)

        # Graph state
        z0z0 = StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]])
        graph_state = StabilizerState([[1, 0, 0, 1], [0, 1, 1, 0]])
        z0z0.apply_H(0)
        z0z0.apply_H(1)
        # Effective CPHASE
        z0z0.apply_H(1)
        z0z0.apply_CNOT(0, 1)
        z0z0.apply_H(1)
        self.assertTrue(z0z0 == graph_state)

    def test_apply_CZ(self):

        # Classical CNOT
        z0x0 = StabilizerState([[0, 0, 1, 0], [0, 1, 0, 0]])
        z1x1 = StabilizerState([[0, 0, 1, 0, 1], [0, 1, 0, 0, 1]])
        z0x0.apply_X(0)
        z0x0.apply_CZ(0, 1)
        z0x0.put_in_standard_form()
        self.assertTrue(z0x0 == z1x1)

        # EPR pair
        z0z0 = StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]])
        epr = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
        z0z0.apply_H(0)
        # Effective CNOT
        z0z0.apply_H(1)
        z0z0.apply_CZ(0, 1)
        z0z0.apply_H(1)
        self.assertTrue(z0z0 == epr)

        # Graph state
        z0z0 = StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]])
        graph_state = StabilizerState([[1, 0, 0, 1], [0, 1, 1, 0]])
        z0z0.apply_H(0)
        z0z0.apply_H(1)
        # Effective CPHASE
        z0z0.apply_CZ(0, 1)
        self.assertTrue(z0z0 == graph_state)

    def test_measure(self):
        for _ in range(20):
            z0 = StabilizerState([[0, 1]])
            m = z0.measure(0)
            self.assertEqual(m, 0)

        for _ in range(20):
            z1 = StabilizerState([[0, 1, 1]])
            m = z1.measure(0)
            self.assertEqual(m, 1)

        z0z0 = StabilizerState([[0, 0, 1, 0], [0, 0, 0, 1]])
        z1z1 = StabilizerState([[0, 0, 1, 0, 1], [0, 0, 0, 1, 1]])
        for _ in range(20):
            epr = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
            m0 = epr.measure(0, inplace=True)
            m1 = epr.measure(1, inplace=True)
            self.assertEqual(m0, m1)
            if m0 == 0:
                self.assertTrue(epr == z0z0)
            else:
                self.assertTrue(epr == z1z1)

        outcomes = []
        for _ in range(200):
            x0 = StabilizerState([[1, 0]])
            outcomes.append(x0.measure(0))
        self.assertTrue(80 <= sum(outcomes) <= 120)

    def test_GHZ(self):
        n = 5
        for _ in range(20):
            GHZ = StabilizerState(n)
            GHZ.apply_H(0)
            for i in range(1, n):
                GHZ.apply_CNOT(0, i)
            outcomes = [GHZ.measure(0) for _ in range(n)]
            self.assertNotIn(False, [outcomes[0] == outcomes[i] for i in range(1, n)])

    def test_going_to_graph(self):
        one_Bell_pair = StabilizerState(["-1XX", "+1ZZ"])
        G = nx.Graph()
        G.add_edge(0, 1)
        one_Bell_pair_graph = one_Bell_pair.find_SQC_equiv_graph_state()
        self.assertTrue(G, one_Bell_pair_graph)

        two_EPR_pairs = StabilizerState(
            [[1, 0, 0, 1, 0, 0, 0, 0], [0, 1, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 1], [0, 0, 0, 0, 0, 1, 1, 0]]
        )
        G.remove_edge(0, 1)
        G.add_edges_from([(0, 3), (1, 2)])
        two_EPR_pairs_graph = two_EPR_pairs.find_SQC_equiv_graph_state()
        self.assertTrue(G, two_EPR_pairs_graph)

        n = 5
        GHZ = StabilizerState(n)
        GHZ.apply_H(0)
        for i in range(1, n):
            GHZ.apply_CNOT(0, i)
        GHZ_graph, operations = GHZ.find_SQC_equiv_graph_state(return_operations=True)
        self.assertTrue(GHZ_graph, nx.star_graph(n - 1))
        self.assertTrue(operations == [("H", i) for i in range(1, n)])

    def test_contains(self):
        tests = [  # stabilizer, expected
            ("XX", True),
            ("+1XX", True),
            ("-1XX", False),
            ("+1YY", False),
            ("-1YY", True),
            ("+1YI", False),
            ("IY", False),
        ]

        for stabilizer, expected in tests:
            with self.subTest(stabilizer=stabilizer, expected=expected):
                s = StabilizerState(["XX", "ZZ"])
                output = s.contains(stabilizer)
                self.assertEqual(output, expected)

    def test_measure_eigenstate(self):
        tests = [  # stabilizers, qubit, expected
            (["ZI", "IZ"], 0, 0),
            (["-1ZI", "IZ"], 0, 1),
            (["ZI", "ZZ"], 0, 0),
            (["IZ", "-1ZZ"], 0, 1),
            (["IZ", "-1ZI"], 0, 1),
            (["+1XIIII", "+1IXIII", "+1IIXII", "-1IIIZI", "+1IIIZZ"], 4, 1),
        ]

        for stabilizers, qubit, expected in tests:
            with self.subTest(stabilizers=stabilizers, qubit=qubit, expected=expected):
                s = StabilizerState(stabilizers)
                output = s.measure(qubit)
                self.assertEqual(output, expected)

    def test_correlations(self):
        tests = [  # stabilizers
            ["ZI", "IZ"],
            ["ZZ", "XX"],
            ["ZX", "XZ"],
            ["XXX", "ZZI", "IZZ"],
            ["XIII", "IXII", "IIXI", "IIIX"],
            ["XZII", "ZXZI", "IZXZ", "IIZX"],  # line graph
            ["XZIZ", "ZXZI", "IZXZ", "ZIZX"],  # cycle graph
            ["XZZZ", "ZXZZ", "ZZXZ", "ZZZX"],  # complete graph
            ["XZZZ", "ZXII", "ZIXI", "ZIIX"],  # star graph
        ]

        for stabilizers in tests:
            for stabilizer in stabilizers:
                for _ in range(10):
                    with self.subTest(stabilizers=stabilizers, stabilizer=stabilizer):
                        s = StabilizerState(stabilizers)
                        outcomes = []
                        qubit = 0
                        for pauli in stabilizer:
                            if pauli == 'X':
                                s.apply_H(qubit)
                            elif pauli == 'Y':
                                s.apply_K(qubit)
                            elif pauli == 'Z':
                                pass
                            else:
                                qubit += 1
                                continue
                            outcomes.append(s.measure(qubit))
                        self.assertEqual(sum(outcomes) % 2, 0)

    def test_standard_form(self):
        tests = [  # stabilizers
            ["ZI", "IZ"],
            ["ZZ", "XX"],
            ["ZX", "XZ"],
            ["XXX", "ZZI", "IZZ"],
            ["XIII", "IXII", "IIXI", "IIIX"],
            ["XZII", "ZXZI", "IZXZ", "IIZX"],  # line graph
            ["XZIZ", "ZXZI", "IZXZ", "ZIZX"],  # cycle graph
            ["XZZZ", "ZXZZ", "ZZXZ", "ZZZX"],  # complete graph
            ["XZZZ", "ZXII", "ZIXI", "ZIIX"],  # star graph
        ]

        for stabilizers in tests:
            with self.subTest(stabilizers=stabilizers):
                state = StabilizerState(stabilizers)
                state.put_in_standard_form()
                # Check that there are no X or Y in the first column except the first row
                for row in state._group[1:, :]:
                    self.assertFalse(row[0])

    def test_reduce_when_measuring(self):
        tests = [  # stabilizers
            ["ZI", "IZ"],
            ["ZZ", "XX"],
            ["ZX", "XZ"],
            ["XXX", "ZZI", "IZZ"],
            ["XIII", "IXII", "IIXI", "IIIX"],
            ["XZII", "ZXZI", "IZXZ", "IIZX"],  # line graph
            ["XZIZ", "ZXZI", "IZXZ", "ZIZX"],  # cycle graph
            ["XZZZ", "ZXZZ", "ZZXZ", "ZZZX"],  # complete graph
            ["XZZZ", "ZXII", "ZIXI", "ZIIX"],  # star graph
        ]

        for stabilizers in tests:
            with self.subTest(stabilizers=stabilizers):
                state = StabilizerState(stabilizers)
                n = len(state)
                for i in range(n):
                    state.measure(0)
                    self.assertEqual(len(state), n - i - 1)
        

if __name__ == "__main__":
    unittest.main()

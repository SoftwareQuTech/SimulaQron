##########################################################################################
#
# This file contains classes for describing stabilizer states and manipulating these using
# Clifford operations and Pauli-measurements etc.
#
# Author: Axel Dahlberg
#
##########################################################################################

import numpy as np
import networkx as nx
from scipy.linalg import block_diag
from random import randint


class StabilizerState:
    bool2phase = {False: "+1", True: "-1"}

    bool2Pauli = {(False, False): "I", (True, False): "X", (True, True): "Y", (False, True): "Z"}

    phase2bool = {"+1": False, "-1": True}

    Pauli2bool = {"I": (False, False), "X": (True, False), "Y": (True, True), "Z": (False, True)}

    def __init__(self, data=None, check_symplectic=True):
        """
        This class represent a stabilizer state and allows to be manipulated using
        Clifford operations and Pauli-measurements.

        If check_symplectic=True then a check will be made that all stabilizers commute, by checking
        That the matrix is symplectic. Otherwise no check is made.

        :param data:
            Can be one of the following:

            A binary array of rank 2:
                A binary array representing the generators of the stabilizer group.
                If the array is n-by-2n a stabilizer state on n qubits will be represented.
                The n first columns are the X-stabilizers and the n last the Z-stabilizer.
                If the array is n-by-(2n+1), the last column is seen as the phase for each generator
                as follows:
                    0 -> 1
                    1 -> -1

            An array of rank 1 containing 'str':
                Then each string is assumed to be a generator as for example "XXZIY"
                Note that each string in the array should have the same length.
                If the number of strings is 'n' then a stabilizer state on 'n' qubits is created.
                If the strings have length 'n' then it is assumed that the phase is '+1'.
                An explicit phase can be added to the start of the string as for example: "-1XXXY".
                Creating a Bell-pair:
                    StabilizerState(["XX", "ZZ"])  # The state (|00> + |11>) / sqrt(2)

            'None' (default):
                Then this is seen as a stabilizer state on no qubits, i.e. a complex number.
                To add a qubit to such a state one can do:
                    s = StabilizerState()
                    s.add_qubit()  # This is now in the state |0>

            'int':
                Then a stabilizer state on this many qubits are created, all in the state |0> as:
                    StabilizerState(5)  # This is the then the state |00000>

            'networkx.Graph':
                Then the graph state corresponding to this graph will be created.
                This assumes that the nodes are numbered from 0 to n - 1, where n is the number of nodes.
                For example:
                    StabilizerState(networkx.complete_graph(5))  # Single qubit Clifford equiv. to a GHZ state

        Examples:
        A qubit in the state |0> can be created as:
            StabilizerState([[0, 1]])

        A qubit in the state |1> can be created as:
            StabilizerState([[0, 1, 1]])

        The entangled state (|00> + |11>)/sqrt(2) can be created as:
            StabilizerState([[1, 1, 0, 0],
                              0, 0, 1, 1]])

        The entangled state (|01> + |10>)/sqrt(2) can be created as:
            StabilizerState([[1, 1, 0, 0, 0],
                              0, 0, 1, 1, 1]])
        :param check_symplectic: bool
            Whether to check if all stabilizers commute or not.
        """
        if data is None:
            self._group = np.empty(shape=(0, 0), dtype=bool)
            self._nr_rows = 0
            self._nr_cols = 0
        elif isinstance(data, int):
            X_part = np.zeros(shape=(data, data), dtype=bool)
            Z_part = np.identity(data, dtype=bool)
            phases = np.zeros(shape=(data, 1), dtype=bool)
            self._group = np.concatenate((X_part, Z_part, phases), 1)
            self._nr_rows = data
            self._nr_cols = 2 * data + 1
        elif isinstance(data, StabilizerState):
            self._group = np.array(data._group, dtype=bool)
            self._nr_rows = data._nr_rows
            self._nr_cols = data._nr_cols
        elif isinstance(data, nx.Graph):
            n = data.number_of_nodes()
            adj_matrix = nx.adjacency_matrix(data)
            X_part = np.identity(n, dtype=bool)
            Z_part = np.array(adj_matrix.todense(), dtype=bool)
            phases = [[False]] * n
            self._group = np.concatenate((X_part, Z_part, phases), 1)
            self._nr_rows = n
            self._nr_cols = 2 * n + 1
        else:
            if len(data) == 0:
                self._group = np.empty(shape=(0, 0), dtype=bool)
                self._nr_rows = 0
                self._nr_cols = 0
                return
            else:
                if isinstance(data[0], str):
                    # We should pre-process this entry since it contains strings and not booleans
                    n = len(data)
                    if all(map(lambda gen_str: len(gen_str) == n, data)):
                        X_part = list(map(lambda gen_str: list(map(lambda P_str: P_str in ("X", "Y"), gen_str)), data))
                        Z_part = list(map(lambda gen_str: list(map(lambda P_str: P_str in ("Y", "Z"), gen_str)), data))
                        data = np.concatenate((X_part, Z_part), 1)
                    elif all(map(lambda gen_str: len(gen_str) == (n + 2), data)):
                        X_part = list(
                            map(lambda gen_str: list(map(lambda P_str: P_str in ("X", "Y"), gen_str[2:])), data)
                        )
                        Z_part = list(
                            map(lambda gen_str: list(map(lambda P_str: P_str in ("Y", "Z"), gen_str[2:])), data)
                        )
                        phases = list(map(lambda gen_str: [self.phase2bool[gen_str[:2]]], data))
                        data = np.concatenate((X_part, Z_part, phases), 1)
                    else:
                        raise ValueError(
                            "If data is a length-'n' list or stings, then each string needs be of length 'n' or 'n+2'"
                        )
                try:
                    self._group = np.array(data, dtype=bool)
                except Exception as err:
                    raise ValueError(
                        "Could not create an array of the 'data' due to the following error: {}".format(err)
                    )

                if len(self._group.shape) != 2:
                    raise ValueError("'data' needs to be an array of rank 2")
                else:
                    self._nr_rows, self._nr_cols = self._group.shape

                    if 2 * self._nr_rows == self._nr_cols:
                        if self._nr_rows != 0:
                            self._group = np.append(self._group, [[False]] * self._nr_rows, 1)
                    elif (2 * self._nr_rows + 1) == self._nr_cols:
                        pass
                    else:
                        raise ValueError("'data' needs to be an array of dimension n x 2n or n x (2n +1)")
                if check_symplectic:
                    # Check that all stabilizers commute, i.e. the matrix should be symplectic
                    n = self._nr_rows
                    zeros = np.zeros(shape=(n, n), dtype=int)
                    identity = np.identity(n, dtype=int)
                    P = np.block([[zeros, identity], [identity, zeros]])
                    M = np.array(self._group[:, :-1], dtype=int)

                    commute = M @ P @ M.transpose()
                    if (commute % 2).any():
                        raise ValueError("All stabilizer of the group constructed from the input does not commute.")

    @property
    def num_qubits(self):
        return self._nr_rows

    def __eq__(self, other):
        if not isinstance(other, StabilizerState):
            raise ValueError("Can only compare with other StabilizerState")
        else:
            if self.num_qubits != other.num_qubits:
                return False
            else:
                # Get the standard forms of the groups
                this_group = self.boolean_gaussian_elimination(self._group)
                other_group = self.boolean_gaussian_elimination(other._group)
                return np.all(this_group == other_group)

    def __mul__(self, other):
        return self.tensor_product(other)

    def __repr__(self):
        return "StabilizerState(np." + self._group.__repr__() + ")"

    def __str__(self):
        to_return = "Stabilizer state on {} with the following stabilizer generators:\n".format(self.num_qubits)
        for row in self._group:
            to_return += "    {} ".format(self.bool2phase[row[-1]])
            n = self.num_qubits
            for i in range(n):
                to_return += self.bool2Pauli[(row[i], row[i + n])]
            to_return += "\n"
        return to_return

    def __len__(self):
        return self.num_qubits

    @staticmethod
    def Pauli_phase_tracking(old_pauli, applied_pauli):
        if old_pauli == [True, False] and applied_pauli == [True, True]:
            added_phase = 3
        elif old_pauli == [True, True] and applied_pauli == [False, True]:
            added_phase = 3
        elif old_pauli == [False, True] and applied_pauli == [True, False]:
            added_phase = 3
        elif old_pauli == [True, True] and applied_pauli == [True, False]:
            added_phase = 1
        elif old_pauli == [False, True] and applied_pauli == [True, True]:
            added_phase = 1
        elif old_pauli == [True, False] and applied_pauli == [False, True]:
            added_phase = 1
        else:
            added_phase = 0
        return added_phase

    @staticmethod
    def boolean_gaussian_elimination(matrix, return_pivot_columns=False):
        """
        Given a boolean matrix returns the matrix in row reduced echelon form
        where entries are seen as elements of GF(2), i.e. intergers modulus 2.
        :param matrix: The boolean matrix
        :type matrix: :obj:`numpy.array`
        :return:
        :rtype: :obj:`numpy.array`
        """
        try:
            new_matrix = np.array(matrix, dtype=bool)
        except Exception as err:
            raise ValueError("Could not create an array of the 'data' due to the following error: {}".format(err))

        if len(new_matrix.shape) != 2:
            raise ValueError("'data' needs to be an array of rank 2")
        else:
            m, n = new_matrix.shape

        h = 0
        k = 0
        pivot_columns = []
        while (h < m) and (k < n):
            non_zero_ind = new_matrix[:, k].nonzero()[0]
            non_zero_ind_under_h = non_zero_ind[non_zero_ind >= h]
            if len(non_zero_ind_under_h) == 0:
                # No nonzero elements in this column
                k += 1
            else:
                i_max = non_zero_ind_under_h[0]
                if i_max != h:
                    new_matrix[[h, i_max]] = new_matrix[[i_max, h]]
                # Add pivot row to the rest
                pivot_columns.append(k)
                non_zero_except_i_max = non_zero_ind[non_zero_ind != i_max]

                for i_loop in non_zero_except_i_max:
                    extra_phase = 0  # we count i's here, so 2 -> (-i)^2=-1, 4->1, 6-> -1
                    for j in range(m):
                        extra_phase += StabilizerState.Pauli_phase_tracking(
                            [new_matrix[i_loop, j], new_matrix[i_loop, j + m]], [new_matrix[h, j], new_matrix[h, j + m]]
                        )
                    new_matrix[i_loop, :] = np.logical_xor(new_matrix[i_loop, :], new_matrix[h, :])
                    if (extra_phase / 2) % 2:
                        new_matrix[i_loop, -1] = np.logical_not(new_matrix[i_loop, -1])
                h += 1
                k += 1
        if return_pivot_columns:
            return new_matrix, pivot_columns
        else:
            return new_matrix

    def check_symplectic(self):
        n = self._nr_rows
        zeros = np.zeros(shape=(n, n), dtype=int)
        identity = np.identity(n, dtype=int)
        P = np.block([[zeros, identity], [identity, zeros]])
        M = np.array(self._group[:, :-1], dtype=int)

        commute = M @ P @ M.transpose()
        if (commute % 2).any():
            # All stabilizer of the group constructed from the input does not commute
            return False
        else:
            return True

    def add_qubit(self):
        """
        Appends a qubit in the state \|0\> to the current state
        :return: None
        """
        z0 = StabilizerState([[0, 1]])
        self.__init__(self.tensor_product(z0))

    def put_in_standard_form(self):
        """
        Puts the generators of the stabilizer group in standard form by performing Gaussiand elemination
        :return: None
        """
        self._group = self.boolean_gaussian_elimination(self._group)

    def tensor_product(self, other):
        r"""
        Performs the tensor product with another StabilizerState and returns a new
        StabilizerState.

        This can also be done using '*' as for example:

            s1 = StabilizerState([[0, 1]])  # The state \|0\>
            s2 = StabilizerState([[0, 1]])  # The state \|0\>

            s3 = s1 * s2  # This is then the state \|00\>

        :param other: The other StabilizerState to perform the tensor product with
        :type other: :obj:`StabilizerState`
        :return: The tensor product of self and other
        :rtype: :obj:`StabilizerState`
        """
        if not isinstance(other, StabilizerState):
            raise ValueError("Can only perform tensor product with other StabilizerState")
        if self.num_qubits == 0:
            return StabilizerState(other)
        elif other.num_qubits == 0:
            return self
        else:
            this_X_stab = self._group[:, : self.num_qubits]
            this_Z_stab = self._group[:, self.num_qubits : -1]
            other_X_stab = other._group[:, : other.num_qubits]
            other_Z_stab = other._group[:, other.num_qubits : -1]

            new_X_stab = block_diag(this_X_stab, other_X_stab)
            new_Z_stab = block_diag(this_Z_stab, other_Z_stab)

            phases = np.append(self._group[:, -1:], other._group[:, -1:], 0)
            new_group = np.concatenate((new_X_stab, new_Z_stab, phases), 1)
            return StabilizerState(new_group)

    def to_array(self, standard_form=False, return_pivot_columns=False):
        """
        Returns the numpy array representing the stabilizer group of this state.
        See doc-string for __init__ how the elements of this numpy array are treated.
        Since, the __init__ takes an array as input, given a StabilizerState 's1' on can do:

            s2 = StabilizerState(to_array(s1))

        and 's1' and 's2' will represent the same state.

        :return: The generators of this stabilizer group as a numpy array
        :rtype: :obj:`numpy.array`
        """

        if standard_form:
            if return_pivot_columns:
                return self.boolean_gaussian_elimination(self._group, True)
            else:
                return self.boolean_gaussian_elimination(self._group)
        else:
            return np.array(self._group, dtype=bool)

    def apply_X(self, position):
        """
        Applies the Pauli X operator to qubit 'position' of the stabilizer state and updates the generators.
        :param position: The position of the qubit.
        :type position: int
        :return: None
        """
        n = self.num_qubits
        if not (position >= 0 and position < n):
            raise ValueError("position= {} if not a valid qubit position (i.e. in [0, {}]".format(position, n))
        yz_rows = self._group[:, position + n]

        # Flip phases for Y and Z rows
        self._group[yz_rows, -1] = np.logical_not(self._group[yz_rows, -1])

    def apply_Y(self, position):
        """
        Applies the Pauli Y operator to qubit 'position' of the stabilizer state and updates the generators.
        :param position: The position of the qubit.
        :type position: int
        :return: None
        """
        n = self.num_qubits
        if not (position >= 0 and position < n):
            raise ValueError("position= {} if not a valid qubit position (i.e. in [0, {}]".format(position, n))
        xz_rows = np.logical_xor(self._group[:, position], self._group[:, position + n])

        # Flip phases for X and Z rows
        self._group[xz_rows, -1] = np.logical_not(self._group[xz_rows, -1])

    def apply_Z(self, position):
        """
        Applies the Pauli Z operator to qubit 'position' of the stabilizer state and updates the generators.
        :param position: The position of the qubit.
        :type position: int
        :return: None
        """
        n = self.num_qubits
        if not (position >= 0 and position < n):
            raise ValueError("position= {} if not a valid qubit position (i.e. in [0, {}]".format(position, n))
        xy_rows = self._group[:, position]

        # Flip phases for X and Y rows
        self._group[xy_rows, -1] = np.logical_not(self._group[xy_rows, -1])

    def apply_H(self, position):
        """
        Applies the H operator to qubit 'position' of the stabilizer state and updates the generators.
        :param position: The position of the qubit.
        :type position: int
        :return: None
        """
        n = self.num_qubits
        if not (position >= 0 and position < n):
            raise ValueError("position= {} if not a valid qubit position (i.e. in [0, {}]".format(position, n))
        # Swap the Z and X columns
        self._group[:, [position, position + n]] = self._group[:, [position + n, position]]

        # Update the phases
        y_rows = np.logical_and(self._group[:, position], self._group[:, position + n])
        self._group[y_rows, -1] = np.logical_not(self._group[y_rows, -1])

    def apply_K(self, position):
        """
        Applies the K operator to qubit 'position' of the stabilizer state and updates the generators.
        :param position: The position of the qubit.
        :type position: int
        :return: None
        """
        n = self.num_qubits
        if not (position >= 0 and position < n):
            raise ValueError("position= {} if not a valid qubit position (i.e. in [0, {}]".format(position, n))
        # Perform effective CNOT from Z column to X column
        yz_rows = self._group[:, position + n]
        self._group[yz_rows, position] = np.logical_not(self._group[yz_rows, position])

        # Update the phases
        x_rows = np.logical_and(self._group[:, position], np.logical_not(self._group[:, position + n]))
        self._group[x_rows, -1] = np.logical_not(self._group[x_rows, -1])

    def apply_S(self, position):
        """
        Applies the S operator to qubit 'position' of the stabilizer state and updates the generators.
        :param position: The position of the qubit.
        :type position: int
        :return: None
        """
        n = self.num_qubits
        if not (position >= 0 and position < n):
            raise ValueError("position= {} if not a valid qubit position (i.e. in [0, {}]".format(position, n))
        # Perform effective CNOT from X column to Z column
        xy_rows = self._group[:, position]
        self._group[xy_rows, position + n] = np.logical_not(self._group[xy_rows, position + n])
        # Update the phases
        x_rows = np.logical_and(self._group[:, position], np.logical_not(self._group[:, position + n]))
        self._group[x_rows, -1] = np.logical_not(self._group[x_rows, -1])

    def apply_sqrt_minIX(self, position):
        self.apply_K(position)
        self.apply_Z(position)

    def apply_sqrt_IZ(self, position):
        self.apply_Z(position)
        self.apply_S(position)

    def apply_CNOT(self, control, target):
        """
        Applies CNOT using qubit 'control' as control and 'target' as target.
        :param control: The control qubit
        :type control: int
        :param target: The target qubit
        :type control: int
        :return: None
        """
        n = self.num_qubits
        if not (control >= 0 and control < n):
            raise ValueError("control= {} if not a valid qubit position (i.e. in [0, {}]".format(control, n))
        if not (target >= 0 and target < n):
            raise ValueError("target= {} if not a valid qubit position (i.e. in [0, {}]".format(target, n))
        if control == target:
            raise ValueError("Control and target qubits cannot be the same")

        # Perform effective CNOT from the control X column to target X column
        xy_control_rows = self._group[:, control]
        self._group[xy_control_rows, target] = np.logical_not(self._group[xy_control_rows, target])

        # Perform effective CNOT from the target Z column to control Z column
        yz_target_rows = self._group[:, target + n]
        self._group[yz_target_rows, control + n] = np.logical_not(self._group[yz_target_rows, control + n])

        # Update the phases
        xy_control_yz_target_rows = np.logical_and(self._group[:, control], self._group[:, target + n])
        yz_control_xy_target_rows = np.logical_and(self._group[:, control + n], self._group[:, target])
        not_yz_control_not_xy_target_rows = np.logical_and(
            np.logical_not(self._group[:, control + n]), np.logical_not(self._group[:, target])
        )
        rows_to_flip = np.logical_and(
            xy_control_yz_target_rows, np.logical_or(yz_control_xy_target_rows, not_yz_control_not_xy_target_rows)
        )
        self._group[rows_to_flip, -1] = np.logical_not(self._group[rows_to_flip, -1])

    def apply_CZ(self, control, target):
        """
        Applies CZ using qubit 'control' as control and 'target' as target.
        :param control: The control qubit
        :type control: int
        :param target: The target qubit
        :type control: int
        :return: None
        """
        n = self.num_qubits
        if not (control >= 0 and control < n):
            raise ValueError("control= {} if not a valid qubit position (i.e. in [0, {}]".format(control, n))
        if not (target >= 0 and target < n):
            raise ValueError("target= {} if not a valid qubit position (i.e. in [0, {}]".format(target, n))
        if control == target:
            raise ValueError("Control and target qubits cannot be the same")

        # Update the phases
        x_and_y_rows = np.logical_and(self._group[:, control], self._group[:, target])
        z_rows = np.logical_xor(self._group[:, control + n], self._group[:, target + n])
        rows_to_flip = np.logical_and(x_and_y_rows, z_rows)
        self._group[rows_to_flip, -1] = np.logical_not(self._group[rows_to_flip, -1])

        # Perform effective CNOT from the control X column to target Z column
        xy_control_rows = self._group[:, control]
        self._group[xy_control_rows, target + n] = np.logical_not(self._group[xy_control_rows, target + n])

        # Perform effective CNOT from the target X column to control Z column
        xy_target_rows = self._group[:, target]
        self._group[xy_target_rows, control + n] = np.logical_not(self._group[xy_target_rows, control + n])

    def measure(self, position, inplace=False):
        """
        Measures qubit 'position' of the stabilizer state in the standard basis.
        If 'inplace=False' the qubit is removed from the state, i.e. the number of qubits in the state is reduced by one
        If 'inplace=True' the qubit is not removed and the number of qubits remain the same.
        :param position: The position of the qubit.
        :type position: int
        :param inplace: Whether to measure the qubit in place or not. (I.e. to keep it or not)
        :type inplace: bool
        :return: The measurement outcome (0 or 1, where 0 is the +1 eigenvalue and 1 is the -1)
        :rtype: int
        """
        n = self.num_qubits
        if not (position >= 0 and position < n):
            raise ValueError("position= {} if not a valid qubit position (i.e. in [0, {}]".format(position, n))

        tmp_matrix = self._group
        # Create a new matrix where the X and Z columns of the corresponding qubit are the first.
        perm = [position] + [i for i in range(n) if i != position]
        perm.extend([i + n for i in perm])
        perm.append(2 * n)
        tmp_matrix = tmp_matrix[:, perm]
        # Perform Gaussian elimination such that there is maximally one X or Y at the qubit position
        tmp_matrix = self.boolean_gaussian_elimination(tmp_matrix)

        # Check if there is an X or a Y at the qubit position
        if tmp_matrix[0, 0]:
            # The first row (generator) of this matrix is then the only one that doesn't commute with the observabel Z
            outcome = randint(0, 1)
            # If outcome is 1 we need to flip phases for the other generators that has an Z at this qubit
            if outcome == 1:
                z_rows = tmp_matrix[:, n]
                tmp_matrix[z_rows, -1] = np.logical_not(tmp_matrix[z_rows, -1])
            if not inplace:
                # Simply remove first generator and columns for X and Z of this qubit
                X_part = tmp_matrix[1:n, 1:n]
                Z_part_and_phase = tmp_matrix[1:n, n + 1 :]
                self._group = np.concatenate((X_part, Z_part_and_phase), 1)
                self._nr_rows = n - 1
            else:
                # Set first generator to be the observable
                tmp_matrix[0, :] = False
                tmp_matrix[0, n] = True
                if outcome == 1:
                    tmp_matrix[0, -1] = not tmp_matrix[0, -1]
                # Set the rest of the first column to be identity
                tmp_matrix[1:, n] = False
                # Swap back the X and Z columns of this qubit
                self._group = tmp_matrix[:, np.argsort(perm)]
        else:
            # Thus means that all stabilizer elements commute with the observable
            # and therefore that the qubit is already in |0> or |1>
            if not tmp_matrix[0, -1]:
                # Qubit is in |0>
                outcome = 0
            else:
                # Qubit is in |1>
                outcome = 1
            if not inplace:
                tmp_matrix = tmp_matrix[:, np.argsort(perm)]
                columns = np.arange(2 * n + 1)
                columns_without_position = np.logical_and(columns != position, columns != (position + n))
                tmp_matrix = tmp_matrix[np.logical_not(tmp_matrix[:, n + position]), :]
                self._group = tmp_matrix[:, columns_without_position]
                self._nr_rows = n - 1
            else:
                # We don't need to do anything here since the state has not changed
                self._group = tmp_matrix[:, np.argsort(perm)]
                pass
        return outcome

    def find_SQC_equiv_graph_state(self, return_operations=False):
        """
        Finds a graph state single qubit Clifford equivalent to self. Method is described
        in quant-ph/0308151.

        For example:
            EPR_pair = [[1,1,0,0],[0,0,1,1]]
            S = StabilizerState(EPR_pair)
            G = find_SQC_equiv_graph_state(S)

        :param self: The StabilizerState for which we want to find the corresponding graph state
        :type self: :obj:`StabilizerState`
        :return: A networkx graph SQC equivalent to S
        :rtype: :obj:`networkx.classes.graph.Graph`
        """
        S_ech_form, pivs = self.to_array(standard_form=True, return_pivot_columns=True)
        n = len(pivs)
        pivsX = [i for i in pivs if i < n]
        k = len(pivsX)
        operations = []

        # Next step is to relabel the qubits such that the pivot columns in X
        # are the first k columns in X-part and the Z-part.
        A = pivsX + [i for i in range(n) if i not in pivsX]
        A.extend([sum(x) for x in zip(A, n * [n])] + [2 * n])
        Sp = StabilizerState(S_ech_form[:, A])

        # Then apply Hadamards on the last n-k qubits such that X has full rank
        for j in range(k, n):
            Sp.apply_H(j)
            operations.append(("H", A[j]))
        Sp_mat = Sp.to_array().astype(int)[:, : 2 * n]
        phase_list = Sp.to_array()[:, -1]

        # Then multiply by inv(X) such that inv(X)X = I
        Spp_mat = np.matmul(np.linalg.inv(Sp_mat[:, :n]), Sp_mat)

        # Test if this was succesfull
        if not np.array_equal(Spp_mat[:, :n], np.identity(n)):
            raise ValueError("The X-part should be identity,but something went wrong")

        # then swap back (first the columns, then the rows to keep identity on the X-part)
        Spp_mat = Spp_mat[:, A[: 2 * n]]
        Spp_mat = Spp_mat[A[:n], :]
        Spp = StabilizerState(np.c_[Spp_mat, [phase_list[i] for i in A[:n]]])

        # Spp is now a graph state with possible self loops. To remove these,
        # do an S on every qubit with a self loop
        for j in range(n):
            if Spp_mat[j, j + n]:
                Spp.apply_S(j)
                operations.append(("S", j))

        # Now we remove -1 phases which might still be there
        for j in range(n):
            if Spp.to_array()[:, -1][j]:
                Spp.apply_Z(j)
                operations.append(("Z", j))
        # Spp is now in the form of (I,Gamma) where Gamma is the adj mat of the Graph
        # SQC equivalent to the stabilizer state.
        adj_mat = Spp.to_array()[:, n : 2 * n]
        G = nx.from_numpy_matrix(adj_mat)

        if return_operations:
            return G, operations
        else:
            return G

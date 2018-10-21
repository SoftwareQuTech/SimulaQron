##########################################################################################
#
# This file contains classes for describing stabilizer states and manipulating these using
# Clifford operations and Pauli-measurements etc.
#
# Author: Axel Dahlberg
#
##########################################################################################

import numpy as np
from scipy.linalg import block_diag
from random import randint


class StabilizerState:
    bool2phase = {(False, False): "+1",
                  (False, True): "-1",
                  (True, False): "+i",
                  (True, True): "-i"}

    bool2Pauli = {(False, False): "I",
                  (True, False): "X",
                  (True, True): "Y",
                  (False, True): "Z"}

    def __init__(self, data=None):
        """
        This class represent a stabilizer state and allows to be manipulated using
        Clifford operations and Pauli-measurements.
        :param data: A binary array representing the generators of the stabilizer group.
            If the array is n-by-2n a stabilizer state on n qubits will be represented.
            The n first columns are the X-stabilizers and the n last the Z-stabilizer.
            If the array is n-by-(2n+2), the two last columns are seen as the phase for each generator
            as follows:
                00 -> 1
                01 -> -1
                10 -> i
                11 -> -i

            If 'data=None' (default) then this is seen as a stabilizer state on no qubits, i.e. a complex number.
            To add a qubit to such a state one can do:
                s = StabilizerState()
                s.add_qubit()  # This is now in the state |0>

            If 'data' is an 'int' then a stabilizer state on this many qubits are created, all in the state |0> as:
                StabilizerState(5)  # This is the then the state |00000>

        Examples:
        A qubit in the state |0> can be created as:
            StabilizerState([[0, 1]])

        A qubit in the state |1> can be created as:
            StabilizerState([[0, 1, 0, 1]])

        The entangled state (|00> + |11>)/sqrt(2) can be created as:
            StabilizerState([[1, 1, 0, 0],
                              0, 0, 1, 1]])

        The entangled state (|01> + |10>)/sqrt(2) can be created as:
            StabilizerState([[1, 1, 0, 0, 0, 0],
                              0, 0, 1, 1, 0, 1]])
        """
        if data is None:
            self._group = np.empty(shape=(0, 0), dtype=bool)
            self._nr_rows = 0
            self._nr_cols = 0
        elif isinstance(data, int):
            X_part = np.zeros(shape=(data, data), dtype=bool)
            Z_part = np.identity(data, dtype=bool)
            phases = np.zeros(shape=(data, 2), dtype=bool)
            self._group = np.concatenate((X_part, Z_part, phases), 1)
            self._nr_rows = data
            self._nr_cols = 2 * data + 2
        elif isinstance(data, StabilizerState):
            self._group = np.array(data._group, dtype=bool)
            self._nr_rows = data._nr_rows
            self._nr_cols = data._nr_cols
        else:
            try:
                self._group = np.array(data, dtype=bool)
            except Exception as err:
                print(data)
                print(type(data))
                raise ValueError("Could not create an array of the 'data' due to the following error: {}".format(err))

            if len(self._group.shape) != 2:
                raise ValueError("'data' needs to be an array of rank 2")
            else:
                self._nr_rows, self._nr_cols = self._group.shape

                if 2 * self._nr_rows == self._nr_cols:
                    if self._nr_rows != 0:
                        self._group = np.append(self._group, [[False, False]] * self._nr_rows, 1)
                elif (2 * self._nr_rows + 2) == self._nr_cols:
                    pass
                else:
                    raise ValueError("'data' needs to be an array of dimension n x 2n or n x (2n +2)")

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
        return 'StabilizerState(np.' + self._group.__repr__() + ')'

    def __str__(self):
        to_return = "Stabilizer state on {} with the following stabilizer generators:\n".format(self.num_qubits)
        for row in self._group:
            to_return += "    {} ".format(self.bool2phase[(row[-2], row[-1])])
            n = self.num_qubits
            for i in range(n):
                to_return += self.bool2Pauli[(row[i], row[i + n])]
            to_return += "\n"
        return to_return

    def __len__(self):
        return self.num_qubits

    @staticmethod
    def boolean_gaussian_elimination(matrix):
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
                non_zero_except_i_max = non_zero_ind[non_zero_ind != i_max]
                new_matrix[non_zero_except_i_max, :] = np.logical_xor(new_matrix[non_zero_except_i_max, :], new_matrix[h, :])
                h += 1
                k += 1
        return new_matrix

    def add_qubit(self):
        """
        Appends a qubit in the state |0> to the current state
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
        """
        Performs the tensor product with another StabilizerState and returns a new
        StabilizerState.

        This can also be done using '*' as for example:
            s1 = StabilizerState([[0, 1]])  # The state |0>
            s2 = StabilizerState([[0, 1]])  # The state |0>

            s3 = s1 * s2  # This is then the state |00>
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
            this_X_stab = self._group[:, :self.num_qubits]
            this_Z_stab = self._group[:, self.num_qubits:-2]
            other_X_stab = other._group[:, :other.num_qubits]
            other_Z_stab = other._group[:, other.num_qubits:-2]

            new_X_stab = block_diag(this_X_stab, other_X_stab)
            new_Z_stab = block_diag(this_Z_stab, other_Z_stab)

            phases = np.append(self._group[:, -2:], other._group[:, -2:], 0)
            new_group = np.concatenate((new_X_stab, new_Z_stab, phases), 1)
            return StabilizerState(new_group)

    def to_array(self, standard_form=False):
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
            return self.boolean_gaussian_elimination(self._group)
        else:
            return np.array(self._group, dtype=bool)

    # def apply_Pauli(self, Pauli, position):
    #     """
    #     Applies a Pauli operator (X, Y or Z) to the qubit a the specified position
    #     of the stabilizer state and updates the generators.
    #     :param Pauli: The Pauli operator to apply
    #     :type Pauli: str
    #     :param position: The position of the qubit.
    #     :type position: int
    #     :return: None
    #     """
    #     if Pauli not in ["X", "Y", "Z"]:
    #         raise ValueError("'Pauli' must be either X, Y or Z (as a str)")
    #     n = self.num_qubits
    #     if not (position >= 0 and position < n):
    #         raise ValueError("position= {} if not a valid qubit position (i.e. in [0, {}]".format(position, n))
    #     for row in self._group:
    #         if self.bool2Pauli[row[position], row[position + n]] in ["I", Pauli]:
    #             pass
    #         else:
    #             row[-1] = not row[-1]

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
        not_yz_control_not_xy_target_rows = np.logical_and(np.logical_not(self._group[:, control + n]), np.logical_not(self._group[:, target]))
        rows_to_flip = np.logical_and(xy_control_yz_target_rows, np.logical_or(yz_control_xy_target_rows, not_yz_control_not_xy_target_rows))
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

        # Perform effective CNOT from the control X column to target Z column
        xy_control_rows = self._group[:, control]
        self._group[xy_control_rows, target + n] = np.logical_not(self._group[xy_control_rows, target + n])

        # Perform effective CNOT from the target X column to control Z column
        xy_target_rows = self._group[:, target]
        self._group[xy_target_rows, control + n] = np.logical_not(self._group[xy_target_rows, control + n])

        # Update the phases

        xy_control_rows = self._group[:, control]
        x_target_rows = np.logical_and(self._group[:, target], np.logical_not(self._group[:, target + n]))
        rows_to_flip = np.logical_and(xy_control_rows, x_target_rows)
        self._group[rows_to_flip, -1] = np.logical_not(self._group[rows_to_flip, -1])

    def measure(self, position, inplace=False):
        """
        Measures qubit 'position' of the stabilizer state in the standard basis.
        If 'inplace=False' the qubit is removed from the state, i.e. the number of qubits in the state is reduced by one.
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
        # Create a new matrix where the X and Z columns of the corresponding qubit are the first.
        columns = np.arange(2*n + 2)
        columns_without_position = np.logical_and(columns != position, columns != (position + n))
        tmp_matrix = np.concatenate((self._group[:, [position, position + n]], self._group[:, columns_without_position]), 1)

        # Perform Gaussian elimination such that there is maximally one X or Y at the qubit position
        tmp_matrix = self.boolean_gaussian_elimination(tmp_matrix)

        # Check if there is an X or a Y at the qubit position
        if tmp_matrix[0, 0]:
            # The first row (generator) of this matrix is then the only one that doesn't commute with the observabel Z
            outcome = randint(0, 1)

            # If outcome is 1 we need to flip phases for the other generators that has an Z at this qubit
            if outcome == 1:
                z_rows = tmp_matrix[:, 1]
                tmp_matrix[z_rows, -1] = np.logical_not(tmp_matrix[z_rows, -1])
            if not inplace:
                # Simply remove first generator and columns for X and Z of this qubit
                self._group = tmp_matrix[1:, 2:]
                self._nr_rows -= 1
            else:
                # Set first generator to be the observable
                tmp_matrix[0, :] = False
                tmp_matrix[0, 1] = True
                if outcome == 1:
                    tmp_matrix[0, -1] = not tmp_matrix[0, -1]
                # Set the rest of the first column to be identity
                tmp_matrix[1:, 1] = False

                # Swap back the X and Z columns of this qubit
                X_part_before_pos = tmp_matrix[:, 2:(position + 2)]
                X_part_after_pos = tmp_matrix[:, (position + 2):n]
                X_part = np.concatenate((X_part_before_pos, tmp_matrix[:, [0]], X_part_after_pos), 1)
                Z_part_before_pos = tmp_matrix[:, n:(position + n + 1)]
                Z_part_after_pos = tmp_matrix[:, (position + n + 1):]
                Z_part = np.concatenate((Z_part_before_pos, tmp_matrix[:, [1]], Z_part_after_pos), 1)
                self._group = np.concatenate((X_part, Z_part), 1)

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
                self._group = tmp_matrix[1:, 2:]
                self._nr_rows -= 1
            else:
                # We don't need to do anything here since the state has not changed
                pass

        return outcome

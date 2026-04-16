#
# Copyright (c) 2017, Stephanie Wehner and Axel Dahlberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from typing import Tuple

from simulaqron.virtual_node.basics import QuantumEngine, QuantumError, NoQubitError
from simulaqron.toolbox.stabilizer_states import StabilizerState
from simulaqron.general import SimUnsupportedError


class StabilizerEngine(QuantumEngine):
    """
    Basic quantum engine which uses stabilizer formalism. Thus, only Clifford operations can be performed
    """

    def __init__(self, node: str, num: int, maxQubits: int = 10):
        """
        Initialize the stabilizer engine.

        :param node: Node name this register is started from.
        :type node: str
        :param num: Number of this register.
        :type num: int
        :param maxQubits: Maximum number of qubits this engine will support.
        :type maxQubits: int
        """

        super().__init__(node=node, num=num, maxQubits=maxQubits)

        self.qubitReg = StabilizerState()

    @property
    def activeQubits(self):
        return self.qubitReg.num_qubits

    def add_fresh_qubit(self) -> int:
        """
        Add a new qubit initialized in the :math:`|0>` state.

        :return: The ID of the new qubit allocated.
        :rtype: int
        """
        # Check if we are still allowed to add qubits
        if self.activeQubits >= self.maxQubits:
            raise NoQubitError("No more qubits available in register.")

        num = self.activeQubits

        # Prepare a clean qubit state in |0>
        self.qubitReg.add_qubit()

        return num

    def add_qubit(self, newQubit):
        """
        Add new qubit in the state described by the array containing the generators of the stabilizer group.
        This should be in the form required by the StabilizerState class.

        :param newQubit: The density matrix of the new qubit.
        :return: The ID of the new qubit allocated.
        :rtype: int
        """

        # Create the qubit
        try:
            qubit = StabilizerState(newQubit)
        except Exception:
            raise ValueError("'newQubits' was not in the correct form to be given as an argument to StabilizerState")

        num = self.activeQubits

        self.qubitReg = self.qubitReg.tensor_product(qubit)

        return num

    def remove_qubit(self, qubitNum):
        """
        Removes the qubit with the desired number qubitNum

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        if (qubitNum + 1) > self.activeQubits:
            raise QuantumError("No such qubit to remove")

        self.measure_qubit(qubitNum)

    def get_register_RI(self):
        """
        Retrieves the entire register in real and imaginary part. Twisted only likes to send real valued lists,
        not complex ones.
        Since this is in stabilizer formalism the real part will be the boolean matrix describing the generators
        and the imaginary part will be None

        :return: The qubit states real and imaginary parts.
        :rtype: Tuple[List[float], List[float]]
        """

        Re = self.qubitReg.to_array().tolist()
        Im = None

        return Re, Im

    def get_density_matrix_RI(self) -> Tuple[Tuple[float], Tuple[float]]:
        """
        Retrieves the density matrix of the qubit as a real and imaginary part. Twisted only
        likes to send real valued lists, not complex ones.

        :return: The qubit density matrix real and imaginary parts.
        :rtype: Tuple[List[float], List[float]]
        """
        # TODO - Implement this
        raise NotImplementedError("get_density_matrix_RI is not implemented for stabilizer engine.")

    def apply_H(self, qubitNum):
        """
        Applies a Hadamard gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        self.qubitReg.apply_H(qubitNum)

    def apply_K(self, qubitNum):
        """
        Applies a K gate to the qubits with number qubitNum. Maps computational basis to Y eigenbasis.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        self.qubitReg.apply_K(qubitNum)

    def apply_X(self, qubitNum):
        """
        Applies a X gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        self.qubitReg.apply_X(qubitNum)

    def apply_Z(self, qubitNum):
        """
        Applies a Z gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        self.qubitReg.apply_Z(qubitNum)

    def apply_Y(self, qubitNum):
        """
        Applies a Y gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        self.qubitReg.apply_Y(qubitNum)

    def apply_T(self, qubitNum):
        """
        Applies a T gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        raise SimUnsupportedError("Cannot apply T gate in stabilizer formalism")

    def apply_rotation(self, qubitNum, n, a):
        """
        Applies a rotation around the axis n with the angle a to qubit with number qubitNum. If n is zero a ValueError
        is raised.

        :param qubitNum: Qubit number
        :type qubitNum: int
        :param n: A tuple of three numbers specifying the rotation axis, e.g n=(1,0,0)
        :type n: Tuple[float, float, float]
        :param a: The rotation angle in radians.
        :type a: float
        """
        raise SimUnsupportedError("Cannot apply arbitrary rotation gate in stabilizer formalism")

    def apply_CNOT(self, qubitNum1, qubitNum2):
        """
        Applies the CNOT to the qubit with the numbers qubitNum1 and qubitNum2.

        :param qubitNum1: Qubit number 1.
        :type qubitNum1: int
        :param qubitNum1: Qubit number 2.
        :type qubitNum1: int
        """
        self.qubitReg.apply_CNOT(qubitNum1, qubitNum2)

    def apply_CPHASE(self, qubitNum1, qubitNum2):
        """
        Applies the CPHASE to the qubit with the numbers qubitNum1 and qubitNum2.

        :param qubitNum1: Qubit number 1.
        :type qubitNum1: int
        :param qubitNum1: Qubit number 2.
        :type qubitNum1: int
        """

        self.qubitReg.apply_CZ(qubitNum1, qubitNum2)

    def apply_onequbit_gate(self, gate, qubitNum):
        """
        Applies a unitary gate to the specified qubit.

        ..warning:: This method is unsupported in the Stabilizer engine.
                    Invoking it will raise ``SimUnsupportedError``.
        """

        raise SimUnsupportedError("Cannot apply arbitrary one qubit gate in stabilizer formalism")

    def apply_twoqubit_gate(self, gate, qubit1, qubit2):
        """
        Applies a unitary gate to the two specified qubits.

        ..warning:: This method is unsupported in the Stabilizer engine.
                    Invoking it will raise ``SimUnsupportedError``.
        """
        raise SimUnsupportedError("Cannot apply arbitrary two qubit gate in stabilizer formalism")

    def measure_qubit_inplace(self, qubitNum: int):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome. The quantum register
        is in the post-measurement state corresponding to the obtained outcome.

        :param qubitNum: The number of the qubit to measure.
        :type qubitNum: int
        """

        # Check we have such a qubit...
        if (qubitNum + 1) > self.activeQubits:
            raise QuantumError("No such qubit to be measured.")

        outcome = self.qubitReg.measure(qubitNum, inplace=True)

        # return measurement outcome
        return outcome

    def measure_qubit(self, qubitNum: int):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome and deletes the qubit.

        :param qubitNum: The number of the qubit to measure.
        :type qubitNum: int
        """
        outcome = self.qubitReg.measure(qubitNum, inplace=False)

        return outcome

    def replace_qubit(self, qubitNum: int, state):
        """
        Replaces the qubit at position qubitNum with the one given by state.

        ..warning:: This method is unsupported in the Stabilizer engine.
                    Invoking it will raise ``SimUnsupportedError``.
        """
        raise NotImplementedError("Currently you cannot replace a qubit using stabilizer formalism")

    def absorb(self, other):
        """
        Absorb the qubits from the other engine into this one. This is done by tensoring the state at the end.

        :param other: The other qubit to absorb.
        :type other: int
        """

        # Check whether there is space
        newNum = self.activeQubits + other.activeQubits
        if newNum > self.maxQubits:
            raise QuantumError("Cannot merge: qubits exceed the maximum available.\n")

        self.qubitReg = self.qubitReg.tensor_product(other.qubitReg)

    def absorb_parts(self, R, I, activeQ):
        """
        Absorb the qubits, given in pieces

        :param R: Real part of the qubit state as a list.
        :type R: List[float]
        :param I: Unused.
        :type I: List[float]
        :param activeQ: Active number of qubits
        """
        # Check whether there is space
        newNum = self.activeQubits + activeQ
        if newNum > self.maxQubits:
            raise QuantumError("Cannot merge: qubits exceed the maximum available.\n")

        self.qubitReg = self.qubitReg.tensor_product(StabilizerState(R))

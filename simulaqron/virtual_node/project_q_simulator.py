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
from typing import Tuple, Dict, List

try:
    import projectq as pQ
except ImportError:
    raise RuntimeError("If you want to use the projectq backend you need to install the python package 'projectq'")
import numpy as np

from simulaqron.virtual_node.basics import QuantumEngine, QuantumError, NoQubitError


class ProjectQEngine(QuantumEngine):
    """
    Basic quantum engine which uses ProjectQ.
    """

    def __init__(self, node: str, num: int, maxQubits: int = 10):
        """
        Initialize the ProjectQ engine.

        :param node: Node name this register is started from.
        :type node: str
        :param num: Number of this register.
        :type num: int
        :param maxQubits: Maximum number of qubits this engine will support.
        :type maxQubits: int
        """

        super().__init__(node=node, num=num, maxQubits=maxQubits)

        # We start with no active qubits
        self.activeQubits = 0

        self.eng = pQ.MainEngine()
        self.qubitReg = []

    def __del__(self):
        """
        Measures out all the current qubits, needed for projectQs garbage collectors.
        """
        # Check first that project Q garbage collector not already removed qubits
        self.eng.flush()
        if not len(self.eng.backend.cheat()[0]) == 0:
            for _ in range(self.activeQubits):
                self.measure_qubit(0)

    def add_fresh_qubit(self) -> int:
        """
        Add a new qubit initialized in the :math:`|0>` state.

        :return: The ID of the new qubit allocated.
        :rtype: int
        """
        # Check if we are still allowed to add qubits
        if self.activeQubits >= self.maxQubits:
            raise NoQubitError("No more qubits available in register.")

        # Prepare a clean qubit state in |0>
        qubit = self.eng.allocate_qubit()[0]

        self.qubitReg.append(qubit)

        num = self.activeQubits

        self.activeQubits += 1

        return num

    def add_qubit(self, newQubit):
        """
        Add new qubit in the state described by the vector newQubit ([a, b])

        :param newQubit: The density matrix of the new qubit.
        :return: The ID of the new qubit allocated.
        :rtype: int
        """

        norm = np.dot(np.array(newQubit), np.array(newQubit).conj())
        if not norm <= 1:
            raise QuantumError(f"State {newQubit} is not normalized.")

        # Create a fresh qubit
        num = self.add_fresh_qubit()

        # Transform the new qubit into the correct state
        pQ.ops.StatePreparation(newQubit) | self.qubitReg[num]

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

    def _get_internal_qubit_state(self) -> Tuple[Dict[int, int], List[complex]]:
        """
        Retrieves the entire register in real and imaginary parts and returns the result as a
        list. Twisted only likes to send real valued lists, not complex ones.
        """
        self.eng.flush()
        order, state = self.eng.backend.cheat()
        # Update the order based on the positions in the qubitReg
        # and not of the qubit IDs
        q_reg_order: Dict[int, int] = {}
        for i, q in enumerate(self.qubitReg):
            q_reg_order[i] = order[q.id]

        return q_reg_order, state

    def get_register_RI(self) -> Tuple[Dict[int, int], Tuple[Tuple[float, ...], Tuple[float, ...]]]:
        """
        Retrieves the entire register in real and imaginary parts and returns the result as a
        list. Twisted only likes to send real valued lists, not complex ones.

        :return: The qubit states real and imaginary parts.
        :rtype: Tuple[Tuple[float, ...], Tuple[float, ...]]
        """
        q_reg_order, state = self._get_internal_qubit_state()

        # Note previously the format of real and imaginary numbers were
        # expected, use the same even though Re will be the qubit mapping
        # and Im the state.
        # Use float() to convert numpy.float64 → Python float so Twisted PB
        # can serialize the values (numpy scalar types become Unpersistable).
        Re = tuple(float(n.real) for n in state)
        Im = tuple(float(n.imag) for n in state)

        return q_reg_order, (Re, Im)

    def get_density_matrix_RI(self) -> Tuple[List[float], List[float]]:
        """
        Retrieves the density matrix of the qubit as a real and imaginary part. Twisted only
        likes to send real valued lists, not complex ones.

        :return: The qubit density matrix real and imaginary parts.
        :rtype: Tuple[List[float], List[float]]
        """
        _, raw_qubit_state = self._get_internal_qubit_state()
        qubit_state = np.array(raw_qubit_state)
        density_matrix = np.outer(qubit_state, qubit_state)
        return density_matrix.real.tolist(), density_matrix.imag.tolist()

    def apply_H(self, qubitNum):
        """
        Applies a Hadamard gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        self.apply_onequbit_gate(pQ.ops.H, qubitNum)

    def apply_K(self, qubitNum):
        """
        Applies a K gate to the qubits with number qubitNum. Maps computational basis to Y eigenbasis.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        self.apply_onequbit_gate(pQ.ops.H, qubitNum)
        self.apply_onequbit_gate(pQ.ops.S, qubitNum)
        self.apply_onequbit_gate(pQ.ops.H, qubitNum)
        self.apply_onequbit_gate(pQ.ops.Z, qubitNum)

    def apply_X(self, qubitNum):
        """
        Applies a X gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        self.apply_onequbit_gate(pQ.ops.X, qubitNum)

    def apply_Z(self, qubitNum):
        """
        Applies a Z gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        self.apply_onequbit_gate(pQ.ops.Z, qubitNum)

    def apply_Y(self, qubitNum):
        """
        Applies a Y gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        self.apply_onequbit_gate(pQ.ops.Y, qubitNum)

    def apply_T(self, qubitNum):
        """
        Applies a T gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        self.apply_onequbit_gate(pQ.ops.T, qubitNum)

    def apply_rotation(self, qubitNum: int, n: Tuple[float, float, float], a: float):
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
        n = tuple(n)
        if n == (1, 0, 0):
            self.apply_onequbit_gate(pQ.ops.Rx(a), qubitNum)
        elif n == (0, 1, 0):
            self.apply_onequbit_gate(pQ.ops.Ry(a), qubitNum)
        elif n == (0, 0, 1):
            self.apply_onequbit_gate(pQ.ops.Rz(a), qubitNum)
        else:
            raise NotImplementedError("Can only do rotations around X, Y, or Z axis right now")

    def apply_CNOT(self, qubitNum1, qubitNum2):
        """
        Applies the CNOT to the qubit with the numbers qubitNum1 and qubitNum2.

        :param qubitNum1: Qubit number 1.
        :type qubitNum1: int
        :param qubitNum1: Qubit number 2.
        :type qubitNum1: int
        """
        self.apply_twoqubit_gate(pQ.ops.CNOT, qubitNum1, qubitNum2)

    def apply_CPHASE(self, qubitNum1, qubitNum2):
        """
        Applies the CPHASE to the qubit with the numbers qubitNum1 and qubitNum2.

        :param qubitNum1: Qubit number 1.
        :type qubitNum1: int
        :param qubitNum1: Qubit number 2.
        :type qubitNum1: int
        """

        self.apply_twoqubit_gate(pQ.ops.CZ, qubitNum1, qubitNum2)

    def apply_onequbit_gate(self, gate, qubitNum: int):
        """
        Applies a unitary gate to the specified qubit.

        :param gate: The project Q gate to be applied.
        :param qubitNum: The number of the qubit this gate is applied to.
        :type qubitNum: int
        """

        if (qubitNum + 1) > self.activeQubits:
            raise QuantumError("No such qubit to apply a single qubit gate to")

        gate | self.qubitReg[qubitNum]

    def apply_twoqubit_gate(self, gate, qubit1: int, qubit2: int):
        """
        Applies a unitary gate to the two specified qubits.

        Arguments:
        :param gate: The project Q gate to be applied
        :param qubit1: The first qubit
        :type qubit1: int
        :param qubit2: The second qubit
        :type qubit2: int
        """
        if (qubit1 + 1) > self.activeQubits:
            raise QuantumError("No such qubit to act as a control qubit")

        if (qubit2 + 1) > self.activeQubits:
            raise QuantumError("No such qubit to act as a target qubit")

        if qubit1 == qubit2:
            raise QuantumError("Control and target are equal")

        gate | (self.qubitReg[qubit1], self.qubitReg[qubit2])

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

        pQ.ops.Measure | self.qubitReg[qubitNum]

        self.eng.flush()

        outcome = int(self.qubitReg[qubitNum])

        # return measurement outcome
        return outcome

    def measure_qubit(self, qubitNum: int):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome and deletes the qubit.

        :param qubitNum: The number of the qubit to measure.
        :type qubitNum: int
        """
        outcome = self.measure_qubit_inplace(qubitNum)

        self.qubitReg.pop(qubitNum)

        # Update the number of qubits
        self.activeQubits = self.activeQubits - 1

        return outcome

    def replace_qubit(self, qubitNum: int, state):
        """
        Replaces the qubit at position qubitNum with the one given by state.

        :param qubitNum: Qubit to be replaced
        :type qubitNum: int
        :param state: New state to write in the place of the old qubit.
        :type state: Any
        """
        raise NotImplementedError("Currently you cannot replace a qubit using project Q as backend")

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

        # Check whether there are in fact qubits to tensor up....
        if self.activeQubits == 0:
            self.eng = other.eng
            self.qubitReg = list(other.qubitReg)
            self.activeQubits = other.activeQubits
        elif other.activeQubits > 0:
            data = other.get_register_RI()
            self.absorb_parts(*data, other.activeQubits)

    def absorb_parts(self, R, I, activeQ):
        """
        Absorb the qubits, given in pieces

        :param R: Real part of the qubit state as a list.
        :type R: List[float]
        :param I: Imaginary part as a list.
        :type I: List[float]
        :param activeQ: Active number of qubits
        """
        # Check whether there is space
        newNum = self.activeQubits + activeQ
        if newNum > self.maxQubits:
            raise QuantumError("Cannot merge: qubits exceed the maximum available.\n")

        if activeQ > 0:
            # Unpack the ordering of qubits and the real and imaginary part
            order, (R, I) = R, I

            # Convert the real and imaginary parts to a state
            state = [re + im * 1j for re, im in zip(R, I)]

            # Allocate qubits in this engine for the new qubits from the other engine
            qreg = self.eng.allocate_qureg(activeQ)

            # Put the new qubits in the correct state
            pQ.ops.StatePreparation(state) | qreg

            # Put the qubits in the correct order
            # The `order` is a mapping from the previous qubit IDs
            # to the bit position in the state. The qubits in the `qreg`
            # are therefore in the old bit positions which needs to be updated.
            new_qubits = [None] * len(qreg)
            for old_q_id, old_bit_pos in order.items():
                new_qubits[old_q_id] = qreg[old_bit_pos]

            # Add the qubits to the list of qubits
            self.qubitReg += new_qubits

            self.activeQubits = newNum

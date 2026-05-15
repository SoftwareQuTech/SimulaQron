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
import cmath
import logging
import math
from typing import Tuple, List

import numpy as np
from qutip import Qobj

try:
    import qutip as qp
    import qutip.qip.operations.gates as gate_ops

    # qutip-qip >= 0.3 renamed/moved gate expansion helpers.
    # Patch the old names as shims so the rest of this file needs no changes.
    if not hasattr(gate_ops, "gate_expand_1toN"):
        from qutip_qip.operations import expand_operator as _expand_op
        gate_ops.gate_expand_1toN = lambda U, N, t: _expand_op(U, N, t)

    if not hasattr(qp, "gate_expand_2toN"):
        from qutip_qip.operations import expand_operator as _expand_op
        qp.gate_expand_2toN = lambda U, N, t1, t2: _expand_op(U, N, [t1, t2])

except ImportError:
    raise RuntimeError("If you want to use the qutip backend you need to install simulaqron "
                       "with the optional dependencies: 'pip install simulaqron[opt]'")

from simulaqron.virtual_node.basics import QuantumEngine, QuantumError, NoQubitError


class QutipEngine(QuantumEngine):
    """
    Basic quantum engine which uses QuTip. Works with density matrices and in principle allows
    full quantum dynamics via QuTip. Subsequently, this is quite slow.
    """
    def __init__(self, node: str, num: int, maxQubits: int = 10):
        """
        Initializes the Qutip engine.

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
        self.qubitReg = qp.Qobj()

    def add_fresh_qubit(self) -> int:
        """
        Add a new qubit initialized in the :math:`|0>` state.

        :return: The ID of the new qubit allocated.
        :rtype: int
        """

        # Prepare a clean qubit state in |0>
        v = qp.basis(2, 0)
        newQubit = v * v.dag()

        num = self.add_qubit(newQubit)
        return num

    def add_qubit(self, newQubit):
        """
        Add new qubit in the state described by the density matrix newQubit.

        :param newQubit: The density matrix of the new qubit.
        :return: The ID of the new qubit allocated.
        :rtype: int
        """

        # Check if we are still allowed to add qubits
        if self.activeQubits >= self.maxQubits:
            raise NoQubitError("No more qubits available in register.")

        # Append to the existing state at the end
        if self.activeQubits > 0:
            self.qubitReg = qp.tensor(self.qubitReg, newQubit)
        else:
            self.qubitReg = newQubit

        # Index number of that qubit
        num = self.activeQubits

        # Increment the number of qubits
        self.activeQubits = self.activeQubits + 1

        return num

    def remove_qubit(self, qubitNum: int):
        """
        Removes the qubit with the desired number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        if (qubitNum + 1) > self.activeQubits:
            raise QuantumError("No such qubit to remove")

        # Check if this the only qubit
        if self.activeQubits == 1:
            self.activeQubits = 0
            self.qubitReg = qp.Qobj()
            return

        # Compute the list of qubits to keep
        keepList = []
        for j in range(self.activeQubits):
            if j != qubitNum:
                keepList.append(j)

        # Trace out this qubit by taking the partial trace
        self.qubitReg = self.qubitReg.ptrace(keepList)

        # Update the number of qubits
        self.activeQubits = self.activeQubits - 1

    def get_qubits_RI(self, qList: List[int]) -> Tuple[List[float], List[float]]:
        """
        Retrieves the qubits in the list and returns the result as a list divided into
        a real and imaginary part. Twisted only likes to send real values lists,
        not complex ones.

        :param qList: List of qubits to retrieve, e.g. [1, 4]
        :type qList: List[int]
        :return: The qubits states real and imaginary parts.
        :rtype: Tuple[List[float], List[float]]
        """
        rho = self.get_qubits(qList)
        Re = rho.full().real.tolist()
        Im = rho.full().imag.tolist()

        return (Re, Im)

    def get_register_RI(self) -> Tuple[List[float], List[float]]:
        """
        Retrieves the entire register in real and imaginary parts and returns the result as a
        list. Twisted only likes to send real valued lists, not complex ones.

        :return: The qubit states real and imaginary parts.
        :rtype: Tuple[List[float], List[float]]
        """
        Re = self.qubitReg.full().real.tolist()
        Im = self.qubitReg.full().imag.tolist()

        return Re, Im

    def get_density_matrix_RI(self) -> Tuple[Tuple[float], Tuple[float]]:
        """
        Retrieves the density matrix of the qubit as a real and imaginary part. Twisted only
        likes to send real valued lists, not complex ones.

        :return: The qubit density matrix real and imaginary parts.
        :rtype: Tuple[List[float], List[float]]
        """
        Re = self.qubitReg.full().real.tolist()
        Im = self.qubitReg.full().imag.tolist()

        return Re, Im
        # Qutip uses density matrices as the internal representation, so we don't need
        # to compute the outer product to get the result
        real_part, im_part = self.get_register_RI()
        return tuple(*real_part), tuple(*im_part)

    def apply_H(self, qubitNum):
        """
        Applies a Hadamard gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        f = math.sqrt(2)
        H = qp.Qobj([[1 / f, 1 / f], [1 / f, -1 / f]], dims=[[2], [2]])
        self.apply_onequbit_gate(H, qubitNum)

    def apply_K(self, qubitNum):
        """
        Applies a K gate to the qubits with number qubitNum. Maps computational basis to Y eigenbasis.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        f = math.sqrt(2)
        i = complex(0, 1)
        K = qp.Qobj([[1 / f, -i / f], [i / f, -1 / f]], dims=[[2], [2]])
        self.apply_onequbit_gate(K, qubitNum)

    def apply_X(self, qubitNum):
        """
        Applies a X gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        X = qp.Qobj([[0, 1], [1, 0]], dims=[[2], [2]])
        self.apply_onequbit_gate(X, qubitNum)

    def apply_Z(self, qubitNum):
        """
        Applies a Z gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        Z = qp.Qobj([[1, 0], [0, -1]], dims=[[2], [2]])
        self.apply_onequbit_gate(Z, qubitNum)

    def apply_Y(self, qubitNum):
        """
        Applies a Y gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """

        i = complex(0, 1)
        Y = qp.Qobj([[0, -i], [i, 0]], dims=[[2], [2]])
        self.apply_onequbit_gate(Y, qubitNum)

    def apply_T(self, qubitNum):
        """
        Applies a T gate to the qubits with number qubitNum.

        :param qubitNum: Qubit number
        :type qubitNum: int
        """
        i = complex(0, 1)
        Y = qp.Qobj([[1, 0], [0, cmath.exp(i * np.pi / 4)]], dims=[[2], [2]])
        self.apply_onequbit_gate(Y, qubitNum)

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
        nNorm = np.linalg.norm(n)
        if nNorm == 0:
            raise ValueError("Rotation vector n can't be 0")
        R = (-1j * a / (2 * nNorm) * (n[0] * qp.sigmax() + n[1] * qp.sigmay() + n[2] * qp.sigmaz())).expm()
        self.apply_onequbit_gate(R, qubitNum)

    def apply_CNOT(self, qubitNum1: int, qubitNum2: int):
        """
        Applies the CNOT to the qubit with the numbers qubitNum1 and qubitNum2.

        :param qubitNum1: Qubit number 1.
        :type qubitNum1: int
        :param qubitNum1: Qubit number 2.
        :type qubitNum1: int
        """

        # Construct the CNOT matrix
        cnot = qp.Qobj([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dims=[[2, 2], [2, 2]])

        # Apply it to the desired qubits
        self.apply_twoqubit_gate(cnot, qubitNum1, qubitNum2)

    def apply_CPHASE(self, qubitNum1, qubitNum2):
        """
        Applies the CPHASE to the qubit with the numbers qubitNum1 and qubitNum2.

        :param qubitNum1: Qubit number 1.
        :type qubitNum1: int
        :param qubitNum1: Qubit number 2.
        :type qubitNum1: int
        """

        # Construct the CPHASE matrix
        cphase = qp.Qobj([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], dims=[[2, 2], [2, 2]])

        # Apply it to the desired qubits
        self.apply_twoqubit_gate(cphase, qubitNum1, qubitNum2)

    def get_qubits(self, list: List[int]):
        """
        Returns the qubits with numbers in list.

        :param list: List of qubits to retrieve.
        :type list: List[int]
        """

        # Qutip distinguishes between system dimensionality and matrix dimensionality
        # so we need to make sure it knows we are talking about multiple qubits
        k = int(math.log2(self.qubitReg.shape[0]))
        dimL = []
        for j in range(k):
            dimL.append(2)

        self.qubitReg.dims = [dimL, dimL]

        logging.debug("Dimensions %s", self.qubitReg.dims)
        return self.qubitReg.ptrace(list)

    def apply_onequbit_gate(self, gateU: Qobj, qubitNum: int):
        """
        Applies a unitary gate to the specified qubit.

        :param gateU: Unitary to apply as Qobj.
        :type gateU: Qobj
        :param qubitNum: The number of the qubit this gate is applied to
        :type qubitNum: int
        """

        overallU = gate_ops.gate_expand_1toN(gateU, self.activeQubits, qubitNum)
        # Compute the overall unitary, identity everywhere with gateU at position qubitNum

        # Qutip distinguishes between system dimensionality and matrix dimensionality
        # so we need to make sure it knows we are talking about multiple qubits
        k = int(math.log2(overallU.shape[0]))
        dimL = []
        for j in range(k):
            dimL.append(2)

        overallU.dims = [dimL, dimL]
        self.qubitReg.dims = [dimL, dimL]

        # Apply the unitary
        self.qubitReg = overallU * self.qubitReg * overallU.dag()

    def apply_twoqubit_gate(self, gateU: Qobj, qubit1: int, qubit2: int):
        """
        Applies a unitary gate to the two specified qubits.

        :param gateU: Unitary to apply as Qobj.
        :type gateU: Qobj
        :param qubit1: The first qubit
        :type qubit1: int
        :param qubit2: The second qubit
        :type qubit2: int
        """

        # Construct the overall unitary
        overallU = qp.gate_expand_2toN(gateU, self.activeQubits, qubit1, qubit2)

        # Qutip distinguishes between system dimensionality and matrix dimensionality
        # so we need to make sure it knows we are talking about multiple qubits
        k = int(math.log2(overallU.shape[0]))
        dimL = []
        for j in range(k):
            dimL.append(2)

        overallU.dims = [dimL, dimL]
        self.qubitReg.dims = [dimL, dimL]

        # Apply the  unitary
        self.qubitReg = overallU * self.qubitReg * overallU.dag()

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

        # Construct the two measurement operators, and put them at the right position
        v0 = qp.basis(2, 0)
        P0 = v0 * v0.dag()
        M0 = gate_ops.gate_expand_1toN(P0, self.activeQubits, qubitNum)

        v1 = qp.basis(2, 1)
        P1 = v1 * v1.dag()
        M1 = gate_ops.gate_expand_1toN(P1, self.activeQubits, qubitNum)

        # Compute the success probabilities
        obj = M0 * self.qubitReg
        p0 = obj.tr().real
        obj = M1 * self.qubitReg
        p1 = obj.tr().real

        # Clamp and renormalize to handle tiny negative values that can arise
        # from floating-point rounding after multi-qubit gate sequences.
        p0 = max(0.0, p0)
        p1 = max(0.0, p1)
        total = p0 + p1
        if total > 0:
            p0 /= total
            p1 /= total
        else:
            p0, p1 = 0.5, 0.5

        # Sample the measurement outcome from these probabilities
        outcome = np.random.choice([0, 1], p=[p0, p1]).item()

        # Compute the post-measurement state, getting rid of the measured qubit
        if outcome == 0:
            self.qubitReg = M0 * self.qubitReg * M0.dag() / p0
        else:
            self.qubitReg = M1 * self.qubitReg * M1.dag() / p1

        # return measurement outcome
        return outcome

    def measure_qubit(self, qubitNum: int):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome and deletes the qubit.

        :param qubitNum: The number of the qubit to measure.
        :type qubitNum: int
        """
        outcome = self.measure_qubit_inplace(qubitNum)
        self.remove_qubit(qubitNum)

        return outcome

    def replace_qubit(self, qubitNum: int, state):
        """
        Replaces the qubit at position qubitNum with the one given by state.

        :param qubitNum: Qubit to be replaced
        :type qubitNum: int
        :param state: New state to write in the place of the old qubit.
        :type state: Any
        """

        # Remove the qubit currently there by tracing it out
        self.remove_qubit(qubitNum)

        # Tensor on the new qubit at the end
        self.add_qubit(state)

        # Put the new qubit in the correct position
        qList = list(range(self.activeQubits))
        qList[qubitNum] = self.activeQubits
        qList[self.activeQubits - 1] = qubitNum
        self.qubitReg.permute(qList)

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
            self.qubitReg = other.qubitReg
        elif other.activeQubits != 0:
            self.qubitReg = qp.tensor(self.qubitReg, other.qubitReg)

        self.activeQubits = newNum

    def absorb_parts(self, R, I, activeQ):
        """
        Absorb the qubits, given in pieces

        :param R: Real part of the qubit state as a list.
        :type R: List[float]
        :param I: Imaginary part as a list.
        :type I: List[float]
        :param activeQ: Active number of qubits
        """

        # Convert the real and imaginary parts given as lists into a qutip object
        M = I
        for s in range(len(I)):
            for t in range(len(I)):
                M[s][t] = R[s][t] + I[s][t] * 1j

        qt = qp.Qobj(M)

        # Check whether there is space
        newNum = self.activeQubits + activeQ
        if newNum > self.maxQubits:
            raise QuantumError("Cannot merge: qubits exceed the maximum available.\n")

        # Check whether there are in fact qubits to tensor up....
        if self.activeQubits == 0:
            self.qubitReg = qt
        elif qt.shape[0] != 0:
            self.qubitReg = qp.tensor(self.qubitReg, qt)

        self.activeQubits = newNum

        # Qutip distinguishes between system dimensionality and matrix dimensionality
        # so we need to make sure it knows we are talking about multiple qubits
        k = int(math.log2(self.qubitReg.shape[0]))
        dimL = []
        for j in range(k):
            dimL.append(2)

        self.qubitReg.dims = [dimL, dimL]

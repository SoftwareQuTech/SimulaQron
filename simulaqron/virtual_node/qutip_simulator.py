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
import math
import cmath

import numpy as np
import logging

try:
    import qutip as qp
except ImportError:
    raise RuntimeError("If you want to use the qutip backend you need to install the python package 'qutip'")

from simulaqron.virtual_node.basics import quantumEngine, quantumError, noQubitError


class qutipEngine(quantumEngine):
    """
    Basic quantum engine which uses QuTip. Works with density matrices and in principle allows full quantum
    dynamics via QuTip. Subsequently, this is quite slow.

    Attributes:
        maxQubits:	maximum number of qubits this engine will support.
    """

    def __init__(self, node, num, maxQubits=10):
        """
        Initialize the simple engine. If no number is given for maxQubits, the assumption will be 10.
        """
        super().__init__(node=node, num=num, maxQubits=maxQubits)

        # We start with no active qubits
        self.activeQubits = 0
        self.qubitReg = qp.Qobj()

    def add_fresh_qubit(self):
        """
        Add a new qubit initialized in the \|0\> state.
        """

        # Prepare a clean qubit state in |0>
        v = qp.basis(2, 0)
        newQubit = v * v.dag()

        num = self.add_qubit(newQubit)
        return num

    def add_qubit(self, newQubit):
        """
        Add new qubit in the state described by the density matrix newQubit
        """

        # Check if we are still allowed to add qubits
        if self.activeQubits >= self.maxQubits:
            raise noQubitError("No more qubits available in register.")

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

    def remove_qubit(self, qubitNum):
        """
        Removes the qubit with the desired number qubitNum
        """
        if (qubitNum + 1) > self.activeQubits:
            raise quantumError("No such qubit to remove")

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

    def get_qubits_RI(self, qList):
        """
        Retrieves the qubits in the list and returns the result as a list divided into
        a real and imaginary part. Twisted only likes to send real values lists,
        not complex ones.

        Arguments
        qList		list of qubits to retrieve, e.g. [1, 4]
        """
        rho = self.get_qubits(qList)
        Re = rho.full().real.tolist()
        Im = rho.full().imag.tolist()

        return (Re, Im)

    def get_register_RI(self):
        """
        Retrieves the entire register in real and imaginary parts and returns the result as a
        list. Twisted only likes to send real valued lists, not complex ones.
        """
        Re = self.qubitReg.full().real.tolist()
        Im = self.qubitReg.full().imag.tolist()

        return (Re, Im)

    def apply_H(self, qubitNum):
        """
        Applies a Hadamard gate to the qubits with number qubitNum.
        """

        f = math.sqrt(2)
        H = qp.Qobj([[1 / f, 1 / f], [1 / f, -1 / f]], dims=[[2], [2]])
        self.apply_onequbit_gate(H, qubitNum)

    def apply_K(self, qubitNum):
        """
        Applies a K gate to the qubits with number qubitNum. Maps computational basis to Y eigenbasis.
        """

        f = math.sqrt(2)
        i = complex(0, 1)
        K = qp.Qobj([[1 / f, -i / f], [i / f, -1 / f]], dims=[[2], [2]])
        self.apply_onequbit_gate(K, qubitNum)

    def apply_X(self, qubitNum):
        """
        Applies a X gate to the qubits with number qubitNum.
        """

        X = qp.Qobj([[0, 1], [1, 0]], dims=[[2], [2]])
        self.apply_onequbit_gate(X, qubitNum)

    def apply_Z(self, qubitNum):
        """
        Applies a Z gate to the qubits with number qubitNum.
        """

        Z = qp.Qobj([[1, 0], [0, -1]], dims=[[2], [2]])
        self.apply_onequbit_gate(Z, qubitNum)

    def apply_Y(self, qubitNum):
        """
        Applies a Y gate to the qubits with number qubitNum.
        """

        i = complex(0, 1)
        Y = qp.Qobj([[0, -i], [i, 0]], dims=[[2], [2]])
        self.apply_onequbit_gate(Y, qubitNum)

    def apply_T(self, qubitNum):
        """
        Applies a T gate to the qubits with number qubitNum.
        """
        i = complex(0, 1)
        Y = qp.Qobj([[1, 0], [0, cmath.exp(i * np.pi / 4)]], dims=[[2], [2]])
        self.apply_onequbit_gate(Y, qubitNum)

    def apply_rotation(self, qubitNum, n, a):
        """
        Applies a rotation around the axis n with the angle a to qubit with number qubitNum. If n is zero a ValueError
        is raised.

        :param qubitNum: int
            Qubit number
        :param n: tuple
            A tuple of three numbers specifying the rotation axis, e.g n=(1,0,0)
        :param a: float
            The rotation angle in radians.
        :rtype: None
        """
        nNorm = np.linalg.norm(n)
        if nNorm == 0:
            raise ValueError("Rotation vector n can't be 0")
        R = (-1j * a / (2 * nNorm) * (n[0] * qp.sigmax() + n[1] * qp.sigmay() + n[2] * qp.sigmaz())).expm()
        self.apply_onequbit_gate(R, qubitNum)

    def apply_CNOT(self, qubitNum1, qubitNum2):
        """
        Applies the CNOT to the qubit with the numbers qubitNum1 and qubitNum2.
        """

        # Construct the CNOT matrix
        cnot = qp.Qobj([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dims=[[2, 2], [2, 2]])

        # Apply it to the desired qubits
        self.apply_twoqubit_gate(cnot, qubitNum1, qubitNum2)

    def apply_CPHASE(self, qubitNum1, qubitNum2):
        """
        Applies the CPHASE to the qubit with the numbers qubitNum1 and qubitNum2.
        """

        # Construct the CPHASE matrix
        cphase = qp.Qobj([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], dims=[[2, 2], [2, 2]])

        # Apply it to the desired qubits
        self.apply_twoqubit_gate(cphase, qubitNum1, qubitNum2)

    def get_qubits(self, list):
        """
        Returns the qubits with numbers in list.
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

    def apply_onequbit_gate(self, gateU, qubitNum):
        """
        Applies a unitary gate to the specified qubit.

        Arguments:
        gateU   	unitary to apply as Qobj
        qubitNum 	the number of the qubit this gate is applied to
        """

        # Compute the overall unitary, identity everywhere with gateU at position qubitNum
        overallU = qp.gate_expand_1toN(gateU, self.activeQubits, qubitNum)

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

    def apply_twoqubit_gate(self, gateU, qubit1, qubit2):
        """
        Applies a unitary gate to the two specified qubits.

        Arguments:
        gateU		unitary to apply as Qobj
        qubit1 		the first qubit
        qubit2		the second qubit
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

    def measure_qubit_inplace(self, qubitNum):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome. The quantum register
        is in the post-measurment state corresponding to the obtained outcome.

        Arguments:
        qubitNum	qubit to be measured
        """

        # Check we have such a qubit...
        if (qubitNum + 1) > self.activeQubits:
            raise quantumError("No such qubit to be measured.")

        # Construct the two measurement operators, and put them at the right position
        v0 = qp.basis(2, 0)
        P0 = v0 * v0.dag()
        M0 = qp.gate_expand_1toN(P0, self.activeQubits, qubitNum)

        v1 = qp.basis(2, 1)
        P1 = v1 * v1.dag()
        M1 = qp.gate_expand_1toN(P1, self.activeQubits, qubitNum)

        # Compute the success probabilities
        obj = M0 * self.qubitReg
        p0 = obj.tr().real
        obj = M1 * self.qubitReg
        p1 = obj.tr().real

        # Sample the measurement outcome from these probabilities
        outcome = int(np.random.choice([0, 1], 1, p=[p0, p1]))

        # Compute the post-measurement state, getting rid of the measured qubit
        if outcome == 0:
            self.qubitReg = M0 * self.qubitReg * M0.dag() / p0
        else:
            self.qubitReg = M1 * self.qubitReg * M1.dag() / p1

        # return measurement outcome
        return outcome

    def measure_qubit(self, qubitNum):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome and deletes the qubit.

        Arguments:
        qubitNum	qubit to be measured
        """
        outcome = self.measure_qubit_inplace(qubitNum)
        self.remove_qubit(qubitNum)

        return outcome

    def replace_qubit(self, qubitNum, state):
        """
        Replaces the qubit at position qubitNum with the one given by state.
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
        """

        # Check whether there is space
        newNum = self.activeQubits + other.activeQubits
        if newNum > self.maxQubits:
            raise quantumError("Cannot merge: qubits exceed the maximum available.\n")

        # Check whether there are in fact qubits to tensor up....
        if self.activeQubits == 0:
            self.qubitReg = other.qubitReg
        elif other.activeQubits != 0:
            self.qubitReg = qp.tensor(self.qubitReg, other.qubitReg)

        self.activeQubits = newNum

    def absorb_parts(self, R, I, activeQ):
        """
        Absorb the qubits, given in pieces

        Arguments:
        R		real part of the qubit state as a list
        I		imaginary part as a list
        activeQ		active number of qubits
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
            raise quantumError("Cannot merge: qubits exceed the maximum available.\n")

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

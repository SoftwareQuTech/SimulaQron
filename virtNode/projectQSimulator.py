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

import qutip as qp
import math
import cmath
import projectq as pQ

import numpy as np
import logging

from SimulaQron.virtNode.basics import quantumError, noQubitError
from SimulaQron.virtNode.crudeSimulator import Engine


class projectQEngine(Engine):
    """
    Basic quantum engine which uses ProjectQ.

    Attributes:
        maxQubits:	maximum number of qubits this engine will support.
    """

    def __init__(self, maxQubits=10):
        """
        Initialize the simple engine. If no number is given for maxQubits, the assumption will be 10.
        """

        self.maxQubits = maxQubits

        # We start with no active qubits
        self.reset()

    def reset(self):
        """
        Resets this register to 0 qubits.
        """
        self.activeQubits = 0
        self.eng = pQ.MainEngine()
        self.qubitReg = []

    def add_fresh_qubit(self):
        """
        Add a new qubit initialized in the \|0\> state.
        """

        # Prepare a clean qubit state in |0>
        newQubit = self.eng.allocate_qubit()

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
        self.qubitReg.append(newQubit)

        # Index number of that qubit
        num = self.activeQubits

        # Increment the number of qubits
        self.activeQubits = self.activeQubits + 1

        return (num)

    def remove_qubit(self, qubitNum):
        """
        Removes the qubit with the desired number qubitNum
        """
        if (qubitNum + 1) > self.activeQubits:
            raise quantumError("No such qubit to remove")

        self.qubitReg.pop(qubitNum)

        # Update the number of qubits
        self.activeQubits = self.activeQubits - 1

    # def get_qubits(self, list):
    #     """
    #     Returns the qubits with numbers in list.
    #     """
    #
    #     # Qutip distinguishes between system dimensionality and matrix dimensionality
    #     # so we need to make sure it knows we are talking about multiple qubits
    #     k = int(math.log2(self.qubitReg.shape[0]))
    #     dimL = []
    #     for j in range(k):
    #         dimL.append(2)
    #
    #     self.qubitReg.dims = [dimL, dimL]
    #
    #     logging.debug("Dimensions %s", self.qubitReg.dims)
    #     return self.qubitReg.ptrace(list)
    #
    # def get_qubits_RI(self, qList):
    #     """
    #     Retrieves the qubits in the list and returns the result as a list divided into
    #     a real and imaginary part. Twisted only likes to send real values lists,
    #     not complex ones.
    #
    #     Arguments
    #     qList		list of qubits to retrieve, e.g. [1, 4]
    #     """
    #     rho = self.get_qubits(qList)
    #     Re = rho.full().real.tolist()
    #     Im = rho.full().imag.tolist()
    #
    #     return (Re, Im)

    def get_register_RI(self):
        """
        Retrieves the entire register in real and imaginary parts and returns the result as a
        list. Twisted only likes to send real valued lists, not complex ones.
        """
        self.eng.flush()
        state = self.eng.backend.cheat()[1]

        Re = tuple(n.real for n in state)
        Im = tuple(n.imag for n in state)

        return (Re, Im)

    def apply_H(self, qubitNum):
        """
        Applies a Hadamard gate to the qubits with number qubitNum.
        """
        self.apply_onequbit_gate(pQ.ops.H, qubitNum)

    def apply_K(self, qubitNum):
        """
        Applies a K gate to the qubits with number qubitNum. Maps computational basis to Y eigenbasis.
        """
        self.apply_onequbit_gate(pQ.ops.H, qubitNum)
        self.apply_onequbit_gate(pQ.ops.S, qubitNum)

    def apply_X(self, qubitNum):
        """
        Applies a X gate to the qubits with number qubitNum.
        """

        self.apply_onequbit_gate(pQ.ops.X, qubitNum)

    def apply_Z(self, qubitNum):
        """
        Applies a Z gate to the qubits with number qubitNum.
        """

        self.apply_onequbit_gate(pQ.ops.Z, qubitNum)

    def apply_Y(self, qubitNum):
        """
        Applies a Y gate to the qubits with number qubitNum.
        """

        self.apply_onequbit_gate(pQ.ops.Y, qubitNum)

    def apply_T(self, qubitNum):
        """
        Applies a T gate to the qubits with number qubitNum.
        """
        self.apply_onequbit_gate(pQ.ops.T, qubitNum)

    def apply_rotation(self, qubitNum, n, a):
        """
        Applies a rotation around the axis n with the angle a to qubit with number qubitNum. If n is zero a ValueError
        is raised.
        Arguments:
                qubitNum    Qubit number
        n	    A tuple of three numbers specifying the rotation axis, e.g n=(1,0,0)
        a	    The rotation angle in radians.
        """
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
        """
        self.apply_twoqubit_gate(pQ.ops.CNOT, qubitNum1, qubitNum2)

    def apply_CPHASE(self, qubitNum1, qubitNum2):
        """
        Applies the CPHASE to the qubit with the numbers qubitNum1 and qubitNum2.
        """

        self.apply_twoqubit_gate(pQ.ops.CZ, qubitNum1, qubitNum2)

    def apply_onequbit_gate(self, gate, qubitNum):
        """
        Applies a unitary gate to the specified qubit.

        Arguments:
        gate       The project Q gate to be applied
        qubitNum 	the number of the qubit this gate is applied to
        """

        if (qubitNum + 1) > self.activeQubits:
            raise quantumError("No such qubit to apply a single qubit gate to")

        gate | self.qubitReg[qubitNum]

    def apply_twoqubit_gate(self, gate, qubit1, qubit2):
        """
        Applies a unitary gate to the two specified qubits.

        Arguments:
        gate       The project Q gate to be applied
        qubit1 		the first qubit
        qubit2		the second qubit
        """
        if (qubit1 + 1) > self.activeQubits:
            raise quantumError("No such qubit to act as a control qubit")

        if (qubit2 + 1) > self.activeQubits:
            raise quantumError("No such qubit to act as a target qubit")

        if qubit1 == qubit2:
            raise quantumError("Control and target are equal")

        gate | (self.qubitReg[qubit1], self.qubitReg[qubit2])

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

        pQ.ops.Measure | self.qubitReg[qubitNum]

        self.eng.flush()

        outcome = int(self.qubitReg[qubitNum])

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
        raise NotImplementedError("Currently you cannot replace a qubit using project Q as backend")

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


class quantumRegister(projectQEngine):
    """
    A simulated quantum register. The qubits who are simulated in this register may be distributed over
    different quantum nodes.
    """

    def __init__(self, node, num, maxQubits=10):
        """
        Initialize the quantum register at the given node.

        Arguments
        node		node this register is started from
        num		number of this register
        maxQubits	maximum number of qubits this register supports
        """

        self.maxQubits = maxQubits
        self.activeQubits = 0
        self.qubitReg = 0

        # Each register has a number, this may be used be the ``outside`` application
        # using this simulator
        self.num = num

        # Node that actually simulates this register
        self.simNode = node

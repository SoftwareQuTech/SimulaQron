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

try:
    from pyqrack import QrackSimulator, Pauli
except ImportError:
    raise RuntimeError("If you want to use the pyqrack backend you need to install the python package 'pyqrack'")
import numpy as np

from simulaqron.virtual_node.basics import quantumEngine, quantumError, noQubitError


class pyqrackEngine(quantumEngine):
    """
    Basic quantum engine which uses PyQrack.

    Attributes:
        maxQubits:	maximum number of qubits this engine will support.
    """

    def __init__(self, node, num, maxQubits=10):
        """
        Initialize the simple engine. If no number is given for maxQubits, the assumption will be 10.
        """

        super().__init__(node=node, num=num, maxQubits=maxQubits)

        self.engine = QrackSimulator()

        # We start with no active qubits
        self.activeQubits = 0
        self.nextQid = 0
        self.qubitReg = []

    def add_fresh_qubit(self):
        """
        Add a new qubit initialized in the \|0\> state.
        """
        # Check if we are still allowed to add qubits
        if self.activeQubits >= self.maxQubits:
            raise noQubitError("No more qubits available in register.")

        # Prepare a clean qubit state in |0>
        qid = self.nextQid
        self.nextQid += 1
        self.engine.allocate_qubit(qid)
        self.activeQubits += 1
        self.qubitReg.append(qid)

        return qid

    def add_qubit(self, newQubit):
        """
        Add new qubit in the state described by the vector newQubit ([a, b])
        """

        norm = np.dot(np.array(newQubit), np.array(newQubit).conj())
        if not norm <= 1:
            raise quantumError("State {} is not normalized.".format(newQubit))

        # Create a fresh qubit
        qid = self.add_fresh_qubit()

        # Find an appropriate state preparation gate
        prob = np.dot(complex(newQubit[1]), np.conj(complex(newQubit[1])))
        sqrtProb = np.sqrt(prob)
        sqrt1MinProb = np.sqrt(1 - prob)

        phase0 = 0
        if sqrt1MinProb > 0:
            phase0 = complex(newQubit[0]) / sqrt1MinProb

        phase1 = 0
        if sqrtProb > 0:
            phase1 = complex(newQubit[1]) / sqrt1MinProb

        cMtrx = [sqrt1MinProb * phase0, sqrtProb * phase0, sqrtProb * phase1, -sqrt1MinProb * phase1]

        # Transform the new qubit into the correct state
        self.engine.mtrx(cMtrx, qid)

        return qid

    def validate_qid(self, qid):
        if qid not in self.qubitReg:
            raise quantumError("No such qubit to remove")

    def remove_qubit(self, qubitNum):
        """
        Removes the qubit with the desired number qubitNum
        """
        self.validate_qid(qubitNum)

        self.engine.release(qubitNum)
        self.qubitReg.remove(qubitNum)
        self.activeQubits -= 1

    def get_register_RI(self):
        """
        Retrieves the entire register in real and imaginary parts and returns the result as a
        list. Twisted only likes to send real valued lists, not complex ones.
        """
        raise NotImplementedError("get_register_RI() not implemented for this backend!")

    def apply_H(self, qubitNum):
        """
        Applies a Hadamard gate to the qubits with number qubitNum.
        """
        self.validate_qid(qubitNum)

        self.engine.h(qubitNum)

    def apply_K(self, qubitNum):
        """
        Applies a K gate to the qubits with number qubitNum. Maps computational basis to Y eigenbasis.
        """
        self.validate_qid(qubitNum)

        self.engine.h(qubitNum)
        self.engine.s(qubitNum)
        self.engine.h(qubitNum)
        self.engine.z(qubitNum)

    def apply_X(self, qubitNum):
        """
        Applies a X gate to the qubits with number qubitNum.
        """
        self.validate_qid(qubitNum)

        self.engine.x(qubitNum)

    def apply_Z(self, qubitNum):
        """
        Applies a Z gate to the qubits with number qubitNum.
        """
        self.validate_qid(qubitNum)

        self.engine.z(qubitNum)

    def apply_Y(self, qubitNum):
        """
        Applies a Y gate to the qubits with number qubitNum.
        """
        self.validate_qid(qubitNum)

        self.engine.y(qubitNum)

    def apply_T(self, qubitNum):
        """
        Applies a T gate to the qubits with number qubitNum.
        """
        self.validate_qid(qubitNum)

        self.engine.t(qubitNum)

    def apply_rotation(self, qubitNum, n, a):
        """
        Applies a rotation around the axis n with the angle a to qubit with number qubitNum. If n is zero a ValueError
        is raised.

        :param qubitNum: int
            Qubit number
        :param n: tuple of floats
            A tuple of three numbers specifying the rotation axis, e.g n=(1,0,0)
        :param a: float
            The rotation angle in radians.
        """
        self.validate_qid(qubitNum)

        n = tuple(n)
        if n == (1, 0, 0):
            self.engine.r(Pauli.PauliX, a, qubitNum)
        elif n == (0, 1, 0):
            self.engine.r(Pauli.PauliY, a, qubitNum)
        elif n == (0, 0, 1):
            self.engine.r(Pauli.PauliZ, a, qubitNum)
        else:
            raise NotImplementedError("Can only do rotations around X, Y, or Z axis right now")

    def validate_control_qids(self, qid1, qid2):
        if qid1 not in self.qubitReg:
            raise quantumError("No such qubit to act as a control qubit")

        if qid2 not in self.qubitReg:
            raise quantumError("No such qubit to act as a target qubit")

        if qid1 == qid2:
            raise quantumError("Control and target are equal")

    def apply_CNOT(self, qubitNum1, qubitNum2):
        """
        Applies the CNOT to the qubit with the numbers qubitNum1 and qubitNum2.
        """
        self.validate_control_qids(qubitNum1, qubitNum2)

        self.engine.mcx([qubitNum1], qubitNum2)

    def apply_CPHASE(self, qubitNum1, qubitNum2):
        """
        Applies the CPHASE to the qubit with the numbers qubitNum1 and qubitNum2.
        """
        self.validate_control_qids(qubitNum1, qubitNum2)

        self.engine.mcz([qubitNum1], qubitNum2)

    def apply_onequbit_gate(self, gate, qubitNum):
        """
        Applies a unitary gate to the specified qubit.

        Arguments:
        gate       The pyqrack gate to be applied
        qubitNum 	the number of the qubit this gate is applied to
        """
        self.validate_qid(qubitNum)

        self.engine.mtrx(gate, qubitNum)

    def apply_twoqubit_gate(self, gate, qubit1, qubit2):
        """
        Applies a unitary gate to the two specified qubits.

        Arguments:
        gate       The pyqrack gate to be applied
        qubit1 		the first qubit
        qubit2		the second qubit
        """
        raise NotImplementedError("apply_twoqubit_gate() not implemented for this backend!")

    def measure_qubit_inplace(self, qubitNum):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome. The quantum register
        is in the post-measurment state corresponding to the obtained outcome.

        Arguments:
        qubitNum	qubit to be measured
        """

        # Check we have such a qubit...
        self.validate_qid(qubitNum)

        outcome = self.engine.m(qubitNum)

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
        raise NotImplementedError("Currently you cannot replace a qubit using pyqrack as backend")

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
            self.engine = other.engine
            self.qubitReg = list(other.qubitReg)
            self.nextQid = other.nextQid
        elif other.activeQubits > 0:
            # PyQrack can internally "compose" the two engines together.
            nQubits = []
            for q in range(other.activeQubits):
                nQubits.append(self.nextQid)
                self.nextQid += 1

            self.engine.compose(other.engine, nQubits)

            # Add the qubits to the list of qubits
            self.qubitReg += nQubits

        self.activeQubits = newNum

    def absorb_parts(self, R, I, activeQ):
        """
        Absorb the qubits, given in pieces

        Arguments:
        R		real part of the qubit state as a list
        I		imaginary part as a list
        activeQ		active number of qubits
        """
        raise NotImplementedError("Currently you cannot absorb_parts() using pyqrack as backend")

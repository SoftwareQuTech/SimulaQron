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

from simulaqron.virtNode.basics import quantumEngine, quantumError, noQubitError
from simulaqron.toolbox.stabilizerStates import StabilizerState


class stabilizerEngine(quantumEngine):
    """
    Basic quantum engine which uses stabilizer formalism. Thus only Clifford operations can be performed

    Attributes:
        maxQubits:	maximum number of qubits this engine will support.
    """

    def __init__(self, node, num, maxQubits=10):
        """
        Initialize the simple engine. If no number is given for maxQubits, the assumption will be 10.
        """

        super().__init__(node=node, num=num, maxQubits=maxQubits)

        self.qubitReg = StabilizerState()

    @property
    def activeQubits(self):
        return self.qubitReg.num_qubits

    def add_fresh_qubit(self):
        """
        Add a new qubit initialized in the \|0\> state.
        """
        # Check if we are still allowed to add qubits
        if self.activeQubits >= self.maxQubits:
            raise noQubitError("No more qubits available in register.")

        num = self.activeQubits

        # Prepare a clean qubit state in |0>
        self.qubitReg.add_qubit()

        return num

    def add_qubit(self, newQubit):
        """
        Add new qubit in the state described by the array containing the generators of the stabilizer group.
        This should be in the form required by the StabilizerState class.
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
        """
        if (qubitNum + 1) > self.activeQubits:
            raise quantumError("No such qubit to remove")

        self.measure_qubit(qubitNum)

    def get_register_RI(self):
        """
        Retrieves the entire register in real and imaginary part. Twisted only likes to send real valued lists,
        not complex ones.
        Since this is in stabilizer formalism the real part will be the boolean matrix describing the generators
        and the imaginary part will be None
        """

        Re = self.qubitReg.to_array().tolist()
        Im = None

        return Re, Im

    def apply_H(self, qubitNum):
        """
        Applies a Hadamard gate to the qubits with number qubitNum.
        """
        self.qubitReg.apply_H(qubitNum)

    def apply_K(self, qubitNum):
        """
        Applies a K gate to the qubits with number qubitNum. Maps computational basis to Y eigenbasis.
        """
        self.qubitReg.apply_K(qubitNum)

    def apply_X(self, qubitNum):
        """
        Applies a X gate to the qubits with number qubitNum.
        """

        self.qubitReg.apply_X(qubitNum)

    def apply_Z(self, qubitNum):
        """
        Applies a Z gate to the qubits with number qubitNum.
        """

        self.qubitReg.apply_Z(qubitNum)

    def apply_Y(self, qubitNum):
        """
        Applies a Y gate to the qubits with number qubitNum.
        """

        self.qubitReg.apply_Y(qubitNum)

    def apply_T(self, qubitNum):
        """
        Applies a T gate to the qubits with number qubitNum.
        """
        raise AttributeError("Cannot apply T gate in stabilizer formalism")

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
        raise AttributeError("Cannot apply arbitrary rotation gate in stabilizer formalism")

    def apply_CNOT(self, qubitNum1, qubitNum2):
        """
        Applies the CNOT to the qubit with the numbers qubitNum1 and qubitNum2.
        """
        self.qubitReg.apply_CNOT(qubitNum1, qubitNum2)

    def apply_CPHASE(self, qubitNum1, qubitNum2):
        """
        Applies the CPHASE to the qubit with the numbers qubitNum1 and qubitNum2.
        """

        self.qubitReg.apply_CZ(qubitNum1, qubitNum2)

    def apply_onequbit_gate(self, gate, qubitNum):
        """
        Applies a unitary gate to the specified qubit.

        Arguments:
        gate       The project Q gate to be applied
        qubitNum 	the number of the qubit this gate is applied to
        """

        raise AttributeError("Cannot apply arbitrary one qubit gate in stabilizer formalism")

    def apply_twoqubit_gate(self, gate, qubit1, qubit2):
        """
        Applies a unitary gate to the two specified qubits.

        Arguments:
        gate       The project Q gate to be applied
        qubit1 		the first qubit
        qubit2		the second qubit
        """
        raise AttributeError("Cannot apply arbitrary two qubit gate in stabilizer formalism")

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

        outcome = self.qubitReg.measure(qubitNum, inplace=True)

        # return measurement outcome
        return outcome

    def measure_qubit(self, qubitNum):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome and deletes the qubit.

        Arguments:
        qubitNum	qubit to be measured
        """
        outcome = self.qubitReg.measure(qubitNum, inplace=False)

        return outcome

    def replace_qubit(self, qubitNum, state):
        """
        Replaces the qubit at position qubitNum with the one given by state.
        """
        raise NotImplementedError("Currently you cannot replace a qubit using stabilizer formalism")

    def absorb(self, other):
        """
        Absorb the qubits from the other engine into this one. This is done by tensoring the state at the end.
        """

        # Check whether there is space
        newNum = self.activeQubits + other.activeQubits
        if newNum > self.maxQubits:
            raise quantumError("Cannot merge: qubits exceed the maximum available.\n")

        self.qubitReg = self.qubitReg.tensor_product(other.qubitReg)

    def absorb_parts(self, R, I, activeQ):
        """
        Absorb the qubits, given in pieces

        Arguments:
        R		The array describing the stabilizer state (from StabilizerState.to_array)
        I		Unused
        activeQ		active number of qubits
        """
        # Check whether there is space
        newNum = self.activeQubits + activeQ
        if newNum > self.maxQubits:
            raise quantumError("Cannot merge: qubits exceed the maximum available.\n")

        self.qubitReg = self.qubitReg.tensor_product(StabilizerState(R))

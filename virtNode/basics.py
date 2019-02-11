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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import abc
from twisted.spread import pb


class quantumError(pb.Error):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class noQubitError(quantumError):
    pass


class virtNetError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class quantumEngine(pb.Referenceable):
    """
    Basic quantum engine. Abstract class meant to be subclassed to implement different simulation backends.

    Attributes:
        Arguments
        node		node this register is started from
        num		number of this register
        maxQubits	maximum number of qubits this register supports
    """

    def __init__(self, node, num, maxQubits=10):
        """
        Initialize the simple engine. If no number is given for maxQubits, the assumption will be 10.
        """

        self.maxQubits = maxQubits

        # Each register has a number, this may be used be the ``outside`` application
        # using this simulator
        self.num = num

        # Node that actually simulates this register
        self.simNode = node

    @abc.abstractmethod
    def add_fresh_qubit(self):
        """
        Add a new qubit initialized in the \|0\> state.
        :return: The qubit number
        :rtype: int
        """
        pass

    @abc.abstractmethod
    def add_qubit(self, newQubit):
        """
        Add new qubit in the state described by the density matrix newQubit
        :return: The qubit number
        :rtype: int
        """
        pass

    @abc.abstractmethod
    def remove_qubit(self, qubitNum):
        """
        Removes the qubit with the desired number qubitNum
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def get_register_RI(self):
        """
        Retrieves the entire register in real and imaginary parts and returns the result as a
        list. Twisted only likes to send real valued lists, not complex ones.
        :return: The real and imaginary parts of a qubit state
        :rtype: tuple
        """
        pass

    @abc.abstractmethod
    def apply_H(self, qubitNum):
        """
        Applies a Hadamard gate to the qubits with number qubitNum.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def apply_K(self, qubitNum):
        """
        Applies a K gate to the qubits with number qubitNum. Maps computational basis to Y eigenbasis.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def apply_X(self, qubitNum):
        """
        Applies a X gate to the qubits with number qubitNum.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def apply_Z(self, qubitNum):
        """
        Applies a Z gate to the qubits with number qubitNum.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def apply_Y(self, qubitNum):
        """
        Applies a Y gate to the qubits with number qubitNum.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def apply_T(self, qubitNum):
        """
        Applies a T gate to the qubits with number qubitNum.
        :rtype: None
        """
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def apply_CNOT(self, qubitNum1, qubitNum2):
        """
        Applies the CNOT to the qubit with the numbers qubitNum1 and qubitNum2.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def apply_CPHASE(self, qubitNum1, qubitNum2):
        """
        Applies the CPHASE to the qubit with the numbers qubitNum1 and qubitNum2.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def apply_onequbit_gate(self, gateU, qubitNum):
        """
        Applies a unitary gate to the specified qubit.

        Arguments:
        gateU   	unitary to apply as Qobj
        qubitNum 	the number of the qubit this gate is applied to
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def apply_twoqubit_gate(self, gateU, qubit1, qubit2):
        """
        Applies a unitary gate to the two specified qubits.

        Arguments:
        gateU		unitary to apply as Qobj
        qubit1 		the first qubit
        qubit2		the second qubit
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def measure_qubit_inplace(self, qubitNum):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome. The quantum register
        is in the post-measurment state corresponding to the obtained outcome.

        Arguments:
        qubitNum	qubit to be measured
        :return: The meaurement outcome
        :rtype: int
        """
        pass

    @abc.abstractmethod
    def measure_qubit(self, qubitNum):
        """
        Measures the desired qubit in the standard basis. This returns the classical outcome and deletes the qubit.

        Arguments:
        qubitNum	qubit to be measured
        :return: The meaurement outcome
        :rtype: int
        """
        pass

    @abc.abstractmethod
    def replace_qubit(self, qubitNum, state):
        """
        Replaces the qubit at position qubitNum with the one given by state.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def absorb(self, other):
        """
        Absorb the qubits from the other engine into this one. This is done by tensoring the state at the end.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def absorb_parts(self, R, I, activeQ):
        """
        Absorb the qubits, given in pieces

        Arguments:
        R		real part of the qubit state as a list
        I		imaginary part as a list
        activeQ		active number of qubits
        :rtype: None
        """
        pass

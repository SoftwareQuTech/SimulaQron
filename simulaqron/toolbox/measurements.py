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

from cqc.pythonLib import qubit


def parity_meas(qubits, bases, node, negative=False):
    """
    Performs a parity measurement on the provided qubits in the Pauli bases specified by 'bases'.
    'bases' should be a string with letters in "IXYZ" and have the same length as the number of qubits provided.
    If 'negative' is true the measurement outcome is flipped.
    If more than one letter of 'bases' is not identity, then an ancilla qubit will be used, which is created using the
    provided 'node'.

    :param qubits: List of qubits to be measured.
    :type qubits: list of :obj: `cqc.pythonLib.qubit`
    :param bases: String specifying the Pauli-bases of the measurement. Example bases="IXY" for three qubits.
    :type bases: str
    :param node: The node storing the qubits. Used for creating an ancilla qubit.
    :type node: :obj: `cqc.pythonLib.CQCConnection`
    :param negative: If the measurement outcome should be flipped or not.
    :type negative: bool
    :return: The measurement outcome 0 or 1, where 0 correspond to the +1 eigenvalue of the measurement operator.
    """

    if not (len(qubits) == len(bases)):
        raise ValueError("Number of bases needs to be the number of qubits.")
    if not all([(B in "IXYZ") for B in bases]):
        raise ValueError("All elements of bases need to be in 'IXYZ'.")

    num_qubits = len(qubits)

    flip_basis = ["I"] * num_qubits
    non_identity_bases = []

    # Check if we need to flip the bases of the qubits
    for i in range(len(bases)):
        B = bases[i]
        if B == "X":
            flip_basis[i] = "H"
            non_identity_bases.append(i)
        elif B == "Y":
            flip_basis[i] = "K"
            non_identity_bases.append(i)
        elif B == "Z":
            non_identity_bases.append(i)
        else:
            pass

    if len(non_identity_bases) == 0:
        # Trivial measurement
        m = 0

    elif len(non_identity_bases) == 1:
        # Single_qubit measurement
        q_index = non_identity_bases[0]
        q = qubits[q_index]

        # Flip to correct basis
        if flip_basis[q_index] == "H":
            q.H()
        if flip_basis[q_index] == "K":
            q.K()

        m = q.measure(inplace=True)

        # Flip the qubit back
        if flip_basis[q_index] == "H":
            q.H()
        if flip_basis[q_index] == "K":
            q.K()

    else:
        # Parity measurement, ancilla needed

        # Initialize ancilla qubit
        anc = qubit(node)

        # Flip to correct basis
        for i in range(len(bases)):
            if flip_basis[i] == "H":
                qubits[i].H()
            if flip_basis[i] == "K":
                qubits[i].K()

                # Transfer parity information to ancilla qubit
        for i in non_identity_bases:
            qubits[i].cnot(anc)

            # Measure ancilla qubit
        m = anc.measure()

        # Flip to correct basis
        for i in range(len(bases)):
            if flip_basis[i] == "H":
                qubits[i].H()
            if flip_basis[i] == "K":
                qubits[i].K()
    if negative:
        return (m + 1) % 2
    else:
        return m

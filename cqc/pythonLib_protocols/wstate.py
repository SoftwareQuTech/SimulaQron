from cqc.pythonLib import qubit
import numpy as np


def initialize_Qubit_register(num_qubit, Owner):

    """
    Initialize quantum registers. Multiple qubits are stored and returned as an array.
    Returns an array of initialized qubits.

    :param num_qubit: Number of qubits to initialize
    :param Owner: The owner of the qubit / CQCConnection.
    """

    qubits = []
    for x in range(0, num_qubit):
        one_more_qubit = qubit(Owner)
        qubits.append(one_more_qubit)
    return qubits


def create_Nqubit_Wstate(num_qubit, Owner):
    """
    Initializes multiple qubits, and entangles them as W state.
    Returns an array of qubits (W state).

    :param num_qubit: Number of qubits to initialize for the W state
    :param Owner: The owner of the qubit / CQCConnection.
    """
    qubits = initialize_Qubit_register(num_qubit, Owner)
    num_qubit = len(qubits)
    qubits[0].X()
    for x in range(1, num_qubit):
        qubit1 = qubits[x - 1]
        qubit2 = qubits[x]
        ControlledG(qubit1, qubit2, num_qubit - x + 1)
    return qubits


def ControlledG(controlled_qubit, target_qubit, index):
    """
    Controlled-G(p)/Controlled-Ry(θ) gate

    :param contolled_qubit: Controlled qubit for this operation
    :param target_qubit: Target qubit for this operation
    :param index: Index to calculate the p value. The p value is an integer between 0 and 1.
    """
    p = np.sqrt(1 - 1 / index)
    x = int(np.arcsin(p) * 256 / (2 * np.pi))
    controlled_qubit.cnot(target_qubit)
    target_qubit.rot_Y(256 - x)
    controlled_qubit.cnot(target_qubit)
    target_qubit.rot_Y(x)
    target_qubit.cnot(controlled_qubit)

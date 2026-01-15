import numpy as np


def assemble_qubit(realM: np.ndarray, imagM: np.ndarray) -> np.ndarray:
    """
    Reconstitute the qubit as array from its real and imaginary components given as a list.

    :param realM: Real component of the qubit.
    :type realM: np.ndarray
    :param imagM: Imaginary component of the qubit.
    :type imagM: np.ndarray
    :return: Assembled qubit as vector of complex numbers.
    :rtype: np.array
    """
    # We need this since Twisted PB does not support sending complex valued object natively.
    M = realM
    for s in range(len(M)):
        for t in range(len(M)):
            M[s][t] = realM[s][t] + 1j * imagM[s][t]

    return M
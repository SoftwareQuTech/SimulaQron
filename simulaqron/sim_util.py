import numpy as np
import logging
from netqasm.sdk import Qubit

from simulaqron.sdk import SimulaQronConnection

logger = logging.getLogger("sim_util")


def get_qubit_state(qubit: Qubit, reduced_dm: bool = True) -> np.ndarray:
    """Get the state of the qubit, only possible in simulation and can be used for debugging.

    .. note:: The function gets the *current* state of the qubit(s). So make sure the subroutine
              is flushed before calling the method.

    :param qubit: The qubit(s) to get the state of.
    :type qubit: Qubit
    :param reduced_dm: Unused; declared to keep compatibility with other simulation engines
    :type reduced_dm: bool
    :return: The state as a density matrix.
    :rtype: np.array
    """
    # Since the qubit state data is maintained by the virtual node, we need to
    # find a way to "bypass" the QNodeOS layer and retrieve the qubit state from
    # the VirtualNode layer

    # Idea for implementing this primitive:
    # - We get the connection associated with the given qubit
    # - We invoke a method on the connection, which sends a particular message to
    #   the SimulaQron QNodeOS layer.
    # - The SimulaQron QNodeOS layer needs to recognize the message, and invoke a
    #   proper method on the VirtualNode layer
    # - The VirtualNode layer handles the request, and (somehow, depending on the
    #   underlying qubit simulation engine) retrieves the state of the qubit
    # - The VirtualNode layers sends the response back to the QNodeOS layer, which
    #   simply forwards it to the connection, and finally, here.
    assert isinstance(qubit.connection, SimulaQronConnection)
    connection: SimulaQronConnection = qubit.connection
    # Retrieve the app_id and the qubit_id to pass in the message
    return np.array(connection.get_qubit_state(connection.app_id, qubit.qubit_id))

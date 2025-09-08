from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk import Qubit

from simulaqron.sdk import SimulaQronConnection

logger = get_netqasm_logger("sim_util")


def get_qubit_state(qubit: Qubit, reduced_dm: bool = True):
    """Currently we cannot get the qubit in SimulaQron, just return None"""
    logger.warning("Cannot get the qubit state in SimulaQron")
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
    # Maybe the app_id is not necessary?
    connection.get_qubit_state(connection.app_id, qubit.qubit_id)
    return None

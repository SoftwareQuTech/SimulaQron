from netqasm.logging.glob import get_netqasm_logger

logger = get_netqasm_logger("sim_util")


def get_qubit_state(qubit, reduced_dm=True):
    """Currenlty we cannot get the qubit in SimulaQron, just return None"""
    logger.warning("Cannot get the qubit state in SimulaQron")
    return None

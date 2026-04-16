class SimUnsupportedError(RuntimeError):
    """
    Raised when the SimulaQron does not support the configured simulation backend.
    Check :py:class:`NodeConfigType` enum for valid values of the simulation backend.
    """
    pass

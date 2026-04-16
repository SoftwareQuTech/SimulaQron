from netqasm.sdk.classical_communication.broadcast_channel import BroadcastChannelBySockets

from .socket import Socket


class BroadcastChannel(BroadcastChannelBySockets):
    """
    Implement a Broadcast channel over sockets

    .. warning:: This class is candidate to be deleted. Test and delete if possible!
    """
    _socket_class = Socket

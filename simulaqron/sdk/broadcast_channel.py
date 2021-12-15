from netqasm.sdk.classical_communication.broadcast_channel import BroadcastChannelBySockets
from .socket import Socket


class BroadcastChannel(BroadcastChannelBySockets):
    _socket_class = Socket

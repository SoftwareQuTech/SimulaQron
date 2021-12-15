from twisted.internet.defer import inlineCallbacks
from netqasm.backend.messages import MsgDoneMessage
from netqasm.backend.qnodeos import QNodeController

from simulaqron.netqasm_backend.executioner import VanillaSimulaQronExecutioner


class SubroutineHandler(QNodeController):
    def __init__(self, factory, instr_log_dir=None, flavour=None):
        super().__init__(factory.name, instr_log_dir=instr_log_dir, flavour=flavour)

        self.factory = factory

        # Give a way for the executioner to return messages
        self._executor.add_return_msg_func(self._return_msg)

        # Give the executioner a handle to the factory
        self._executor.add_factory(self.factory)

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, protocol):
        self._protocol = protocol

    @inlineCallbacks
    def handle_netqasm_message(self, msg_id, msg):
        yield from super().handle_netqasm_message(
            msg_id=msg_id,
            msg=msg,
        )

    @classmethod
    def _get_executor_class(cls, flavour=None):
        return VanillaSimulaQronExecutioner

    def _mark_message_finished(self, msg_id, msg):
        ret_msg = MsgDoneMessage(msg_id=msg_id)
        self._return_msg(msg=ret_msg)

    def stop(self):
        self.factory.stop()

    def _return_msg(self, msg):
        """Return a message to the host"""
        assert self._protocol is not None, "Seems protocol of handler has not yet been set"
        self._logger.debug(f"sending message {msg} to host")
        self.protocol._return_msg(msg=bytes(msg))

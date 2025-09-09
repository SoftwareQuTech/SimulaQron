from typing import Optional, Dict, Callable, Generator, Any, List

from netqasm.backend.messages import MsgDoneMessage, Message, MessageType
from netqasm.backend.qnodeos import QNodeController
from netqasm.lang.instr import Flavour
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol

import simulaqron.settings as settings
from simulaqron.netqasm_backend.executioner import VanillaSimulaQronExecutioner
from simulaqron.sdk.connection import (NewMessageType, GetQubitStateMessage,
                                       ReturnQubitStateMessage)


class SubroutineHandler(QNodeController):
    def __init__(self, factory: "NetQASMFactory", instr_log_dir: Optional[str] = None,
                 flavour: Optional[Flavour] = None):
        super().__init__(factory.name, instr_log_dir=instr_log_dir, flavour=flavour)

        self.factory = factory

        # Give a way for the executioner to return messages
        self._executor.add_return_msg_func(self._return_msg)

        # Give the executioner a handle to the factory
        self._executor.add_factory(self.factory)

    @property
    def protocol(self) -> Protocol:
        return self._protocol

    @protocol.setter
    def protocol(self, protocol: Protocol):
        self._protocol = protocol

    @inlineCallbacks
    def handle_netqasm_message(self, msg_id: int, msg: Message):
        yield from super().handle_netqasm_message(
            msg_id=msg_id,
            msg=msg,
        )

    def _handle_get_qubit_state(self, get_quibit_state_msg: GetQubitStateMessage) -> Generator[Any, None, None]:
        assert isinstance(self._executor, VanillaSimulaQronExecutioner)
        casted_executor: VanillaSimulaQronExecutioner = self._executor
        # The ProjectQ backend also returns an unused mapping; we need to fix that
        if settings.simulaqron_settings.sim_backend == settings.SimBackend.PROJECTQ.value:
            _, [realvec, imagvec] = yield casted_executor.get_qubit_state(get_quibit_state_msg.qubit_id)
        else:
            realvec, imagvec = yield casted_executor.get_qubit_state(get_quibit_state_msg.qubit_id)
        # Return a message to the connection object
        self._return_qubit_state(get_quibit_state_msg.qubit_id, realvec, imagvec)

    def _return_qubit_state(self, qubit_id: int, real_part: List[float], imag_part: List[float]):
        qubit_state_message = ReturnQubitStateMessage(qubit_id, real_part, imag_part)
        self._return_msg(msg=qubit_state_message)

    # We override the _get_message_handlers method so we can also handle the "get qubit state" message
    def _get_message_handlers(self) -> Dict[NewMessageType | MessageType, Callable]:
        return {
            MessageType.SIGNAL: self._handle_signal,
            MessageType.SUBROUTINE: self._handle_subroutine,
            MessageType.INIT_NEW_APP: self._handle_init_new_app,
            MessageType.STOP_APP: self._handle_stop_app,
            MessageType.OPEN_EPR_SOCKET: self._handle_open_epr_socket,
            NewMessageType.GET_QUBIT_STATE: self._handle_get_qubit_state
        }

    @classmethod
    def _get_executor_class(cls, flavour: Optional[Flavour] = None):
        return VanillaSimulaQronExecutioner

    def _mark_message_finished(self, msg_id: int, msg: Message):
        ret_msg = MsgDoneMessage(msg_id=msg_id)
        self._return_msg(msg=ret_msg)

    def stop(self):
        self.factory.stop()

    def _return_msg(self, msg: Message):
        """Return a message to the host"""
        assert self._protocol is not None, "Seems protocol of handler has not yet been set"
        self._logger.debug("sending message %s to host", msg)
        self.protocol._return_msg(msg=bytes(msg))

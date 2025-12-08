import logging
import sys

from typing import Optional, Dict, Callable, Generator, Any, List, Type

from netqasm.backend.executor import Executor
from netqasm.backend.messages import MsgDoneMessage, Message, MessageType
from netqasm.backend.qnodeos import QNodeController
from netqasm.lang.instr import Flavour
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol

from simulaqron.netqasm_backend.executioner import VanillaSimulaQronExecutioner
from simulaqron.sdk.connection import (NewMessageType, GetQubitStateMessage,
                                       ReturnQubitStateMessage)
from simulaqron.settings import simulaqron_settings


class SubroutineHandler(QNodeController):
    def __init__(self, factory: "NetQASMFactory", instr_log_dir: Optional[str] = None,  # noqa: F821
                 flavour: Optional[Flavour] = None):
        super().__init__(factory.name, instr_log_dir=instr_log_dir, flavour=flavour)

        self.factory = factory
        self._logger = logging.getLogger("QnodeController")

        # Force configure root logger with a handler, ensure our log output to this file
        # will allow us to trace back exactly where it came from in the codebase
        logging.basicConfig(
            format="%(asctime)s:%(levelname)s:%(name)s:%(filename)s:%(lineno)d:%(message)s",
            level=simulaqron_settings.log_level,
            force=True,
            stream=sys.stdout  # send logs to the standard output, we set this earlier to be in /tmp
        )

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
        """
        Handle incoming NetQASM messages by bridging two async models.
    
        NetQASM's executor uses Python generators (yield from) while SimulaQron
        uses Twisted deferreds (@inlineCallbacks). This method bridges them by:
        1. Running the parent's generator manually
        2. Detecting whether each yielded item is a Twisted Deferred or a nested generator
        3. For Deferreds: yielding to Twisted's reactor to await completion
        4. For nested generators: consuming them fully and capturing their return value
    
        Without this bridge, nested generator return values (like physical_address
        from _instr_qalloc) would be lost, causing None to propagate through the system.
        This is also what caused the tests to fail, and probably other random weird things.
        """
        print(f"DEBUG handle_netqasm_message: msg_id={msg_id}", flush=True)
        gen = super().handle_netqasm_message(
            msg_id=msg_id,
            msg=msg,
        )

        # The following is a bug fix to properly wait for twisted deferreds
      
        try:
            result = None
            iteration = 0
            while True:
                iteration = iteration + 1
                item = gen.send(result)
                if hasattr(item, 'addCallback'):  # Deferred
                    result = yield item
                elif hasattr(item, '__next__'):  # Nested generator - consume it
                    nested_result = None
                    try:
                        while True:
                            nested_item = item.send(nested_result)
                            if hasattr(nested_item, 'addCallback'):
                                nested_result = yield nested_item
                            else:
                                nested_result = None
                    except StopIteration as e:
                        result = e.value  # Get the return value from the generator
                else:
                    result = None
        except StopIteration:
            pass

    def _handle_get_qubit_state(self, get_quibit_state_msg: GetQubitStateMessage) -> Generator[Any, None, None]:
        assert isinstance(self._executor, VanillaSimulaQronExecutioner)
        casted_executor: VanillaSimulaQronExecutioner = self._executor
        # The ProjectQ backend also returns an unused mapping; we need to fix that
        realvec, imagvec = yield from casted_executor.get_qubit_state(get_quibit_state_msg.qubit_id)
        # Return a message to the connection object
        self._return_qubit_state(get_quibit_state_msg.qubit_id, realvec, imagvec)

    def _return_qubit_state(self, qubit_id: int, real_part: List[List[float]], imag_part: List[List[float]]):
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
    def _get_executor_class(cls, flavour: Optional[Flavour] = None) -> Type[Executor]:
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

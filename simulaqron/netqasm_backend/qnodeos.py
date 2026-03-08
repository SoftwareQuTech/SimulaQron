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
        """
        Class that handles the NetQASM messages and bridges the NetQASM with the SimulaQron world.

        The main responsibility of this class is to "transform" the native python generators (used
        by the NetQASM library) into twisted ``Deferred`` s.

        Each time the QNodeOS Server (specifically, the NetQASMProtocol instance) receives and correctly
        parses a NetQASM message (e.g. a subroutine), it will be delegated to this class for further
        processing.

        The main entry point that process the message is the :py:meth:`handle_netqasm_message` method.

        :param factory: The :py:class:`NetQASMFactory` object.
        :type factory: NetQASMFactory
        :param instr_log_dir: Directory used to write log files to.
        :type instr_log_dir: str | None
        :param flavour: NetQASM flavour to use.
        :type flavour: Flavour | None
        """
        super().__init__(factory.name, instr_log_dir=instr_log_dir, flavour=flavour)

        self.factory = factory
        self._logger = logging.getLogger("QnodeController")

        # NOTE: Commented out because basicConfig(force=True) clobbers the root logger's
        # handlers on every new connection, silently destroying any logging config set up
        # at startup. If log output goes missing mid-run, this was the culprit.
        # If you need to configure logging, do it once at process startup (e.g. in run.py),
        # not here.
        # logging.basicConfig(
        #     format="%(asctime)s:%(levelname)s:%(name)s:%(filename)s:%(lineno)d:%(message)s",
        #     level=simulaqron_settings.log_level,
        #     force=True,
        #     stream=sys.stdout  # send logs to the standard output, we set this earlier to be in /tmp
        # )

        # Give a way for the executioner to return messages
        self._executor.add_return_msg_func(self._return_msg)

        # Give the executioner a handle to the factory
        self._executor.add_factory(self.factory)

    @property
    def protocol(self) -> Protocol:
        """Returns the :py:class:`NetQASMProtocol` object associated with this routine Handler."""
        return self._protocol

    @protocol.setter
    def protocol(self, protocol: Protocol):
        """Sets the :py:class:`NetQASMProtocol` object associated with this routine Handler."""
        self._protocol = protocol

    @inlineCallbacks
    def handle_netqasm_message(self, msg_id: int, msg: Message):
        """
        Handle incoming NetQASM messages by bridging two async models.
    
        NetQASM's executor uses Python generators (yield from) while SimulaQron
        uses Twisted deferred's (@inlineCallbacks). This method bridges them by:
        1. Running the parent's generator manually
        2. Detecting whether each yielded item is a Twisted Deferred or a nested generator
        3. For Deferred's: yielding to Twisted's reactor to await completion
        4. For nested generators: consuming them fully and capturing their return value
    
        Without this bridge, nested generator return values (like physical_address
        from _instr_qalloc) would be lost, causing None to propagate through the system.
        This is also what caused the tests to fail, and probably other random weird things.

        :param msg_id: The id of the message to process.
        :type msg_id: int
        :param msg: The message to process.
        :type msg: Message
        """
        # Let the executioner know which subroutine we're processing so that any
        # RichErrorMessage it sends back carries the correct msg_id for the client
        # to unblock its _wait_for_done loop.
        self._executor._current_msg_id = msg_id

        gen = super().handle_netqasm_message(
            msg_id=msg_id,
            msg=msg,
        )

        # Bridge between two async models:
        # - NetQASM's executor uses Python generators (yield from)
        # - SimulaQron uses Twisted deferreds (@inlineCallbacks)
        #
        # We manually drive the netqasm generator, detecting whether each
        # yielded item is a Twisted Deferred (wait for it) or a nested
        # generator (consume it manually, propagating its return value back).
        #
        # The gen.throw() call below is critical: when a nested generator
        # (e.g. super()._instr_qalloc) raises an exception, we must re-throw
        # it into the outer generator so netqasm's try/except in
        # _execute_commands can catch it and call _handle_command_exception,
        # which sends RichErrorMessage back to the client.  Without this,
        # the exception escapes the runner, _handle_command_exception never
        # runs, and the client hangs waiting for a reply that never comes.
        result = None
        while True:
            try:
                item = gen.send(result)
            except StopIteration:
                break  # generator finished normally

            if hasattr(item, 'addCallback'):  # Twisted Deferred
                result = yield item
            elif hasattr(item, '__next__'):  # Nested generator — consume manually
                nested_result = None
                try:
                    while True:
                        nested_item = item.send(nested_result)
                        if hasattr(nested_item, 'addCallback'):
                            nested_result = yield nested_item
                        else:
                            nested_result = None
                except StopIteration as e:
                    result = e.value  # propagate return value back to outer gen
                except Exception as e:
                    # Nested generator raised (e.g. "virtual address outside unit module").
                    # Re-throw into the outer generator so netqasm can handle it.
                    try:
                        item2 = gen.throw(type(e), e)
                        # Outer generator caught the exception and yielded again —
                        # process item2 exactly like any other yielded item.
                        result = None
                        if hasattr(item2, 'addCallback'):
                            result = yield item2
                        elif hasattr(item2, '__next__'):
                            nested_result2 = None
                            try:
                                while True:
                                    ni2 = item2.send(nested_result2)
                                    if hasattr(ni2, 'addCallback'):
                                        nested_result2 = yield ni2
                                    else:
                                        nested_result2 = None
                            except StopIteration as se2:
                                result = se2.value
                    except StopIteration:
                        break  # outer generator finished after handling the error
            else:
                result = None

    def _handle_get_qubit_state(self, get_qubit_state_msg: GetQubitStateMessage) -> Generator[Any, None, None]:
        assert isinstance(self._executor, VanillaSimulaQronExecutioner)
        casted_executor: VanillaSimulaQronExecutioner = self._executor
        # The ProjectQ backend also returns an unused mapping; we need to fix that
        realvec, imagvec = yield from casted_executor.get_qubit_state(get_qubit_state_msg.qubit_id)
        # Return a message to the connection object
        self._return_qubit_state(get_qubit_state_msg.qubit_id, realvec, imagvec)

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
        """
        Stops this instance of the SubroutineHandler.
        """
        self.factory.stop()

    def _return_msg(self, msg: Message):
        """
        Returns (by sending it back to the application server) a message to the host

        :param msg: The message to return.
        :type msg: Message
        """
        assert self._protocol is not None, "Seems protocol of handler has not yet been set"
        self._logger.debug("sending message %s to host", msg)
        self.protocol._return_msg(msg=bytes(msg))

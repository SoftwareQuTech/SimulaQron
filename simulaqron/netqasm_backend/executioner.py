import time

from twisted.internet.defer import inlineCallbacks
from twisted.spread.pb import RemoteError

from netqasm.executioner import Executioner
from netqasm import instructions
from simulaqron.sdk.messages import ErrorMessage, ErrorCode, ReturnRegMessage, ReturnArrayMessage
from simulaqron.virtual_node.basics import quantumError, noQubitError


class UnknownQubitError(RuntimeError):
    pass


class VanillaSimulaQronExecutioner(Executioner):

    SIMULAQRON_OPS = {
        instructions.vanilla.GateXInstruction : "apply_X",
        instructions.vanilla.GateYInstruction : "apply_Y",
        instructions.vanilla.GateZInstruction : "apply_Z",
        instructions.vanilla.GateHInstruction : "apply_H",
        instructions.vanilla.GateSInstruction : "apply_S",
        instructions.vanilla.GateKInstruction : "apply_K",
        instructions.vanilla.GateTInstruction : "apply_T",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._return_msg_func = None
        self._factory = None

    @property
    def factory(self):
        return self._factory

    @staticmethod
    def get_error_class(remote_err):
        """
        This is a function to get the error class of a remote thrown error when using callRemote.
        :param remote_err: :obj:`twisted.spread.pb.RemoteError`
        :return: class
        """
        # Get name of remote error
        error_name = remote_err.remoteType.split(b".")[-1].decode()

        # Get class of remote error
        error_class = eval(error_name)

        return error_class

    def add_return_msg_func(self, func):
        self._return_msg_func = func

    def add_factory(self, factory):
        self._factory = factory

    def _return_msg(self, msg):
        if self._return_msg_func is None:
            raise RuntimeError("Cannot return msg since no function is set")
        self._return_msg_func(msg=msg)

    # def _instr_qalloc(self, subroutine_id, instr):
    def _allocate_physical_qubit(self, subroutine_id, virtual_address, physical_address=None):
        physical_address = super()._allocate_physical_qubit(
            subroutine_id=subroutine_id,
            virtual_address=virtual_address,
            physical_address=physical_address,
        )
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        # TODO inline callbacks?
        # yield self.cmd_new(app_id=app_id, physical_address=physical_address)
        yield self.cmd_new(app_id=app_id, physical_address=physical_address)
        print("continuing after cmd_new")

    @inlineCallbacks
    def cmd_new(self, app_id, physical_address):
        """
        Request a new qubit. Since we don't need it, this python CQC just provides very crude timing information.
        (return_q_id is used internally)
        (ignore_max_qubits is used internally to ignore the check of number of virtual qubits at the node
        such that the node can temporarily create a qubit for EPR creation.)
        """
        try:
            print("cmd_new")
            self.factory._lock.acquire()
            try:
                virt = yield self.factory.virtRoot.callRemote("new_qubit")
                succ = True
            except RemoteError as remote_err:
                error_class = self.get_error_class(remote_err)
                succ = False
                if error_class == noQubitError:
                    self._logger.error("Out of simulated qubits in register or virtual qubits in node")
                    self._return_msg(msg=ErrorMessage(err_code=ErrorCode.NO_QUBIT))
                elif error_class == quantumError:
                    self._logger.error("Unknown quantum error occurred when trying to create new qubit.")
                    self._return_msg(msg=ErrorMessage(err_code=ErrorCode.GENERAL))
                else:
                    self._logger.error(
                        f"Got the following unexpected error when trying to create new qubit: {remote_err}"
                    )
                    self._return_msg(msg=ErrorMessage(err_code=ErrorCode.GENERAL))
            except Exception as err:
                succ = False
                self._logger.error(
                    f"Got the following unexpected error when trying to create new qubit: {err}"
                )
                self._return_msg(msg=ErrorMessage(err_code=ErrorCode.GENERAL))

            if succ:
                # q_id = self.new_qubit_id(app_id)
                q_id = physical_address
                q = VirtualQubitRef(q_id, int(time.time()), virt)
                self.factory.qubitList[(app_id, q_id)] = q
                print(f"qubitList after alloc: {self.factory.qubitList}")
                self._logger.info(f"{self.name}: Requested new qubit ({app_id}, {q_id})")

        finally:
            try:
                self.factory._lock.release()
            except Exception as err:
                print(err)
        print("cmd_new finished")
        return succ

    def _do_single_qubit_instr(self, instr, subroutine_id, address):
        position = self._get_position(subroutine_id=subroutine_id, address=address)
        if isinstance(instr, instructions.core.InitInstruction):
            yield self.cmd_reset(subroutine_id=subroutine_id, qubit_id=position)
        elif isinstance(instr, instructions.core.QFreeInstruction):
            yield self.cmd_reset(subroutine_id=subroutine_id, qubit_id=position, correct=False)
        else:
            simulaqron_gate = self._get_simulaqron_gate(instr=instr)
            yield self.apply_single_qubit_gate(subroutine_id=subroutine_id, gate=simulaqron_gate, qubit_id=position)

    def _do_single_qubit_rotation(self, instr, subroutine_id, address, angle):
        raise NotImplementedError

    def _do_two_qubit_instr(self, instr, subroutine_id, address1, address2):
        raise NotImplementedError

    @classmethod
    def _get_simulaqron_gate(cls, instr):
        simulaqron_gate = cls.SIMULAQRON_OPS.get(type(instr))
        if simulaqron_gate is None:
            raise TypeError(f"Unknown gate type {type(instr)}")
        return simulaqron_gate

    @inlineCallbacks
    def apply_single_qubit_gate(self, subroutine_id, gate, qubit_id):
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        try:
            virt_qubit = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id)
        except UnknownQubitError as error:
            self._logger.error(error)
            self._return_msg(msg=ErrorMessage(err_code=ErrorCode.NO_QUBIT))
            return False
        try:
            success = yield virt_qubit.callRemote(gate)
            if success is False:
                self._return_msg(msg=ErrorMessage(err_code=ErrorCode.UNSUPP))
                return False
        except Exception as e:
            raise e

        return True

    def get_virt_qubit(self, app_id, qubit_id):
        """
        Get reference to the virtual qubit reference in SimulaQron given app and qubit id, if it exists.
        If not found, send back no qubit error.
        Caution: Twisted PB does not allow references to objects to be passed back between connections.
        If you need to pass a qubit reference back to the Twisted PB on a _different_ connection,
        then use get_virt_qubit_indep below.
        """
        if not (app_id, qubit_id) in self.factory.qubitList:
            raise UnknownQubitError("CQC {}: Qubit not found".format(self.name))
        qubit = self.factory.qubitList[(app_id, qubit_id)]
        return qubit.virt

    def _do_meas(self, subroutine_id, q_address):
        position = self._get_position(subroutine_id=subroutine_id, address=q_address)
        outcome = yield self.cmd_measure(subroutine_id=subroutine_id, qubit_id=position)
        return outcome

    @inlineCallbacks
    def cmd_measure(self, subroutine_id, qubit_id):
        """
        Measure
        """
        print("cmd_measure")
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        self._logger.debug(f"{self.name}: Measuring App ID {app_id} qubit id {qubit_id}")
        try:
            virt_qubit = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id)
        except UnknownQubitError as e:
            self._logger.warning(e)
            self._return_msg(msg=ErrorMessage(err_code=ErrorCode.NO_QUBIT))
            return False
        try:
            inplace=False
            outcome = yield virt_qubit.callRemote("measure", inplace)
        except Exception as err:
            self._logger.error(
                f"{self.name}: Got the following unexpected error when trying to measure qubit {qubit_id}: {err}"
            )
            self._return_msg(msg=ErrorMessage(err_code=ErrorCode.GENERAL))
            return False

        if outcome is None:
            self._logger.warning(f"{self.name}: Measurement failed")
            self._return_msg(msg=ErrorMessage(err_code=ErrorCode.GENERAL))
            return False

        self._logger.debug(f"{self.name}: Measured outcome {outcome}")

        print(f"cmd_measure finished with outcome {outcome}")
        return outcome

    @inlineCallbacks
    def cmd_reset(self, subroutine_id, qubit_id, correct=True):
        """
        Reset Qubit to \|0\>
        """
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        self._logger.debug(f"{self.name}: Reset App ID {app_id} qubit id {qubit_id}")
        try:
            print(f"qubitList before reset: {self.factory.qubitList}")
            virt_qubit = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id)
        except UnknownQubitError as e:
            self._logger.error(e)
            self._return_msg(msg=ErrorMessage(err_code=ErrorCode.NO_QUBIT))
            return False

        try:
            outcome = yield virt_qubit.callRemote("measure", inplace=True)
        except Exception as err:
            self._logger.error(
                f"{self.name}: Got the following unexpected error when trying to reset qubit {qubit_id}: {err}"
            )
            self._return_msg(msg=ErrorMessage(err_code=ErrorCode.UNSUPP))
            return False

        # If state is |1> do correction
        if correct and outcome:
            try:
                yield virt_qubit.callRemote("apply_X")
            except Exception as err:
                self._logger.error(
                    f"{self.name}: Got the following unexpected error when trying to correct a the"
                    f" reset qubit {qubit_id}: {err}"
                )
                self._return_msg(msg=ErrorMessage(err_code=ErrorCode.UNSUPP))
                return False
        return True

    def _do_wait(self):
        raise NotImplementedError

    def _update_shared_memory(self, app_id, entry, value):
        print(app_id, entry, value)
        if isinstance(entry, instructions.operand.Register):
            print("reg")
            self._return_msg(msg=ReturnRegMessage(
                register=entry.cstruct,
                value=value,
            ))
        elif isinstance(entry, instructions.operand.Address):
            print("address")
            address = entry.address
            self._return_msg(msg=ReturnArrayMessage(
                address=address,
                values=value,
            ))
        else:
            raise TypeError(f"Cannot update shared memory with entry specified as {entry}")

    def _wait_to_handle_epr_responses(self):
        # TODO check if used
        raise NotImplementedError

    def _reserve_physical_qubit(self, physical_address):
        # TODO check if used
        raise NotImplementedError

    def _clear_phys_qubit_in_memory(self, physical_address):
        # TODO check if used
        raise NotImplementedError


class VirtualQubitRef:
    def __init__(self, qubit_id=0, timestamp=0, virt=0):
        self.qubit_id = qubit_id
        self.timestamp = timestamp
        self.virt = virt

    def __str__(self):
        return f"{self.__class__.__name__}(qubit_id={self.qubit_id}, timestamp={self.timestamp}, virt={self.virt})"

    def __repr__(self):
        return str(self)

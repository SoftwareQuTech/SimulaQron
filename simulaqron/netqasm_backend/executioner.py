import time
from enum import Enum
from collections import defaultdict

from twisted.internet.defer import inlineCallbacks

from netqasm.executioner import Executioner, EprCmdData
from netqasm import instructions
from netqasm.network_stack import BaseNetworkStack

from qlink_interface import (
    LinkLayerOKTypeK,
    LinkLayerOKTypeM,
    LinkLayerOKTypeR,
    LinkLayerErr,
    BellState,
    ReturnType,
)

from simulaqron.sdk.messages import ErrorMessage, ErrorCode, ReturnRegMessage, ReturnArrayMessage
from simulaqron.settings import simulaqron_settings
from simulaqron.general.host_config import get_node_id_from_net_config


class UnknownQubitError(RuntimeError):
    pass


class NetworkStack(BaseNetworkStack):

    def __init__(self, executioner):
        """This is just a wrapper around the executioners methods for entanglement generation
        in order to use the correct framework as used by the netqasm executioner.
        """
        self._executioner = executioner
        self._sockets = {}

    def put(self, request):
        """Handles an request to the network stack"""
        raise NotImplementedError("NetworkStack.put")

    def setup_epr_socket(self, epr_socket_id, remote_node_id, remote_epr_socket_id, timeout=1):
        """Asks the network stack to setup circuits to be used"""
        # NOTE this just records the information but does not actually set up the socket
        self._sockets[epr_socket_id] = (remote_node_id, remote_epr_socket_id)


class VanillaSimulaQronExecutioner(Executioner):

    SIMULAQRON_OPS = {
        instructions.vanilla.GateXInstruction: "apply_X",
        instructions.vanilla.GateYInstruction: "apply_Y",
        instructions.vanilla.GateZInstruction: "apply_Z",
        instructions.vanilla.GateHInstruction: "apply_H",
        instructions.vanilla.GateSInstruction: "apply_S",
        instructions.vanilla.GateKInstruction: "apply_K",
        instructions.vanilla.GateTInstruction: "apply_T",
        instructions.vanilla.CnotInstruction: "cnot_onto",
        instructions.vanilla.CphaseInstruction: "cphase_onto",
    }

    ROTATION_AXIS = {
        instructions.vanilla.RotXInstruction: (1, 0, 0),
        instructions.vanilla.RotYInstruction: (0, 1, 0),
        instructions.vanilla.RotZInstruction: (0, 0, 1),
    }

    # Dictionary storing the next unique entanglement id for each used (host_app_id,remote_node,remote_app_id)
    _next_ent_id = defaultdict(int)

    # Next create id
    _next_create_id = defaultdict(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._return_msg_func = None
        self._factory = None
        self._network_stack = NetworkStack(self)

    @property
    def factory(self):
        return self._factory

    @property
    def node_id(self):
        return get_node_id_from_net_config(self.factory.qnodeos_net, self.name)

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

    def _handle_command_exception(self, exc, prog_counter, traceback_str):
        self._logger.error(f"At line {prog_counter}: {exc}\n{traceback_str}")
        self._return_msg(msg=ErrorMessage(err_code=ErrorCode.GENERAL))

    def _return_msg(self, msg):
        if self._return_msg_func is None:
            raise RuntimeError("Cannot return msg since no function is set")
        self._return_msg_func(msg=msg)

    def _instr_qalloc(self, subroutine_id, instr: instructions.core.QAllocInstruction):
        physical_address = yield from super()._instr_qalloc(
            subroutine_id=subroutine_id,
            instr=instr,
        )
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        yield from self.cmd_new(app_id=app_id, physical_address=physical_address)

    @inlineCallbacks
    def cmd_new(self, app_id, physical_address):
        """
        Request a new qubit. Since we don't need it, this python NetQASM just provides very crude timing information.
        (return_q_id is used internally)
        (ignore_max_qubits is used internally to ignore the check of number of virtual qubits at the node
        such that the node can temporarily create a qubit for EPR creation.)
        """
        try:
            self.factory._lock.acquire()
            virt = yield self.factory.virtRoot.callRemote("new_qubit")
            q_id = physical_address
            q = VirtualQubitRef(q_id, int(time.time()), virt)
            self.factory.qubitList[(app_id, q_id)] = q
            self._logger.info(f"Requested new qubit ({app_id}, {q_id})")

        finally:
            self.factory._lock.release()

    def _do_single_qubit_instr(self, instr, subroutine_id, address):
        position = self._get_position(subroutine_id=subroutine_id, address=address)
        if isinstance(instr, instructions.core.InitInstruction):
            yield from self.cmd_reset(subroutine_id=subroutine_id, qubit_id=position)
        else:
            simulaqron_gate = self._get_simulaqron_gate(instr=instr)
            yield from self.apply_single_qubit_gate(
                subroutine_id=subroutine_id,
                gate=simulaqron_gate,
                qubit_id=position,
            )

    def _do_single_qubit_rotation(self, instr, subroutine_id, address, angle):
        position = self._get_position(subroutine_id=subroutine_id, address=address)
        axis = self._get_axis(instr=instr)
        yield from self.apply_rotation(
            subroutine_id=subroutine_id,
            axis=axis,
            angle=angle,
            qubit_id=position,
        )

    @classmethod
    def _get_axis(cls, instr):
        axis = cls.ROTATION_AXIS.get(type(instr))
        if axis is None:
            raise ValueError(f"Unknown rotation instruction {instr}")
        return axis

    @inlineCallbacks
    def apply_rotation(self, subroutine_id, axis, angle, qubit_id):
        """
        Apply a rotation of the qubit specified in cmd with an angle specified in xtra
        around the axis
        """
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        self._logger.debug(f"Applying a rotation around {axis} to App ID {app_id} qubit id {qubit_id}")
        virt_qubit = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id)
        yield virt_qubit.callRemote("apply_rotation", axis, angle)

    def _do_two_qubit_instr(self, instr, subroutine_id, address1, address2):
        positions = self._get_positions(subroutine_id=subroutine_id, addresses=[address1, address2])
        simulaqron_gate = self._get_simulaqron_gate(instr=instr)
        yield from self.apply_two_qubit_gate(
            subroutine_id=subroutine_id,
            gate=simulaqron_gate,
            qubit_id1=positions[0],
            qubit_id2=positions[1],
        )

    @inlineCallbacks
    def apply_two_qubit_gate(self, subroutine_id, gate, qubit_id1, qubit_id2):
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        self._logger.debug(f"Applying {gate} to App ID {app_id} qubit id {qubit_id1} target {qubit_id2}")
        control = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id1)
        target = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id2)
        if control == target:
            raise ValueError("target and control in two-qubit gate cannot be equal")
        yield control.callRemote(gate, target)

    @classmethod
    def _get_simulaqron_gate(cls, instr):
        simulaqron_gate = cls.SIMULAQRON_OPS.get(type(instr))
        if simulaqron_gate is None:
            raise TypeError(f"Unknown gate type {type(instr)}")
        return simulaqron_gate

    @inlineCallbacks
    def apply_single_qubit_gate(self, subroutine_id, gate, qubit_id):
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        virt_qubit = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id)
        yield virt_qubit.callRemote(gate)

    def get_virt_qubit(self, app_id, qubit_id):
        """
        Get reference to the virtual qubit reference in SimulaQron given app and qubit id, if it exists.
        If not found, send back no qubit error.
        Caution: Twisted PB does not allow references to objects to be passed back between connections.
        If you need to pass a qubit reference back to the Twisted PB on a _different_ connection,
        then use get_virt_qubit_indep below.
        """
        if not (app_id, qubit_id) in self.factory.qubitList:
            raise UnknownQubitError(f"{self.name}: Qubit {qubit_id} not found")
        qubit = self.factory.qubitList[(app_id, qubit_id)]
        return qubit.virt

    @inlineCallbacks
    def get_virt_qubit_num(self, app_id, qubit_id):
        """
        Get NUMBER (not reference!) to virtual qubit in SimulaQron specific to this connection.
        If not found, send back no qubit error.
        """
        # First let's get the general virtual qubit reference, if any
        virt = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id)
        num = yield virt.callRemote("get_virt_num")
        return num

    def _do_meas(self, subroutine_id, q_address):
        position = self._get_position(subroutine_id=subroutine_id, address=q_address)
        outcome = yield from self.cmd_measure(subroutine_id=subroutine_id, qubit_id=position)
        return outcome

    @inlineCallbacks
    def cmd_measure(self, subroutine_id, qubit_id):
        """
        Measure
        """
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        self._logger.debug(f"Measuring App ID {app_id} qubit id {qubit_id}")
        virt_qubit = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id)
        inplace = False
        outcome = yield virt_qubit.callRemote("measure", inplace)
        if outcome is None:
            raise RuntimeError("Measurement failed")
        self._logger.debug(f"Measured outcome {outcome}")
        return outcome

    @inlineCallbacks
    def cmd_reset(self, subroutine_id, qubit_id, correct=True):
        """
        Reset Qubit to \|0\>
        """
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        self._logger.debug(f"Reset App ID {app_id} qubit id {qubit_id}")
        virt_qubit = self.get_virt_qubit(app_id=app_id, qubit_id=qubit_id)
        outcome = yield virt_qubit.callRemote("measure", inplace=True)

        # If state is |1> do correction
        if correct and outcome:
            yield virt_qubit.callRemote("apply_X")

    def _do_wait(self):
        raise NotImplementedError("_do_wait")

    def _update_shared_memory(self, app_id, entry, value):
        if isinstance(entry, instructions.operand.Register):
            self._return_msg(msg=ReturnRegMessage(
                register=entry.cstruct,
                value=value,
            ))
        elif isinstance(entry, instructions.operand.Address):
            address = entry.address
            self._return_msg(msg=ReturnArrayMessage(
                address=address,
                values=value,
            ))
        else:
            raise TypeError(f"Cannot update shared memory with entry specified as {entry}")

    def _do_create_epr(
        self,
        subroutine_id,
        remote_node_id,
        epr_socket_id,
        q_array_address,
        arg_array_address,
        ent_info_array_address,
    ):
        create_request = self._get_create_request(
            subroutine_id=subroutine_id,
            remote_node_id=remote_node_id,
            epr_socket_id=epr_socket_id,
            arg_array_address=arg_array_address,
        )
        if create_request.number > 1:
            raise NotImplementedError("Currently only one pair per request is implemented")

        qubit_id_host = self._get_unused_physical_qubit()

        remote_epr_socket_id = self._get_remote_epr_socket_id(epr_socket_id=epr_socket_id)

        create_id = self._get_new_create_id(remote_node_id=remote_node_id)

        self._epr_create_requests[epr_socket_id].append(EprCmdData(
            subroutine_id=subroutine_id,
            ent_info_array_address=ent_info_array_address,
            q_array_address=q_array_address,
            request=create_request,
            tot_pairs=create_request.number,
            pairs_left=create_request.number,
        ))

        yield from self.cmd_epr(
            subroutine_id=subroutine_id,
            create_id=create_id,
            remote_node_id=remote_node_id,
            epr_socket_id=epr_socket_id,
            remote_epr_socket_id=remote_epr_socket_id,
            qubit_id=qubit_id_host,
        )

    def _do_recv_epr(
        self,
        subroutine_id,
        remote_node_id,
        epr_socket_id,
        q_array_address,
        ent_info_array_address,
    ):
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        qubit_id = self._get_unused_physical_qubit()
        num_pairs = self._get_num_pairs_from_array(
            app_id=app_id,
            ent_info_array_address=ent_info_array_address,
        )
        if num_pairs > 1:
            raise NotImplementedError("Currently only one pair per request is implemented")

        self._epr_recv_requests[epr_socket_id].append(EprCmdData(
            subroutine_id=subroutine_id,
            ent_info_array_address=ent_info_array_address,
            q_array_address=q_array_address,
            request=None,
            tot_pairs=num_pairs,
            pairs_left=num_pairs,
        ))

        yield from self.cmd_epr_recv(
            subroutine_id=subroutine_id,
            epr_socket_id=epr_socket_id,
            qubit_id=qubit_id,
        )

    def _get_remote_epr_socket_id(self, epr_socket_id):
        remote_entry = self.network_stack._sockets.get(epr_socket_id)
        if remote_entry is None:
            raise ValueError(f"Unknown EPR socket ID {epr_socket_id}")
        return remote_entry[1]

    @inlineCallbacks
    def cmd_epr(
        self,
        subroutine_id,
        create_id,
        remote_node_id,
        epr_socket_id,
        remote_epr_socket_id,
        qubit_id,
    ):
        """
        Create EPR pair with another node.
        Depending on the ips and ports this will either create an EPR-pair and send one part, or just receive.
        """
        # Get ip and port of this host
        app_id = self._get_app_id(subroutine_id=subroutine_id)

        # Get ip and port of remote host
        for remote_node_name, remote_host in self.factory.qnodeos_net.hostDict.items():
            remote_node_id = get_node_id_from_net_config(self.factory.qnodeos_net, remote_host.name)
            if remote_node_id == remote_node_id:
                break
        else:
            raise ValueError(f"Unknown node with ID {remote_node_id}")

        self._logger.debug(f"Creating EPR with {remote_node_name} on socket {epr_socket_id}")

        # Check so that it is not the same node
        if self.name == remote_node_name:
            raise ValueError("Trying to create EPR from node to itself.")

        # Check that other node is adjacent to us
        if not self.factory.is_adjacent(remote_node_name):
            raise ValueError(f"Node {self.name} is not adjacent to {remote_node_name} in the specified topology.")

        # Create the qubits
        # NOTE we don't actually allocate it since it will be sent to the other node
        # NOTE we will use negative address to not mix up with normal qubits
        second_qubit_id = -(1 + qubit_id)
        for q_id in [qubit_id, second_qubit_id]:
            yield from self.cmd_new(
                app_id=app_id,
                physical_address=q_id,
            )

        # Produce EPR-pair
        h_gate = self._get_simulaqron_gate(instr=instructions.vanilla.GateHInstruction())
        yield from self.apply_single_qubit_gate(
            subroutine_id=subroutine_id,
            gate=h_gate,
            qubit_id=qubit_id,
        )
        cnot_gate = self._get_simulaqron_gate(instr=instructions.vanilla.CnotInstruction())
        yield from self.apply_two_qubit_gate(
            subroutine_id=subroutine_id,
            gate=cnot_gate,
            qubit_id1=qubit_id,
            qubit_id2=second_qubit_id,
        )

        # Get entanglement id
        # TODO lock here?
        ent_id = self.new_ent_id(
            epr_socket_id=epr_socket_id,
            remote_node_id=remote_node_id,
            remote_epr_socket_id=remote_epr_socket_id,
        )
        # Prepare ent_info header with entanglement information
        ent_info = LinkLayerOKTypeK(
            type=ReturnType.OK_K,
            create_id=create_id,
            logical_qubit_id=qubit_id,
            directionality_flag=0,
            sequence_number=ent_id,
            # NOTE We use EPR socket ID
            purpose_id=epr_socket_id,
            remote_node_id=remote_node_id,
            goodness=1,
            goodness_time=int(time.time()),
            bell_state=BellState.PHI_PLUS,
        )

        # Send second qubit
        yield from self.send_epr_half(
            subroutine_id=subroutine_id,
            qubit_id=second_qubit_id,
            epr_socket_id=epr_socket_id,
            remote_node_name=remote_node_name,
            remote_epr_socket_id=remote_epr_socket_id,
            ent_info=ent_info,
        )

        self._handle_epr_response(response=ent_info)

    @classmethod
    def new_ent_id(cls, epr_socket_id, remote_node_id, remote_epr_socket_id):
        """
        Returns a new unique entanglement id for the specified host_app_id, remote_node and remote_app_id.
        Used by cmd_epr.
        """
        pair_id = (epr_socket_id, remote_node_id, remote_epr_socket_id)
        ent_id = cls._next_ent_id[pair_id]
        cls._next_ent_id[pair_id] += 1
        return ent_id

    @classmethod
    def _get_new_create_id(cls, remote_node_id):
        create_id = cls._next_create_id[remote_node_id]
        cls._next_create_id[remote_node_id] += 1
        return create_id

    @inlineCallbacks
    def send_epr_half(
        self,
        subroutine_id,
        qubit_id,
        epr_socket_id,
        remote_node_name,
        remote_epr_socket_id,
        ent_info
    ):
        """
        Send qubit to another node.
        """
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        # Lookup the virtual qubit from identifier
        virt_num = yield from self.get_virt_qubit_num(app_id=app_id, qubit_id=qubit_id)

        # Prepare update raw entanglement information header
        remote_ent_info = LinkLayerOKTypeK(
            type=ent_info.type,
            create_id=ent_info.create_id,
            logical_qubit_id=qubit_id,
            directionality_flag=1,
            sequence_number=ent_info.sequence_number,
            # NOTE We use EPR socket ID
            purpose_id=remote_epr_socket_id,
            remote_node_id=self.node_id,
            goodness=ent_info.goodness,
            goodness_time=ent_info.goodness_time,
            bell_state=ent_info.bell_state,
        )

        # Send instruction to transfer the qubit
        remote_ent_info = tuple(v.value if isinstance(v, Enum) else v for v in remote_ent_info)
        # remote_ent_info = tuple(remote_ent_info)
        yield self.factory.virtRoot.callRemote(
            "netqasm_send_epr_half",
            virt_num,
            remote_node_name,
            epr_socket_id,
            remote_epr_socket_id,
            remote_ent_info,
        )

        self._logger.debug(f"Sent half a EPR pair as qubit id {qubit_id} to {remote_node_name}")
        # Remove from active mapped qubits
        self.remove_qubit_id(app_id=app_id, qubit_id=qubit_id)

    @staticmethod
    def _unpack_ent_info(raw_ent_info):
        return_type_id = raw_ent_info[0]
        ent_info_class = {
            ReturnType.OK_K.value: LinkLayerOKTypeK,
            ReturnType.OK_M.value: LinkLayerOKTypeM,
            ReturnType.OK_R.value: LinkLayerOKTypeR,
            ReturnType.ERR.value: LinkLayerErr,
        }[return_type_id]
        return ent_info_class(
            ReturnType(return_type_id),
            *raw_ent_info[1:-1],
            bell_state=BellState(raw_ent_info[-1]),
        )

    @staticmethod
    def _update_qubit_id(ent_info, qubit_id):
        dct = ent_info._asdict()
        dct["logical_qubit_id"] = qubit_id
        return ent_info.__class__(**dct)

    @inlineCallbacks
    def cmd_epr_recv(self, subroutine_id, epr_socket_id, qubit_id):
        """
        Receive half of epr from another node. Block until qubit is received.
        """
        self._logger.debug(f"Asking to receive for EPR socket ID {epr_socket_id}")

        # This will block until a qubit is received.
        no_qubit = True
        virt_qubit = None
        ent_info = None
        # recv_timeout is in 100ms (for legacy reasons there are no plans to change it to seconds)
        sleep_time = simulaqron_settings.recv_retry_time
        for _ in range(int(simulaqron_settings.recv_timeout * 0.1 / sleep_time)):
            data = yield self.factory.virtRoot.callRemote("netqasm_get_epr_recv", epr_socket_id)
            if data:
                no_qubit = False
                (virt_qubit, raw_ent_info) = data
                ent_info = self._unpack_ent_info(raw_ent_info=raw_ent_info)
                ent_info = self._update_qubit_id(ent_info=ent_info, qubit_id=qubit_id)
                break
            else:
                time.sleep(sleep_time)
        if no_qubit:
            raise TimeoutError("TIMEOUT, no qubit received.")

        self._logger.debug("Qubit received for EPR socket ID {epr_socket_id}", epr_socket_id)

        # Once we have the qubit, add it to the local list and send a reply we received it. Note that we will
        # recheck whether it exists: it could have been added by another connection in the mean time
        app_id = self._get_app_id(subroutine_id=subroutine_id)
        try:
            self.factory._lock.acquire()

            if (app_id, qubit_id) in self.factory.qubitList:
                raise RuntimeError(f"Qubit with ID {qubit_id} already in use")

            q = VirtualQubitRef(qubit_id, int(time.time()), virt_qubit)
            self.factory.qubitList[(app_id, qubit_id)] = q
        finally:
            self.factory._lock.release()

        self._handle_epr_response(response=ent_info)

    def remove_qubit_id(self, app_id, qubit_id):
        self.factory.qubitList.pop((app_id, qubit_id))

    def _release_qubits(self, subroutine_id, qubit_ids):
        for qubit_id in qubit_ids:
            try:
                yield from self.cmd_reset(subroutine_id=subroutine_id, qubit_id=qubit_id, correct=False)
            except Exception as err:
                self._logger.warning("Failed to destroy qubits")
                self._logger.error(err)

    def _get_epr_socket_id(self, response):
        # NOTE we for now just use the purpose ID
        # This will in fact always be the EPR socket ID for the local node
        # See cmd_epr and send_epr_half
        return response.purpose_id

    def _get_purpose_id(self, remote_node_id, epr_socket_id):
        # NOTE this is for now since we communicate directly to link layer
        # Use the EPR socket ID for now
        return epr_socket_id

    def _wait_to_handle_epr_responses(self):
        # NOTE in simulaqron we will never need to wait since epr is handled after information is added
        # but raise an error in case this happens due to bug
        raise NotImplementedError("_wait_to_handle_epr_responses")

    def _reserve_physical_qubit(self, physical_address):
        # NOTE does not do anything, done by cmd_new instead
        pass


class VirtualQubitRef:
    def __init__(self, qubit_id=0, timestamp=0, virt=0):
        self.qubit_id = qubit_id
        self.timestamp = timestamp
        self.virt = virt

    def __str__(self):
        return f"{self.__class__.__name__}(qubit_id={self.qubit_id}, timestamp={self.timestamp}, virt={self.virt})"

    def __repr__(self):
        return str(self)

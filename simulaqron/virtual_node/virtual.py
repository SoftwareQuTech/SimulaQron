#
# Copyright (c) 2017, Stephanie Wehner and Axel Dahlberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import random
# import traceback

from collections import deque

from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, DeferredLock, Deferred, DeferredList
from twisted.internet.task import deferLater
from twisted.internet.error import ConnectionRefusedError, CannotListenError
from twisted.spread.pb import RemoteError, RemoteReference

from netqasm.logging.glob import get_netqasm_logger

from simulaqron.virtual_node.basics import quantumError, noQubitError, virtNetError
from simulaqron.virtual_node.quantum import simulatedQubit
from simulaqron.general.host_config import SocketsConfig
from simulaqron.settings import simulaqron_settings, SimBackend

if simulaqron_settings.sim_backend == SimBackend.QUTIP.value:
    from simulaqron.virtual_node.qutip_simulator import qutipEngine
elif simulaqron_settings.sim_backend == SimBackend.PROJECTQ.value:
    from simulaqron.virtual_node.project_q_simulator import projectQEngine
elif simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
    from simulaqron.virtual_node.stabilizer_simulator import stabilizerEngine
else:
    raise quantumError(f"Unknown backend {simulaqron_settings.sim_backend}")


def reraise_remote_error(self, remote_err):
    """
    This is a function re-raises the error thrown remotely
    :param remote_err: :obj:`twisted.spread.pb.RemoteError`
    :return: class
    """
    # Get name of remote error
    error_name = remote_err.remoteType.split(b".")[-1].decode()

    # Get class of remote error
    error_class = eval(error_name)

    raise error_class(str(remote_err))


@inlineCallbacks
def call_method(obj, method_name, *args, **kwargs):
    """Convenience method to call a method on an object, or a remote reference to an object"""
    if isinstance(obj, RemoteReference):
        try:
            output = yield obj.callRemote(method_name, *args, **kwargs)
        except RemoteError as remote_err:
            reraise_remote_error(remote_err)
        except Exception as err:
            raise err
    else:
        output = getattr(obj, f"remote_{method_name}")(*args, **kwargs)
        if isinstance(output, Deferred):
            output = yield output
    return output


######
#
# Backend - starts the local virtual node and connects to the other virtual nodes
# forming the quantum network
#
class Backend(object):
    def __init__(self, name, virtualFile, network_name="default"):
        """
        Initialize. This will read the configuration file and populate the name,hostname,port information with the
        information found in the configuration file for the given name.
        """
        self._logger = get_netqasm_logger(f"{self.__class__.__name__}({name})")

        # Read the configuration file
        try:
            self.config = SocketsConfig(virtualFile, network_name=network_name, config_type="vnode")
            self.myID = self.config.hostDict[name]
        except KeyError as e:
            self._logger.error(f"No such name in the configuration file {virtualFile}: {e}")
            raise e
        except Exception as e:
            self._logger.error(f"Error reading the configuration file {virtualFile}: {e}")
            raise e

    def start(self, maxQubits=simulaqron_settings.max_qubits, maxRegisters=simulaqron_settings.max_registers):
        """
        Start listening to requests from other nodes.

        Arguments
        maxQubits	maximum qubits in the default register
        """

        try:
            self._logger.debug(f"Starting on port {self.myID.port}")
            node = virtualNode(self.myID, self.config, maxQubits=maxQubits, maxRegisters=maxRegisters)
            reactor.listenTCP(self.myID.port, pb.PBServerFactory(node))

            self._logger.debug("Running reactor")
            reactor.run()
        except CannotListenError:
            self._logger.error(f"NetQASM server address ({self.myID.port}) is already in use.")
            return
        except Exception as e:
            self._logger.error(f"Critical error when starting local virtual node server: {e}")
            return


#######
#
# virtualNode - this is the virtual quantum node. It keeps track of registers simulated here, qubits
# virtually available at this node, etc
#


class virtualNode(pb.Root):
    def __init__(self, ID, config, maxQubits=simulaqron_settings.max_qubits,
                 maxRegisters=simulaqron_settings.max_registers):
        """
        Initialize storing also our own name, hostname and port.

        Arguments:
        ID		host identifier of this node
        maxQubits	maximum number of qubits to use in the default engine (default 10)
        maxRegister	maximum number of registers
        """
        self._logger = get_netqasm_logger(f"{self.__class__.__name__}({ID.name})")

        # Store our own host identifiers and configuration
        self.myID = ID
        self.myID.root = self
        self.config = config

        # Set max nr of registers and virtual qubits
        self.maxRegs = maxRegisters
        self.maxQubits = maxQubits

        # List of connections
        self.conn = {}

        # Number of registers _created_ at this node
        # this may not equal the numbers of registers virtually carried
        self.numRegs = 0

        # Counter for used register numbers
        self._next_reg_num = 0

        # Set up the dictionary of registers
        self.registers = {}

        # Initialize the list of qubits at this node
        self.virtQubits = []
        self.simQubits = []

        # Set up connections to the neighouring nodes in the network
        self.connectNet()

        # Global lock: needs to be acquire whenever we want to manipulate more than one
        # qubit object
        self._lock = DeferredLock()

        # Time until retry
        self._delay = 1

        # Maximum number of attempts at getting locks
        self.maxAttempts = 300

        # List of qubit received to be polled by NetQASM
        self.qubit_recv = {}

        # List of halves of epr-pairs received to be polled by NetQASM
        self.qubit_recv_epr = {}

    def connectNet(self):
        """
        Initialize the connections to the other virtual nodes in the network according to the available
        configuration.
        """

        for key in self.config.hostDict:
            node = self.config.hostDict[key]
            if node.name != self.myID.name:
                self.connect_to_node(node)
            else:
                self.conn[node.name] = node

    def remote_check_connections(self):
        """
        Checks if all connections are up. (Just checks if the number of
        connections equal the number of nodes in config-file)
        """
        return len(self.conn) == len(self.config.hostDict)

    @inlineCallbacks
    def get_connection(self, name):
        """
        Returns the connection specified by 'name'. If no such connection is
        up yet but name is in the configuration file, wait and try again.
        """
        if name in self.conn:
            return self.conn[name]
        else:
            self._logger.debug(f"Connection to {name} not up yet, need to wait...")
            conn_to_return = yield deferLater(
                reactor,
                simulaqron_settings.conn_retry_time,
                self.get_connection,
                name,
            )
            return conn_to_return

    def connect_to_node(self, node):
        """
        Connects to other node. If node not up yet, waits for CONF_WAIT_TIME seconds.
        """
        self._logger.debug(f"Trying to connect to node {node.name}.")
        node.factory = pb.PBClientFactory()
        reactor.connectTCP(node.hostname, node.port, node.factory)
        defer = node.factory.getRootObject()
        defer.addCallback(self.handle_connection, node)
        defer.addErrback(self.handle_connection_error, node)

    def handle_connection(self, obj, node):
        """
        Callback obtaining twisted root object when connection to the node given by the node details 'node'.
        """
        self._logger.debug(f"New connection to {node.name}.")
        # Retrieve the root object: virtualNode on the remote
        node.root = obj

        # Add this node to the local connections
        self.conn[node.name] = node

    def handle_connection_error(self, reason, node):
        """
        Handles errors from trying to connect to other node.
        If a ConnectionRefusedError is raised another try will be made after CONF_WAIT_TIME seconds.
        CONF_WAIT_TIME is set in 'settings.py'.
        Any other error is raised again.
        """

        try:
            reason.raiseException()
        except ConnectionRefusedError:
            self._logger.debug(f"Could not connect to {node.name}, trying again...")
            reactor.callLater(simulaqron_settings.conn_retry_time, self.connect_to_node, node)
        except Exception as e:
            self._logger.error(e)
            reactor.stop()

    def get_virtual_id(self):
        """
        This is a crude and horrible cludge to generate unique IDs for virtual qubits.
        """

        # Loop through the firt k numbers where k is the number of virtual qubits + 1
        # Note that this is guaranteed to find a an index which is not yet used
        for j in range(len(self.virtQubits) + 1):
            used = 0
            for q in self.virtQubits:
                if q.num == j:
                    used = 1
            if used == 0:
                return j

    def get_sim_id(self):
        """
        Similarly, this is a crude and horrible cludge to generate unique IDs for simulated qubits.
        """

        # Loop through the firt k numbers where k is the number of virtual qubits + 1
        # Note that this is guaranteed to find a an index which is not yet used
        for j in range(len(self.simQubits) + 1):
            used = 0
            for q in self.simQubits:
                if q.simNum == j:
                    used = 1
            if used == 0:
                return j

    def _q_num_to_obj(self, num):
        """
        Given the simulation number of a qubit simulated here, return the corresponding object.
        """
        for q in self.simQubits:
            if q.simNum == num:
                return q
        return None

    def remote_isLocked(self):
        return self._lock.locked

    @inlineCallbacks
    def _get_global_lock(self):
        self._logger.debug("GETTING LOCK")
        while self._lock.locked:
            yield deferLater(reactor, self._delay, lambda: None)
        yield self._lock.acquire()
        self._logger.debug("GOT LOCK")

    @inlineCallbacks
    def remote_get_global_lock(self):
        yield self._get_global_lock()

    def _release_global_lock(self):
        self._logger.debug("RELEASE LOCK")
        if self._lock.locked:
            self._lock.release()

    def remote_release_global_lock(self):
        self._release_global_lock()

    @inlineCallbacks
    def _lock_reg_qubits(self, qubit):
        """
        Acquire the lock on all qubits in the same register as the local sim qubit qubit.
        """
        for q in self.simQubits:
            if q.register == qubit.register:
                yield q.lock()

    @inlineCallbacks
    def remote_lock_reg_qubits(self, qubitNum):
        """
        Acquire the lock on all qubits in the same register as qubitNum.
        """
        yield self._lock_reg_qubits(self._q_num_to_obj(qubitNum))

    @inlineCallbacks
    def _unlock_reg_qubits(self, qubit):
        """
        Release the lock on all qubits in the same register as qubit.
        """
        for q in self.simQubits:
            if q.register == qubit.register:
                yield q.unlock()

    @inlineCallbacks
    def remote_unlock_reg_qubits(self, qubitNum):
        """
        Release the lock on all qubits in the same register as qubitNum.
        """
        yield self._unlock_reg_qubits(self._q_num_to_obj(qubitNum))

    def remote_add_register(self, maxQubits=10):
        """
        Adds a new register to the node..

        Arguments:
        maxQubits	maximum number of qubits to use in the default engine
        """
        # TODO We have two methods that do the same thing, should deprecate one of them
        return self.remote_new_register(maxQubits=maxQubits)

    def get_new_reg_num(self):
        """
        Returns an unused register number.
        """
        reg_num = self._next_reg_num
        self._next_reg_num += 1
        return reg_num

    def remote_new_register(self, maxQubits=10):
        """
        Initialize a local register. Right now, this simple creates a register according to the simple engine backend
        using qubit.

        Arguments:
        maxQubits	maximum number of qubits to use in the default engine (default 10)
        """

        # Make sure that reg numbers are assigned correctly
        if self.numRegs >= self.maxRegs:
            self._logger.error("Maximum number of registers reached.")
            raise quantumError("Maximum number of registers reached.")

        self.numRegs = self.numRegs + 1
        regNum = self.get_new_reg_num()
        if simulaqron_settings.sim_backend == SimBackend.QUTIP.value:
            newReg = qutipEngine(self.myID, regNum, maxQubits)
        elif simulaqron_settings.sim_backend == SimBackend.PROJECTQ.value:
            newReg = projectQEngine(self.myID, regNum, maxQubits)
        elif simulaqron_settings.sim_backend == SimBackend.STABILIZER.value:
            newReg = stabilizerEngine(self.myID, regNum, maxQubits)
        else:
            raise quantumError(f"Unknown backend {simulaqron_settings.sim_backend}")

        self.registers[regNum] = newReg

        self._logger.debug("Initializing new simulated register.")
        return newReg

    def remote_delete_register(self, reg):
        """
        Removes the register from the node.
        Happens if the last qubit in the register is measured out.
        """

        # Get register number
        regnum = reg.num

        # Remove register
        self.registers.pop(regnum)
        self.numRegs -= 1

    @inlineCallbacks
    def remote_new_qubit(self, ignore_max_qubits=False):
        """
        Create a new qubit in the default local register.

        :param ignore_max_qubits: bool
            Used to ignore the check if max virtual qubits is reached. This is used when creating EPR pairs
            to be able to temporarily create a qubit.
        """
        self._logger.debug("Request to create new qubit.")

        # Get a lock to assure IDs are assigned correctly and maxQubits is consitently checked
        yield self._get_global_lock()

        try:
            if (len(self.virtQubits) >= self.maxQubits) and (not ignore_max_qubits):
                self._logger.error("Maximum number of virtual qubits reached.")
                raise noQubitError("Max virtual qubits reached")
            else:
                # Qubit in the simulation backend, initialized to |0>
                simNum = self.get_sim_id()

                # Create a new register
                newReg = self.remote_add_register()

                simQubit = simulatedQubit(self.myID, newReg, simNum)
                simQubit.make_fresh()

                self.simQubits.append(simQubit)

                # Virtual qubit
                newNum = self.get_virtual_id()
                newQubit = virtualQubit(self.myID, self.myID, simQubit, newNum)
                self.virtQubits.append(newQubit)
        finally:
            self._release_global_lock()

        return newQubit

    @inlineCallbacks
    def remote_new_qubit_inreg(self, reg):
        """
        Create a new qubit in the specified register reg.
        """

        # Only allow if the register is local
        if reg.simNode != self.myID:
            raise quantumError("Can only create qubits registers simulated locally by this node.")

        # Get a lock to assure IDs are assigned correctly and maxQubits is consitently checked
        yield self._get_global_lock()

        try:
            if len(self.virtQubits) >= self.maxQubits:
                self._logger.error("Maximum number of virtual qubits reached.")
                raise noQubitError("Max virtual qubits reached")
            else:
                # Qubit in the local simulation backend, initialized to |0>
                simNum = self.get_sim_id()
                simQubit = simulatedQubit(self.myID, reg, simNum)
                simQubit.make_fresh()
                self.simQubits.append(simQubit)

                # Virtual qubit
                newNum = self.get_virtual_id()
                newQubit = virtualQubit(self.myID, self.myID, simQubit, newNum)
                self.virtQubits.append(newQubit)
        finally:
            self._release_global_lock()

        return newQubit

    @inlineCallbacks
    def remote_netqasm_send_qubit(self, num, targetName, app_id, remote_app_id):
        """
        Send interface for NetQASM to add the qubit to the remote nodes received list for an application.

        Arguments:
        num		number of virtual qubit to send
        targetName	name of the node to send to
        app_id		application asking to have this qubit delivered
        remote_app_id	application ID to deliver the qubit to
        """
        self._logger.debug(f"request to send qubit {num} to {targetName}")

        virtQubit = self.remote_get_virtual_ref(num)

        newVirtNum = yield self.remote_send_qubit(virtQubit, targetName)

        # Lookup host ID of node
        if not (targetName in self.config.hostDict):
            raise virtNetError(
                f"Trying to get conncetion to virtual node {targetName}, but this is not in configuration file"
            )
        remoteNode = yield self.get_connection(targetName)

        # Ask to add to list
        try:
            yield call_method(
                remoteNode.root,
                "netqasm_add_recv_list",
                self.myID.name,
                app_id,
                remote_app_id,
                newVirtNum,
            )
        except RemoteError as remote_err:
            self.reraise_remote_error(remote_err)

    def remote_netqasm_add_recv_list(self, fromName, from_epr_socket_id, to_epr_socket_id, new_virt_num=None):
        """
        Add an item to the received list for use in NetQASM.
        """

        if not (to_epr_socket_id in self.qubit_recv):
            self.qubit_recv[to_epr_socket_id] = deque([])

        self.qubit_recv[to_epr_socket_id].append(
            QubitNetQASM(
                fromName,
                self.myID.name,
                from_epr_socket_id,
                to_epr_socket_id,
                new_virt_num,
            )
        )
        self._logger.debug(f"Added a qubit on EPR socket ID {to_epr_socket_id} to recv list")

    def remote_netqasm_get_recv(self, to_epr_socket_id):
        """
        Retrieve the next qubit with the given app ID form the received list.
        """

        self._logger.debug(f"Trying to retrieve qubit on EPR socket ID {to_epr_socket_id} from recv list")
        # Get the list corresponding to the specified application ID
        if not (to_epr_socket_id in self.qubit_recv):
            return None

        qQueue = self.qubit_recv[to_epr_socket_id]
        if not qQueue:
            return None

        # Retrieve the first element on that list (first in, first out)
        qc = qQueue.popleft()
        if not qc:
            return None

        self._logger.debug(f"Returning qubit on EPR socket ID {to_epr_socket_id} from recv list")
        return self.remote_get_virtual_ref(qc.virt_num)

    @inlineCallbacks
    def remote_netqasm_send_epr_half(self, num, targetName, app_id, remote_app_id, rawEntInfo):
        """
        Send interface for NetQASM to add the qubit to the remote nodes received list for an application.

        Arguments:
        num		number of virtual qubit to send
        targetName	name of the node to send to
        app_id		application asking to have this qubit delivered
        remote_app_id	application ID to deliver the qubit to
        entInfo		entanglement information
        """
        if num is None:
            # Only an outcome from measure directly so no qubit
            newVirtNum = None
        else:
            qubit = self.remote_get_virtual_ref(num)

            newVirtNum = yield self.remote_send_qubit(qubit, targetName)

        # Lookup host ID of node
        if not (targetName in self.config.hostDict):
            raise virtNetError(
                f"Trying to get conncetion to virtual node {targetName}, but this is not in configuration file"
            )
        remoteNode = yield self.get_connection(targetName)

        # Ask to add to list
        try:
            yield call_method(
                remoteNode.root,
                "netqasm_add_epr_list",
                self.myID.name,
                app_id,
                remote_app_id,
                newVirtNum,
                rawEntInfo,
            )
        except RemoteError as remote_err:
            self.reraise_remote_error(remote_err)

    def remote_netqasm_add_epr_list(self, fromName, from_epr_socket_id, to_epr_socket_id, new_virt_num, rawEntInfo):
        """
        Add an item to the epr list for use in NetQASM.
        """

        if not (to_epr_socket_id in self.qubit_recv_epr):
            self._logger.debug(f"Creating epr list for EPR socket ID {to_epr_socket_id}")
            self.qubit_recv_epr[to_epr_socket_id] = deque([])

        self.qubit_recv_epr[to_epr_socket_id].append(
            QubitNetQASM(
                fromName,
                self.myID.name,
                from_epr_socket_id,
                to_epr_socket_id,
                new_virt_num,
                rawEntInfo=rawEntInfo,
            )
        )
        self._logger.debug(f"Added a qubit on EPR socket ID {to_epr_socket_id} to epr list")

    def remote_netqasm_get_epr_recv(self, to_epr_socket_id):
        """
        Retrieve the next qubit (half of an EPR-pair) with the given app ID from the received list.
        """
        self._logger.debug(f"Trying to retrieve qubit on EPR socket ID {to_epr_socket_id} from epr list")
        # Get the list corresponding to the specified application ID
        if not (to_epr_socket_id in self.qubit_recv_epr):
            self._logger.debug(f"No epr list for EPR socket ID {to_epr_socket_id}")
            return None

        qQueue = self.qubit_recv_epr[to_epr_socket_id]
        if not qQueue:
            self._logger.debug(f"Nothing in epr list for EPR socket ID {to_epr_socket_id}")
            return None

        # Retrieve the first element on that list (first in, first out)
        qc = qQueue.popleft()
        if not qc:
            self._logger.debug(f"First element in epr list is empty for EPR socket ID {to_epr_socket_id}")
            return None

        self._logger.debug(f"Returning qubit on EPR socket ID {to_epr_socket_id} from epr list")
        return self.remote_get_virtual_ref(qc.virt_num), qc.rawEntInfo

    @inlineCallbacks
    def remote_send_qubit(self, qubit, targetName):
        """
        Sends the qubit to the specified target node. This creates a new virtual qubit object at the remote node
        with the right qubit and backend details.

        Arguments
        qubit		virtual qubit to be sent
        targetName	target ndoe to place qubit at (host object)
        """
        self._logger.debug(f"Request to send qubit sim Num {qubit.num} to {targetName}.")
        if qubit.active != 1:
            self._logger.debug("Attempt to manipulate qubit no longer at this node.")
            return

        # Lookup host id of node
        if not (targetName in self.config.hostDict):
            raise virtNetError(
                f"Trying to get conncetion to virtual node {targetName}, but this is not in configuration file"
            )
        remoteNode = yield self.get_connection(targetName)

        # Get lock to prevent access to qubits between sending and manipulating local list
        yield self._get_global_lock()

        try:
            # Check whether we are just the virtual, or also the simulating node
            if qubit.virtNode == qubit.simNode:
                self._logger.debug("Sending qubit simulated locally")
                # We are both the virtual as well as the simulating node
                # Pass a reference to our locally simulated qubit object to the remote node
                try:
                    newNum = yield call_method(remoteNode.root, "add_qubit", self.myID.name, qubit.simQubit)
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)
            else:
                self._logger.debug(f"Sending qubit simulated remotely at {qubit.simNode.name}")
                # Also lock the virtual node of the simulating node unless it is the remoteNode or this node
                locked_node = yield self._lock_simulating_node(exclude=[self.virtNode, remoteNode])
                try:
                    # We are only the virtual node, not the simulating one. In this case, we need to ask
                    # the actual simulating node to do the transfer for us. Due to the pecularities of Twisted PB
                    # we need to do this by the simulated qubit number
                    try:
                        simQubitNum = yield call_method(qubit.simQubit, "get_sim_number")
                    except RemoteError as remote_err:
                        self.reraise_remote_error(remote_err)
                    try:
                        newNum = yield call_method(qubit.simNode.root, "transfer_qubit", simQubitNum, targetName)
                    except RemoteError as remote_err:
                        self.reraise_remote_error(remote_err)
                finally:
                    if locked_node is not None:
                        yield call_method(locked_node.root, "release_global_lock")

            # We gave it away so mark as inactive
            qubit.active = 0

            # Remove the qubit from the local virtual list. Note it remains in the simulated
            # list, since we continue to simulate this qubit if we did so before.
            self.virtQubits.remove(qubit)
        finally:
            self._release_global_lock()

        return newNum

    @inlineCallbacks
    def remote_transfer_qubit(self, simQubitNum, targetName):
        """
        Transfer the qubit to the destination node if we are the simulating node. The reason why we cannot
        do this directly is that Twisted PB does not allow objects to be passed between connecting nodes.
        Only between the creator of the object and its immediate connections.

        Arguments
        simQubitNum	simulated qubit number to be sent
        targetName	target node to place qubit at (host object)
        """
        self._logger.debug(f"Request to transfer qubit to {targetName}.")

        # Convert the number into the right local object
        simQubit = self._q_num_to_obj(simQubitNum)

        # Lookup host id of node
        if not (targetName in self.config.hostDict):
            raise virtNetError(
                f"Trying to get conncetion to virtual node {targetName}, but this is not in configuration file"
            )
        remoteNode = yield self.get_connection(targetName)

        # Check if we are both the destination node and simulating node
        if self.myID.name == targetName:
            newNum = yield remoteNode.root.remote_add_qubit(self.myID.name, simQubit)
        else:
            try:
                newNum = yield call_method(remoteNode.root, "add_qubit", self.myID.name, simQubit)
            except RemoteError as remote_err:
                self.reraise_remote_error(remote_err)

        return newNum

    @inlineCallbacks
    def remote_add_qubit(self, name, simQubit):
        """
        Add a qubit to the local virtual node.

        Arguments
        name		name of the node simulating this qubit
        simQubit 	simulated qubit reference in the backend we're adding
        """

        self._logger.debug(f"Request to add qubit from {name}.")

        # Get the details of the remote node
        if not (name in self.config.hostDict):
            raise virtNetError(
                f"Trying to get conncetion to virtual node {name}, but this is not in configuration file"
            )
        nb = yield self.get_connection(name)

        # Get a lock to make sure IDs are assigned correctly
        yield self._get_global_lock()

        try:
            if len(self.virtQubits) >= self.maxQubits:
                raise noQubitError("Max virtual qubits reached")

            # Generate a new virtual qubit object for the qubit now at this node
            newNum = self.get_virtual_id()
            newQubit = virtualQubit(self.myID, nb, simQubit, newNum)

            # Add to local list
            self.virtQubits.append(newQubit)
        finally:
            self._release_global_lock()

        return newNum

    def remote_get_virtual_ref(self, num):
        """
        Return a virual qubit object for the given number.

        Arguments
        num		number of the virtual qubit
        """

        for q in self.virtQubits:
            if q.num == num:
                return q

        return None

    @inlineCallbacks
    def remote_remove_sim_qubit_num(self, delNum):
        """
        Removes the simulated qubit delQubit from the node and also from the underlying engine. Relies on this qubit
        having been locked.

        Arguments
        delNum		simID of the simulated qubit to delete
        """

        yield self._remove_sim_qubit(self._q_num_to_obj(delNum))

    @inlineCallbacks
    def _remove_sim_qubit(self, delQubit):
        """
        Removes the simulated qubit object.

        Arguments
        delQubit	simulated qubit object to delete
        """
        # Caution: Only qubits simulated at this node can be removed
        if delQubit not in self.simQubits:
            self._logger.error("Attempt to delete qubit not simulated at this node.")
            raise quantumError("Cannot delete qubits we don't simulate.")

        #
        delNum = delQubit.num
        delRegister = delQubit.register

        # Should already be locked
        assert self._lock.locked, "Virtual node is not locked"

        try:
            # Lock all relevant qubits first
            for q in self.simQubits:
                if q.register == delRegister:
                    if q.num != delNum:  # Don't lock the delQubit since it should already be locked
                        yield q.lock()
                    else:
                        assert q.isLocked(), "Qubit should be locked but isn't"

            # First we remove the physical qubit from the register
            delRegister.remove_qubit(delNum)

            # Check if this was the last qubit
            if delRegister.activeQubits == 0:
                self.remote_delete_register(delRegister)
            else:
                # When removing a qubit, we need to update the positions of the qubits in
                # the underlying physical register
                # in all relevant qubit objects.
                for q in self.simQubits:
                    # If they are in the same engine, and update is required
                    if q.register == delRegister:
                        if q.num > delNum:
                            q.num = q.num - 1

            # Remove the qubit form the list of simulated qubits
            self._logger.debug(f"removing qubit {delQubit.simNum} from {self.simQubits}")
            self.simQubits.remove(delQubit)

        finally:
            # Release all relevant qubits again
            for q in self.simQubits:
                if q.register == delRegister:
                    q.unlock()

    def remote_merge_regs(self, num1, num2):
        """
        Merges the two local quantum registers. Note that these register may simulate virtual qubits across different
        network nodes. This will ignore maxQubits and simply create one large register allowing twice maxQubits qubits.

        Arguments
        num1 		number of the first qubit
        num2		number of the second qubit
        """

        # Lookup the qubit objects corresponding to these numbers
        for q in self.simQubits:
            if q.simNum == num1:
                q1 = q
            elif q.simNum == num2:
                q2 = q

        self.local_merge_regs(q1, q2)

    def local_merge_regs(self, qubit1, qubit2):
        """
        Merges the two local quantum registers. Note that these register may simulate virtual qubits across different
        network nodes. This will ignore maxQubits and simply create one large register allowing twice maxQubits qubits.

        Arguments
        qubit1		qubit1 in reg1, called from remote having access to only qubits
        qubit2		qubit2 in reg2
        """
        self._logger.debug(
            f"Request to merge local register for qubits simNum {qubit1.simNum} and simNum {qubit2.simNum}."
        )

        # This should only be called if locks are acquired
        assert qubit1._lock.locked, "Qubit should be locked but isn't"
        assert qubit2._lock.locked, "Qubit should be locked but isn't"
        assert self._lock.locked, "No global lock present"

        self._logger.debug("Request to merge LOCKS PRESENT")

        reg1 = qubit1.register
        reg2 = qubit2.register

        # Check if there's anything to do at all
        if reg1 == reg2:
            self._logger.debug("not required")
            return

        self._logger.debug("need merge")

        # Allow reg 1 to absorb reg 2
        reg1.maxQubits = reg1.maxQubits + reg2.activeQubits

        # For relabelling qubit numbers get the offset
        offset = reg1.activeQubits

        # Add reg2 to reg1
        reg1.absorb(reg2)

        # Update the simulated qubit numbering and register
        for i, q in enumerate(self.simQubits):
            if q.register == reg2:
                self._logger.debug(f"Updating register {q.num} to {q.num + offset}.")
                q.register = reg1
                q.num = q.num + offset

        self.remote_delete_register(reg2)

    @inlineCallbacks
    def remote_merge_from(self, simNodeName, simQubitNum, localReg):
        """
        Bring a remote register to this node.

        Arguments
        simNodeName	name of the node who simulates right now
        simQubitNum	simulation number of qubit whose register we will merge
        localReg	local register to merge with
        """

        self._logger.debug(f"Merging from {simNodeName}")

        # This should only be called if lock is acquired
        assert self._lock.locked, f"No global lock present for node {self.myID.name}"

        self._logger.debug(f"Merging from {simNodeName} LOCKS PRESENT")

        # Lookup the local connection for this simulating node
        if not (simNodeName in self.config.hostDict):
            raise virtNetError(
                f"Trying to get conncetion to virtual node {simNodeName}, but this is not in configuration file"
            )
        simNode = yield self.get_connection(simNodeName)

        # Fetch the details of the remote register and qubit, and remove sim qubits at node
        try:
            (R, I, activeQ, oldRegNum, oldQubitNum) = yield call_method(simNode.root, "get_register_del", simQubitNum)
        except RemoteError as remote_err:
            self.reraise_remote_error(remote_err)

        # Get numbering offset from previous register: append at end
        offset = localReg.activeQubits

        # Allow localReg to absorb the remote register
        localReg.maxQubits = localReg.maxQubits + activeQ
        localReg.absorb_parts(R, I, activeQ)

        # Collect mappings between numbers and objects for updating the virtual qubits
        newD = {}

        # Make new qubit objects
        for k in range(activeQ):
            simNum = self.get_sim_id()
            newQubit = simulatedQubit(self.myID, localReg, simNum, offset + k)
            # Lock the qubit directly until merge is finished
            yield newQubit.lock()
            self.simQubits.append(newQubit)
            newD[k] = newQubit

        # Issue an update call to all nodes to update their virtual qubits if necessary
        # for name in self.conn:
        for name in self.config.hostDict:
            if name != self.myID.name:
                nb = yield self.get_connection(name)
                try:
                    yield call_method(nb.root, "update_virtual_merge", self.myID.name, simNodeName, oldRegNum, newD)
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)

        # Locally, we might also already have virtual qubits which were in the remote simulated
        # register. Update them as well
        self._logger.debug("Updating local virtual qubits.")
        yield self.remote_update_virtual_merge(self.myID.name, simNodeName, oldRegNum, newD)

        # Return the qubit object corresponding to the new physical qubit
        return newD[oldQubitNum]

    @inlineCallbacks
    def remote_update_virtual_merge(self, newSimNodeName, oldSimNodeName, oldRegNum, newD):
        """
        Update the virtual qubits to the new simulating node, if applicable. This is extremely
        inefficient due to not keeping register information in virtualQubit.

        Arguments
        newSimNodeName	new node simulating this qubit
        oldSimNodeName	old node simulating the qubit
        oldReg		old register
        newD		dictionary mapping qubit numbers to qubit objects at the new simulating node
        """

        self._logger.debug("Request to update local virtual qubits.")

        # If this is a third node (not involved in the two qubit gate, but carrying virtual qubits
        # which were in the simulated register), then they will now be updated. We remark that this function
        # can only be called from the _simulating node_ now handing over simulation to someone else. Both the simulating
        # node and the new simulating node are globally locked so there should be no conflicts here in updating:
        # a third node that may wish to do a 2 qubit gate between the qubits to be updated needs to wait.

        # Lookup the local connections for the given node names
        if not (newSimNodeName in self.config.hostDict):
            raise virtNetError(
                f"Trying to get conncetion to virtual node {newSimNodeName}, but this is not in configuration file"
            )
        if not (oldSimNodeName in self.config.hostDict):
            raise virtNetError(
                f"Trying to get conncetion to virtual node {oldSimNodeName}, but this is not in configuration file"
            )
        newSimNode = yield self.get_connection(newSimNodeName)
        oldSimNode = yield self.get_connection(oldSimNodeName)

        for q in self.virtQubits:
            if q.virtNode == q.simNode and q.simNode == oldSimNode:
                self._logger.debug("Simulating node update.")
                # We previously simulated this qubit ourselves
                givenReg = q.simQubit.register.num
                givenNum = q.simQubit.num
            elif q.simNode == oldSimNode:
                self._logger.debug("Previously remote simulator node update.")
                # We had the virtual qubit but it was simulated elsewhere
                try:
                    (givenNum, givenReg) = yield call_method(q.simQubit, "get_numbers")
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)

            # Check if this qubit needs updating
            if q.simNode == oldSimNode and givenReg == oldRegNum:
                self._logger.debug(
                    f"Updating virtual qubit {q.num}, previously {oldSimNode.name} now {newSimNode.name}"
                )
                q.simNode = newSimNode
                q.simQubit = newD[givenNum]

    @inlineCallbacks
    def remote_get_register_RI(self, qubit):
        """
        Return the real and imaginary part of the (possibly remote) simulated register which
        contains this virtual qubit.
        """
        if isinstance(qubit, virtualQubit):
            realM, imagM = yield qubit.remote_get_register_RI()
        else:
            realM, imagM = yield call_method(qubit, "get_register_RI")
        return realM, imagM

    def remote_get_register(self, qubit):
        """
        Return the value of of a locally simulated register which contains this virtual qubit.
        """

        (realM, imagM) = qubit.simQubit.register.get_register_RI()
        activeQ = qubit.simQubit.register.activeQubits
        oldRegNum = qubit.simQubit.register.num
        oldQubitNum = qubit.simQubit.num

        return (realM, imagM, activeQ, oldRegNum, oldQubitNum)

    def remote_get_register_del(self, qubitNum):
        """
        Return the value of of a locally simulated register, and remove the simulated qubits from this node.

        Caution: virtual qubits not updated.
        """

        assert self._lock.locked, "Virtual node is not locked"

        # Locate the qubit object for this ID
        gotQ = None
        for q in self.simQubits:
            if q.simNum == qubitNum:
                gotQ = q

        # If nothing is found, return
        if gotQ is None:
            self._logger.debug(f"No simulated qubit with ID {qubitNum}.")
            return ([], [], 0, 0, 0)

        (realM, imagM) = gotQ.register.get_register_RI()
        activeQ = gotQ.register.activeQubits
        oldRegNum = gotQ.register.num
        oldQubitNum = gotQ.num
        delRegister = gotQ.register

        # Remove all simulated qubits and the register
        # Need to iterate of simQubits in reverse, otherwise wrong elements are removed
        self._logger.debug(f"removing all sim qubits in reg {oldRegNum}")
        for q in reversed(self.simQubits):
            if q.register.num == oldRegNum:
                self.simQubits.remove(q)

        self.remote_delete_register(delRegister)

        return (realM, imagM, activeQ, oldRegNum, oldQubitNum)

    @inlineCallbacks
    def remote_get_multiple_qubits(self, qList):
        """
        Return the state of multiple qubits virtually located at this node. This will fail if the qubits
        are not in the same register or thus also simulating node.

        Arguments
        qList		list of virtual qubits of which to retrieve the state
        """

        localSim = False
        remoteSim = False

        # Check whether we are the simulating node.
        for q in qList:
            if q.simNode == q.virtNode:
                localSim = True
            elif q.simNode != q.virtNode:
                remoteSim = True

        # Check whether two nodes are the simulator, for now we simply fail in this case
        if localSim and remoteSim:
            self._logger.error("Getting multiple qubits from multiple simulators is currently not supported.")
            return ([0], [0])

        if localSim:
            # Qubits are local, simply retrieve from the simulation
            nums = []
            for q in qList:
                nums.append(q.simQubit.simNum)
            self._logger.debug(f"Looking for simulated qubits. {nums}")
            (R, I) = self.remote_get_state(nums)
        else:
            # Qubits are located elsewhere.
            nums = []
            for q in qList:
                try:
                    (num, name) = yield call_method(q.simQubit, "get_details")
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)
                nums.append(num)
            try:
                (R, I) = yield call_method(qList[0].simNode.root, "get_state", nums)
            except RemoteError as remote_err:
                self.reraise_remote_error(remote_err)

        return (R, I)

    def remote_get_state(self, simNumList):
        """
        Return the state of multiple qubits corresponding to the IDs in simNumList.
        """

        # Convert simulation numbers to register and real number in register
        traceList = []
        foundOne = False
        prev = None
        for n in simNumList:
            for q in self.simQubits:
                if q.simNum == n:
                    if foundOne is True and prev.register != q.register:
                        self._logger.error("Getting multiple qubits from different registers not supported.")
                        return ([], [])
                    prev = q
                    foundOne = True
                    traceList.append(q.num)
        if not foundOne:
            self._logger.error("No such qubits found.")
            return

        traceList.sort()
        (realM, imagM) = prev.register.get_qubits_RI(traceList)

        return (realM, imagM)

    def remote_sim_qubit_num_in_same_reg(self, sim_qubit_num1, sim_qubit_num2):
        """Checks if two qubits are in the same register"""
        sim_qubit1 = self._q_num_to_obj(sim_qubit_num1)
        sim_qubit2 = self._q_num_to_obj(sim_qubit_num2)
        assert sim_qubit1 is not None, "Sim num {sim_qubit_num1} not in this node"
        assert sim_qubit2 is not None, "Sim num {sim_qubit_num2} not in this node"
        return sim_qubit1.register == sim_qubit2.register


#######
#
# virtualQubit - a qubit that is virtually carried at this node. It may be simulated elsewhere
# but in the simulation it is located at this particular virtualNode.
#
# This is given out as a reference object to users who ask for a "local" qubit
#
#


class virtualQubit(pb.Referenceable):
    def __init__(self, virtNode, simNode, simQubit, num):
        """
        Creates a virtual qubit object simulated in the specified simulation register backend

        Arguments
        virtNode	node where this qubit is virtually located
        simNode		node where this qubit is simulated
        simQubit	reference to the underlying qubit object (may be remote)
        num		number ID among the virtual qubits
        """
        self._logger = get_netqasm_logger(f"{self.__class__.__name__}({virtNode.name}, {num})")

        # Node where this qubit is virtually located
        self.virtNode = virtNode

        # Node where this qubit is being simulated
        self.simNode = simNode

        # Underlying qubit object for simulation
        self.simQubit = simQubit

        # Qubit active at this node. The client may retain a reference to this object,
        # which will cause python to keep it, while it has actually be transferred to
        # another node. We do not allow operations on a qubit that is now virtually elsewhere.
        self.active = 1

        # Our number at this virtual node. Note that this has nothing to do
        # with the number of the qubits in the register
        self.num = num

    @inlineCallbacks
    def _single_gate(self, name, *args):
        """
        Apply the single gate function to the underlying qubit. This is an internal method used by all the other
        single qubit calls, which will perform the correct local or remote method calls as applicable after
        performing the necessary locking.

        Arguments
        name		name of the method corresponding to the name. For example: name = apply_X
        param		parameters for gates such as rotations (axis,angle)
        """
        self._logger.debug(f"applying gate {name} to virtual qubit {self.num}")
        if self.active != 1:
            self._logger.error("Attempt to manipulate qubits no longer at this node.")
            return False

        locked_node = yield self._lock_simulating_node()
        yield call_method(self.simQubit, "lock")
        try:
            active = yield call_method(self.simQubit, "isActive")
            if active:
                yield call_method(self.simQubit, name, *args)
        finally:
            yield call_method(self.simQubit, "unlock")
            assert locked_node == self.simNode, "Something went wrong"
            yield call_method(self.simNode.root, "release_global_lock")

    @inlineCallbacks
    def remote_apply_X(self):
        """
        Apply X gate to itself by passing it onto the underlying register.
        """
        yield self._single_gate("apply_X")

    @inlineCallbacks
    def remote_apply_Y(self):
        """
        Apply Y gate.
        """
        yield self._single_gate("apply_Y")

    @inlineCallbacks
    def remote_apply_Z(self):
        """
        Apply Z gate.
        """
        yield self._single_gate("apply_Z")

    @inlineCallbacks
    def remote_apply_H(self):
        """
        Apply H gate.
        """
        yield self._single_gate("apply_H")

    @inlineCallbacks
    def remote_apply_K(self):
        """
        Apply K gate - taking computational basis to Y eigenbasis.
        """
        yield self._single_gate("apply_K")

    @inlineCallbacks
    def remote_apply_T(self):
        """
        Apply T gate.
        """
        yield self._single_gate("apply_T")

    @inlineCallbacks
    def remote_apply_rotation(self, n, a):
        """
        Apply rotation around axis n with angle a.
        Arguments:
        n	A tuple of three numbers specifying the rotation axis, e.g n=(1,0,0)
        a	The rotation angle in radians.
        """
        yield self._single_gate("apply_rotation", n, a)

    @inlineCallbacks
    def remote_measure(self, inplace=False):
        """
        Measure the qubit in the standard basis. If inplace=False, this does delete the qubit from the simulation.

        Returns the measurement outcome.
        """

        if self.active != 1:
            self._logger.error("Attempt to manipulate qubits no longer at this node.")
            return

        self._logger.debug("measuring virtual qubit {self.num}")
        locked_node = yield self._lock_simulating_node()
        yield call_method(self.simQubit, "lock")

        try:
            active = yield call_method(self.simQubit, "isActive")
            if active:
                outcome = yield call_method(self.simQubit, "measure_inplace")
                if not inplace:
                    num = yield call_method(self.simQubit, "get_sim_number")
                    yield call_method(self.simNode.root, "remove_sim_qubit_num", num)

                    # Delete from virtual qubits
                    self.virtNode.root.virtQubits.remove(self)
        finally:
            yield call_method(self.simQubit, "unlock")
            assert locked_node == self.simNode, "Something went wrong"
            yield call_method(self.simNode.root, "release_global_lock")

        return outcome

    @inlineCallbacks
    def _lock_nodes(self, target):
        """
        Wrapper to acquire the global register lock on nodes that involve the qubits, and local node.
        This can in fact be everyting from a single node if both qubits are simulated locally or three nodes
        if both qubits are simulated remotely.

        Since deadlocks can occur a random timeout is used when acquiring the locks and the acquisition of the locks
        will be tried again until success.

        Furthermore, when waiting for locks of a simulating node, this might change in the meantime, so we check
        that indeed the simulating nodes are the same after acquiring the locks. If not, we try again until success.

        Parameters
        ----------
        target : :class:`~.virtualQubit`
            virtual qubit of the target qubit

        Returns
        -------
        list: The nodes that have been locked so that they can be unlocked again by the caller
        """
        local_node = self.virtNode
        control_sim_node = self.simNode
        target_sim_node = target.simNode

        ds = {}
        # Get deferreds for locking all the relevant nodes once (which might overlap)
        for node in set([local_node, control_sim_node, target_sim_node]):
            ds[node] = call_method(node.root, "get_global_lock")
        self._logger.debug(f"For merging gonna lock the nodes {list(ds.keys())}")
        # Deferred for all of the locks
        d_lock = DeferredList(list(ds.values()), fireOnOneCallback=False, consumeErrors=True)
        # Since deadlock might occur also schedule a random timeout
        d_timeout = deferLater(reactor, random.uniform(1, 4), lambda: None)
        # Yield on either the locks or the timeout
        yield DeferredList([d_lock, d_timeout], fireOnOneCallback=True, fireOnOneErrback=True, consumeErrors=True)
        if d_timeout.called:
            # Timeout so cancel any locks and revert any that were acquired
            d_lock.cancel()
            self._logger.debug("Trying to get lock timedout, will try again")
            for node, d in ds.items():
                if d.called:
                    yield call_method(node.root, "release_global_lock")
            # Try again
            locked_nodes = yield self._lock_nodes(target=target)
            return locked_nodes
        else:
            assert d_lock.called, "Neither timeout or locked was called"
            # Check that the simulating nodes have not changed in the meantime
            if control_sim_node != self.simNode or target_sim_node != target.simNode:
                self._logger.debug("at least on simulating node changed, releasing and trying again")
                for node, d in ds.items():
                    assert d.called, "Something went wrong, locked deferred not called"
                    yield call_method(node.root, "release_global_lock")
                # Try again
                locked_nodes = yield self._lock_nodes(target=target)
                return locked_nodes
            else:
                return list(ds.keys())

    @inlineCallbacks
    def _lock_inreg(self, qubit):
        """
        Lock all qubits in the same register as the virtual qubit qubit.
        """

        try:
            if qubit.simNode == qubit.virtNode:
                yield qubit.simNode.root._lock_reg_qubits(qubit.simQubit)
            else:
                simNum = yield call_method(qubit.simQubit, "get_sim_number")
                yield call_method(qubit.simNode.root, "lock_reg_qubits", simNum)
        except RemoteError as remote_err:
            self.virtNode.root.reraise_remote_error(remote_err)

    @inlineCallbacks
    def _unlock_inreg(self, qubit):
        """
        Lock all qubits in the same register as the virtual qubit qubit.
        """

        try:
            if qubit.simNode == qubit.virtNode:
                yield qubit.simNode.root._unlock_reg_qubits(qubit.simQubit)
            else:
                simNum = yield call_method(qubit.simQubit, "get_sim_number")
                yield call_method(qubit.simNode.root, "unlock_reg_qubits", simNum)
        except RemoteError as remote_err:
            self.virtNode.root.reraise_remote_error(remote_err)

    @inlineCallbacks
    def remote_cnot_onto(self, target):
        """
        Performs a CNOT operation with this qubit as control, and the other qubit as target.

        Arguments
        target		the virtual qubit to use as the target of the CNOT
        """

        yield self._two_qubit_gate(target, "cnot_onto")

    @inlineCallbacks
    def remote_cphase_onto(self, target):
        """
        Performs a CPHASE operation with this qubit as control, and the other qubit as target.

        Arguments
        target		the virtual qubit to use as the target of the CPHASE
        """

        yield self._two_qubit_gate(target, "cphase_onto")

    @inlineCallbacks
    def _two_qubit_gate(self, target, name):
        """
        Perform a two qubit gate including all the required locking.

        Arguments
        target		second virtual qubit (beyond self which is the first)
        name		name of the gate to perform
        """

        if self.active != 1 or target.active != 1:
            self._logger.error("Attempt to manipulate qubits no longer at this node.")
            return

        localName = "".join(["remote_", name])
        self._logger.debug(f"Doing 2 qubit gate name {name} and local call {localName}")

        # First lock the relevant nodes
        locked_nodes = yield self._lock_nodes(target=target)

        # We have now acquired the relevant global node locks. If more than one qubit is locked, all code
        # will first acquire the global lock, so this should be safe from deadlocks now, so we will not timeout
        # Lock the control qubits register
        # If the target is in the same register we don't want to lock again so first check
        # what case we are in
        yield self._lock_inreg(self)
        # if self.simQubit.register != target.simQubit.register:

        # Todo a 2 qubit gate, both qubits must be in the same simulated register. We will merge
        # registers if this is not already the case.
        try:
            if self.simNode == target.simNode:
                # Both qubits are simulated at the same node
                self._logger.debug("both qubits same node for two qubit gate")

                if self.simNode == self.virtNode:
                    self._logger.debug("both qubits locally for two qubit gate")
                    # Both qubits are both locally simulated, check whether they are in the same register

                    if self.simQubit.register == target.simQubit.register:
                        # They are even in the same register, just do the gate
                        getattr(self.simQubit, localName)(target.simQubit.num)
                    else:
                        yield self._lock_inreg(target)
                        self._logger.debug("2qubit command demands register merge.")
                        # Both are local but not in the same register
                        yield self.simNode.root.local_merge_regs(self.simQubit, target.simQubit)

                        # After the merge, just do the gate
                        getattr(self.simQubit, localName)(target.simQubit.num)
                else:
                    # Both are remotely simulated
                    self._logger.debug("2qubit command demands remote register merge.")

                    # Fetch the details of the two simulated qubits from remote
                    (fNum, fNode) = yield call_method(self.simQubit, "get_details")
                    (tNum, tNode) = yield call_method(target.simQubit, "get_details")

                    same_reg = yield call_method(self.simNode.root, "sim_qubit_num_in_same_reg", fNum, tNum)
                    if not same_reg:
                        # Not same register so also lock target register
                        yield self._lock_inreg(target)

                    # Sanity check: we really have the right simulating node
                    if fNode != self.simNode.name or tNode != target.simNode.name:
                        self._logger.error("Inconsistent simulation. Cannot merge.")
                        raise quantumError("Inconsistent simulation")

                    # Merge the remote register according to the simulation IDs of the qubits
                    self._logger.debug("merging remote same node")
                    yield call_method(self.simNode.root, "merge_regs", fNum, tNum)

                    # Get the number of the target in the new register
                    targetNum = yield call_method(target.simQubit, "get_number")

                    # Execute the 2 qubit gate
                    yield call_method(self.simQubit, name, targetNum)
                    self._logger.debug(f"Remote 2qubit command to {target.simNode.name}.")
            else:
                # They are simulated at two different nodes
                if self.simNode == self.virtNode:
                    self._logger.debug("control is simulated locally")

                    # We are the locally simulating node of the first qubit, merge all to us
                    self._logger.debug(
                        "2qubit command demands merge from remote target sim %s to us.",
                        target.simNode.name,
                    )
                    (fNum, fNode) = yield call_method(target.simQubit, "get_details")
                    if fNode != target.simNode.name:
                        self._logger.error("Inconsistent simulation. Cannot merge.")
                        raise quantumError("Inconsistent simulation.")
                    target.simQubit = yield self.simNode.root.remote_merge_from(
                        target.simNode.name, fNum, self.simQubit.register
                    )

                    # Get the number of the target in the new register
                    targetNum = target.simQubit.num

                    # Execute the 2 qubit gate
                    getattr(self.simQubit, localName)(targetNum)

                elif target.simNode == target.virtNode:
                    # We are the locally simulating node of the target qubit, merge all to us
                    self._logger.debug(
                        "2qubit command demands merge from remote sim %s to us.",
                        self.simNode.name,
                    )
                    (fNum, fNode) = yield call_method(self.simQubit, "get_details")
                    if fNode != self.simNode.name:
                        self._logger.error("Inconsistent simulation. Cannot merge.")
                        raise quantumError("Inconsistent simulation.")
                    self.simQubit = yield target.simNode.root.remote_merge_from(
                        self.simNode.name, fNum, target.simQubit.register
                    )

                    # Get the number of the target in the new register
                    targetNum = target.simQubit.num

                    # Execute the 2 qubit gate
                    getattr(self.simQubit, localName)(targetNum)

                else:
                    self._logger.debug("both are remote")
                    # Both qubits are remotely simulated - we will pull both registers to become one local register
                    self._logger.debug(
                        "2qubit command demands total remote merge from %s and %s.",
                        target.simNode.name,
                        self.simNode.name,
                    )

                    # Create a new local register
                    newLocalReg = self.virtNode.root.remote_add_register()

                    # Fetch the detail of the two registers from remote
                    (fNum, fNode) = yield call_method(self.simQubit, "get_details")
                    if fNode != self.simNode.name:
                        self._logger.error("Inconsistent simulation. Cannot merge.")
                        raise quantumError("Inconsistent simulation.")
                    (tNum, tNode) = yield call_method(target.simQubit, "get_details")
                    if tNode != target.simNode.name:
                        self._logger.error("Inconsistent simulation. Cannot merge.")
                        raise quantumError("Inconsistent simulation.")

                    # Pull the remote registers to this node
                    self.simQubit = yield self.virtNode.root.remote_merge_from(
                        self.simNode.name,
                        fNum,
                        newLocalReg,
                    )
                    target.simQubit = yield target.virtNode.root.remote_merge_from(
                        target.simNode.name, tNum, newLocalReg
                    )
                    # Get the number of the target in the new register
                    targetNum = target.simQubit.num

                    # Finally, execute the two qubit gate
                    getattr(self.simQubit, localName)(targetNum)
        except RemoteError as remote_err:
            self.virtNode.root.reraise_remote_error(remote_err)
        finally:
            # Release the locks in the register of the control (which now contains also the others)
            yield self._unlock_inreg(self)
            for node in locked_nodes:
                yield call_method(node.root, "release_global_lock")

    @inlineCallbacks
    def remote_get_number(self):
        """
        Returns the number of this qubit in whatever local register it is in. Not useful for the client,
        but convenient for debugging.
        """

        if self.active != 1:
            self._logger.error("Attempt to manipulate qubits no longer at this node.")

        if self.virtNode == self.simNode:
            num = self.simQubit.num
        else:
            try:
                num = yield call_method(self.simQubit, "get_number")
            except ConnectionError:
                self._logger.error("cannot get qubit number.")
                return

        return num

    def remote_get_virt_num(self):
        """
        Returns the number of the virtual qubit.
        """
        return self.num

    def remote_get_virtNode(self):
        """
        Returns the virtNode of this virtual qubit
        """
        return self.virtNode.name

    def remote_get_simNode(self):
        """
        Returns the simNode of this virtual qubit
        """
        return self.simNode.name

    @inlineCallbacks
    def remote_get_qubit(self):
        """
        Returns the state of this qubit in real and imaginary parts separated. This is required
        single Twisted cannot natively transfer complex valued objects.
        """

        if self.active != 1:
            self._logger.error("Attempt to manipulate qubits no longer at this node.")

        if self.virtNode == self.simNode:
            (R, I) = self.simQubit.remote_get_qubit()
        else:
            try:
                try:
                    (R, I) = yield call_method(self.simQubit, "get_qubit")
                except RemoteError as remote_err:
                    self.virtNode.root.reraise_remote_error(remote_err)
            except ConnectionError:
                self._logger.error("cannot get qubit number.")

        return (R, I)

    @inlineCallbacks
    def remote_get_register_RI(self):
        if self.simNode == self.virtNode:
            realM, imagM = self.simQubit.register.get_register_RI()
        else:
            realM, imagM = yield call_method(self.simQubit, "get_register_RI")
        return realM, imagM

    @inlineCallbacks
    def _lock_simulating_node(self, exclude=None):
        """Aquires a global lock on the simulating node

        Since the simulating node can change while trying to acquire the lock, we
        check if this happened and if so, try again.

        Parameters
        ----------
        exclude : list
            List of hosts which to exclude since they might already have been locked
        """
        if exclude is None:
            exclude = []
        curr_sim_node = self.simNode
        if curr_sim_node in exclude:
            return
        yield call_method(curr_sim_node.root, "get_global_lock")
        # Now that we have a look, check that the sim node hasn't change before the looked was acquired
        if curr_sim_node != self.simNode:
            # Release the lock since this is not anymore the simulating one and try again
            self._logger.debug("simulating node changed, releasing and trying again")
            yield call_method(curr_sim_node.root, "release_global_lock")
            locked_node = yield self._lock_simulating_node()
            return locked_node
        else:
            self._logger.debug("got lock of simulating node {curr_sim_node}")
            return curr_sim_node


############################################
#
# Keeping track of received qubits and outcomes for NetQASM


class QubitNetQASM:
    def __init__(self, fromName, toName, from_epr_socket_id, to_epr_socket_id, new_virt_num=None, rawEntInfo=None):
        self.fromName = fromName
        self.toName = toName
        self.from_epr_socket_id = from_epr_socket_id
        self.to_epr_socket_id = to_epr_socket_id
        self.virt_num = new_virt_num
        self.rawEntInfo = rawEntInfo

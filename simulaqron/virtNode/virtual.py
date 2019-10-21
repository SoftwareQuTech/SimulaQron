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

import logging
import random

from collections import deque

from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, DeferredLock, Deferred, DeferredList
from twisted.internet.task import deferLater
from twisted.internet.error import ConnectionRefusedError, CannotListenError
from twisted.spread.pb import RemoteError

from simulaqron.virtNode.basics import quantumError, noQubitError, virtNetError
from simulaqron.virtNode.quantum import simulatedQubit
from simulaqron.general.hostConfig import socketsConfig
from simulaqron.settings import simulaqron_settings

if simulaqron_settings.backend == "qutip":
    from simulaqron.virtNode.qutipSimulator import qutipEngine
elif simulaqron_settings.backend == "projectq":
    from simulaqron.virtNode.projectQSimulator import projectQEngine
elif simulaqron_settings.backend == "stabilizer":
    from simulaqron.virtNode.stabilizerSimulator import stabilizerEngine
else:
    raise quantumError("Unknown backend {}".format(simulaqron_settings.backend))


######
#
# backEnd - starts the local virtual node and connects to the other virtual nodes
# forming the quantum network
#
class backEnd(object):
    def __init__(self, name, virtualFile, network_name="default"):
        """
        Initialize. This will read the configuration file and populate the name,hostname,port information with the
        information found in the configuration file for the given name.
        """

        # Read the configuration file
        try:
            self.config = socketsConfig(virtualFile, network_name=network_name, config_type="vnode")
            self.myID = self.config.hostDict[name]
        except KeyError as e:
            logging.error("LOCAL {}: No such name in the configuration file {}: {}".format(name, virtualFile, e))
            raise e
        except Exception as e:
            logging.error("LOCAL {}: Error reading the configuration file {}: {}".format(name, virtualFile, e))
            raise e

    def start(self, maxQubits=simulaqron_settings.max_qubits, maxRegisters=simulaqron_settings.max_registers):
        """
        Start listening to requests from other nodes.

        Arguments
        maxQubits	maximum qubits in the default register
        """

        try:
            logging.debug("VIRTUAL NODE %s: Starting on port %d", self.myID.name, self.myID.port)
            node = virtualNode(self.myID, self.config, maxQubits=maxQubits, maxRegisters=maxRegisters)
            reactor.listenTCP(self.myID.port, pb.PBServerFactory(node))

            logging.debug("VIRTUAL NODE %s: running reactor.", self.myID.name)
            reactor.run()
        except CannotListenError:
            logging.error("LOCAL {}: CQC server address ({}) is already in use.".format(self.myID.name, self.myID.port))
            return
        except Exception as e:
            logging.error(
                "LOCAL {}: Critical error when starting local virtual node server: {}".format(self.myID.name, e)
            )
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

        try:

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

            # List of qubit received to be polled by CQC
            self.cqcRecv = {}

            # List of halves of epr-pairs received to be polled by CQC
            self.cqcRecvEpr = {}

        except Exception as e:
            logging.error("VIRTUAL NODE {}: Critical error when initializing virtNode: {}".format(ID.name, e))
            raise e

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

    def connectNet(self):
        """
        Initialize the connections to the other virtual nodes in the network according to the available
        configuration.
        """

        try:
            for key in self.config.hostDict:
                node = self.config.hostDict[key]
                if node.name != self.myID.name:
                    self.connect_to_node(node)
                else:
                    self.conn[node.name] = node
        except Exception as e:
            logging.error(
                "VIRTUAL NODE {}: Critical error when connection network of virtual nodes: {}".format(self.myID.name, e)
            )
            raise e

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
            try:
                logging.debug(
                    "VIRTUAL NODE {}: Connection to {} not up yet, need to wait...".format(self.myID.name, name)
                )
                conn_to_return = yield deferLater(reactor, simulaqron_settings.conn_retry_time, self.get_connection,
                                                  name)
                return conn_to_return
            except Exception as e:
                raise e

    def connect_to_node(self, node):
        """
        Connects to other node. If node not up yet, waits for CONF_WAIT_TIME seconds.
        """
        logging.debug("VIRTUAL NODE {}: Trying to connect to node {}.".format(self.myID.name, node.name))
        node.factory = pb.PBClientFactory()
        reactor.connectTCP(node.hostname, node.port, node.factory)
        defer = node.factory.getRootObject()
        defer.addCallback(self.handle_connection, node)
        defer.addErrback(self.handle_connection_error, node)

    def handle_connection(self, obj, node):
        """
        Callback obtaining twisted root object when connection to the node given by the node details 'node'.
        """
        try:
            logging.debug("VIRTUAL NODE %s: New connection to %s.", self.myID.name, node.name)
            # Retrieve the root object: virtualNode on the remote
            node.root = obj

            # Add this node to the local connections
            self.conn[node.name] = node
        except Exception as e:
            logging.error(
                "VIRTUAL NODE {}: Critical error when handling connection to node {}: {}".format(
                    self.myID.name, node.name, e
                )
            )
            raise e

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
            logging.debug("VIRTUAL NODE {}: Could not connect to {}, trying again...".format(self.myID.name, node.name))
            reactor.callLater(simulaqron_settings.conn_retry_time, self.connect_to_node, node)
        except Exception as e:
            logging.error(
                "VIRTUAL NODE {}: Critical error when connection to local virtual node: {}".format(self.myID.name, e)
            )
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
        logging.debug("VIRTUAL NODE %s: Local GETTING LOCK", self.myID.name)
        try:
            yield self._lock.acquire()
        except Exception as e:
            raise e
        logging.debug("VIRTUAL NODE %s: Local GOT LOCK", self.myID.name)

    @inlineCallbacks
    def remote_get_global_lock(self):
        logging.debug("VIRTUAL NODE %s: Remote GETTING LOCK", self.myID.name)
        try:
            yield self._lock.acquire()
        except Exception as e:
            raise e
        logging.debug("VIRTUAL NODE %s: Remote GOT LOCK", self.myID.name)

    @inlineCallbacks
    def _release_global_lock(self):
        logging.debug("VIRTUAL NODE %s: Local RELEASE LOCK", self.myID.name)
        if self._lock.locked:
            try:
                yield self._lock.release()
            except Exception as e:
                raise e

    @inlineCallbacks
    def remote_release_global_lock(self):
        logging.debug("VIRTUAL NODE %s: Remote RELEASE LOCK", self.myID.name)
        if self._lock.locked:
            try:
                yield self._lock.release()
            except Exception as e:
                raise e

    @inlineCallbacks
    def _lock_reg_qubits(self, qubit):
        """
        Acquire the lock on all qubits in the same register as the local sim qubit qubit.
        """
        for q in self.simQubits:
            if q.register == qubit.register:
                try:
                    yield q.lock()
                except Exception as err:
                    raise err

    @inlineCallbacks
    def remote_lock_reg_qubits(self, qubitNum):
        """
        Acquire the lock on all qubits in the same register as qubitNum.
        """

        try:
            yield self._lock_reg_qubits(self._q_num_to_obj(qubitNum))
        except Exception as err:
            raise err

    @inlineCallbacks
    def _unlock_reg_qubits(self, qubit):
        """
        Release the lock on all qubits in the same register as qubit.
        """
        for q in self.simQubits:
            if q.register == qubit.register:
                if q._lock.locked:
                    try:
                        yield q.unlock()
                    except Exception as err:
                        raise err

    @inlineCallbacks
    def remote_unlock_reg_qubits(self, qubitNum):
        """
        Release the lock on all qubits in the same register as qubitNum.
        """

        try:
            yield self._unlock_reg_qubits(self._q_num_to_obj(qubitNum))
        except Exception as err:
            raise err

    def remote_add_register(self, maxQubits=10):
        """
        Adds a new register to the node..

        Arguments:
        maxQubits	maximum number of qubits to use in the default engine
        """
        # TODO We have to methods that do the same thing, should deprecate one of them
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

        try:
            # Make sure that reg numbers are assigned correctly
            self._get_global_lock()

            if self.numRegs >= self.maxRegs:
                logging.error("%s: Maximum number of registers reached.", self.myID.name)
                raise quantumError("Maximum number of registers reached.")

            self.numRegs = self.numRegs + 1
            regNum = self.get_new_reg_num()
            if simulaqron_settings.backend == "qutip":
                newReg = qutipEngine(self.myID, regNum, maxQubits)
            elif simulaqron_settings.backend == "projectq":
                newReg = projectQEngine(self.myID, regNum, maxQubits)
            elif simulaqron_settings.backend == "stabilizer":
                newReg = stabilizerEngine(self.myID, regNum, maxQubits)
            else:
                raise quantumError("Unknown backend {}".format(simulaqron_settings.backend))

            self.registers[regNum] = newReg

            logging.debug("VIRTUAL NODE %s: Initializing new simulated register.", self.myID.name)
        except Exception as e:
            logging.error("VIRTUAL NODE {}: Critical error when getting new register: {}".format(self.myID.name, e))
            raise e
        finally:
            self._release_global_lock()
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
        logging.debug("VIRTUAL NODE %s: Request to create new qubit.", self.myID.name)

        try:
            # Get a lock to assure IDs are assigned correctly and maxQubits is consitently checked
            try:
                yield self._get_global_lock()
            except Exception as err:
                raise err

            if (len(self.virtQubits) >= self.maxQubits) and (not ignore_max_qubits):
                logging.error("VIRTUAL NODE %s: Maximum number of virtual qubits reached.", self.myID.name)
                raise noQubitError("Max virtual qubits reached")
            else:
                # Qubit in the simulation backend, initialized to |0>
                simNum = self.get_sim_id()

                # Create a new register
                newReg = self.remote_add_register()

                # simQubit = simulatedQubit(self.myID, self.defaultReg, simNum)
                simQubit = simulatedQubit(self.myID, newReg, simNum)
                try:
                    simQubit.make_fresh()
                except noQubitError as err:
                    logging.error("VIRTUAL NODE %s: Max qubits for register reached.", self.myID.name)
                    raise err

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

        try:
            # Get a lock to assure IDs are assigned correctly and maxQubits is consitently checked
            try:
                yield self._get_global_lock()
            except Exception as err:
                raise err

            if len(self.virtQubits) >= self.maxQubits:
                logging.error("VIRTUAL NODE %s: Maximum number of virtual qubits reached.", self.myID.name)
                raise noQubitError("Max virtual qubits reached")
            else:
                # Qubit in the local simulation backend, initialized to |0>
                simNum = self.get_sim_id()
                simQubit = simulatedQubit(self.myID, reg, simNum)
                try:
                    simQubit.make_fresh()
                except noQubitError as err:
                    logging.error("VIRTUAL NODE %s: Max qubits for register reached.", self.myID.name)
                    raise err
                self.simQubits.append(simQubit)

                # Virtual qubit
                newNum = self.get_virtual_id()
                newQubit = virtualQubit(self.myID, self.myID, simQubit, newNum)
                self.virtQubits.append(newQubit)
        finally:
            self._release_global_lock()

        return newQubit

    @inlineCallbacks
    def remote_cqc_send_qubit(self, num, targetName, app_id, remote_app_id):
        """
        Send interface for CQC to add the qubit to the remote nodes received list for an application.

        Arguments:
        num		number of virtual qubit to send
        targetName	name of the node to send to
        app_id		application asking to have this qubit delivered
        remote_app_id	application ID to deliver the qubit to
        """
        logging.debug("VIRTUAL NODE %s: request to send qubit %d to %s", self.myID.name, num, targetName)

        virtQubit = self.remote_get_virtual_ref(num)

        try:
            newVirtNum = yield self.remote_send_qubit(virtQubit, targetName)
        except Exception as err:
            raise err

        # Lookup host ID of node
        try:
            if not (targetName in self.config.hostDict):
                raise virtNetError(
                    "Trying to get conncetion to virtual node {}, but this is not in configuration file".format(
                        targetName
                    )
                )
            remoteNode = yield self.get_connection(targetName)
        except Exception as err:
            raise err

        # Ask to add to list
        try:
            yield remoteNode.root.callRemote("cqc_add_recv_list", self.myID.name, app_id, remote_app_id, newVirtNum)
        except RemoteError as remote_err:
            self.reraise_remote_error(remote_err)
        except Exception as err:
            raise err

    def remote_cqc_add_recv_list(self, fromName, from_app_id, to_app_id, new_virt_num):
        """
        Add an item to the received list for use in CQC.
        """

        if not (to_app_id in self.cqcRecv):
            self.cqcRecv[to_app_id] = deque([])

        self.cqcRecv[to_app_id].append(QubitCQC(fromName, self.myID.name, from_app_id, to_app_id, new_virt_num))
        logging.debug("VIRTUAL NODE %s: Added a qubit for app id %d to recv list", self.myID.name, to_app_id)

    def remote_cqc_get_recv(self, to_app_id):
        """
        Retrieve the next qubit with the given app ID form the received list.
        """

        logging.debug(
            "VIRTUAL NODE %s: Trying to retrieve qubit for app id %d from recv list", self.myID.name, to_app_id
        )
        # Get the list corresponding to the specified application ID
        if not (to_app_id in self.cqcRecv):
            return None

        qQueue = self.cqcRecv[to_app_id]
        if not qQueue:
            return None

        # Retrieve the first element on that list (first in, first out)
        qc = qQueue.popleft()
        if not qc:
            return None

        logging.debug("VIRTUAL NODE %s: Returning qubit for app id %d from recv list", self.myID.name, to_app_id)
        return self.remote_get_virtual_ref(qc.virt_num)

    @inlineCallbacks
    def remote_cqc_send_epr_half(self, num, targetName, app_id, remote_app_id, rawEntInfo):
        """
        Send interface for CQC to add the qubit to the remote nodes received list for an application.

        Arguments:
        num		number of virtual qubit to send
        targetName	name of the node to send to
        app_id		application asking to have this qubit delivered
        remote_app_id	application ID to deliver the qubit to
        entInfo		entanglement information
        """
        qubit = self.remote_get_virtual_ref(num)

        try:
            newVirtNum = yield self.remote_send_qubit(qubit, targetName)
        except Exception as err:
            raise err

        # Lookup host ID of node
        try:
            if not (targetName in self.config.hostDict):
                raise virtNetError(
                    "Trying to get conncetion to virtual node {}, but this is not in configuration file".format(
                        targetName
                    )
                )
            remoteNode = yield self.get_connection(targetName)
        except Exception as e:
            raise e

        # Ask to add to list
        try:
            yield remoteNode.root.callRemote(
                "cqc_add_epr_list", self.myID.name, app_id, remote_app_id, newVirtNum, rawEntInfo
            )
        except RemoteError as remote_err:
            self.reraise_remote_error(remote_err)
        except Exception as err:
            raise err

    def remote_cqc_add_epr_list(self, fromName, from_app_id, to_app_id, new_virt_num, rawEntInfo):
        """
        Add an item to the epr list for use in CQC.
        """

        if not (to_app_id in self.cqcRecvEpr):
            self.cqcRecvEpr[to_app_id] = deque([])

        self.cqcRecvEpr[to_app_id].append(
            QubitCQC(fromName, self.myID.name, from_app_id, to_app_id, new_virt_num, rawEntInfo=rawEntInfo)
        )
        logging.debug("VIRTUAL NODE %s: Added a qubit for app id %d to epr list", self.myID.name, to_app_id)

    def remote_cqc_get_epr_recv(self, to_app_id):
        """
        Retrieve the next qubit (half of an EPR-pair) with the given app ID from the received list.
        """

        try:
            logging.debug(
                "VIRTUAL NODE %s: Trying to retrieve qubit for app id %d from epr list", self.myID.name, to_app_id
            )
            # Get the list corresponding to the specified application ID
            if not (to_app_id in self.cqcRecvEpr):
                return None

            qQueue = self.cqcRecvEpr[to_app_id]
            if not qQueue:
                return None

            # Retrieve the first element on that list (first in, first out)
            qc = qQueue.popleft()
            if not qc:
                return None

            logging.debug("VIRTUAL NODE %s: Returning qubit for app id %d from epr list", self.myID.name, to_app_id)
            return self.remote_get_virtual_ref(qc.virt_num), qc.rawEntInfo

        except Exception as e:
            raise e

    @inlineCallbacks
    def remote_send_qubit(self, qubit, targetName):
        """
        Sends the qubit to the specified target node. This creates a new virtual qubit object at the remote node
        with the right qubit and backend details.

        Arguments
        qubit		virtual qubit to be sent
        targetName	target ndoe to place qubit at (host object)
        """
        logging.debug("VIRTUAL NODE %s: Request to send qubit sim Num %d to %s.", self.myID.name, qubit.num, targetName)
        if qubit.active != 1:
            logging.debug("VIRTUAL NODE %s: Attempt to manipulate qubit no longer at this node.", self.myID.name)
            return

        # Lookup host id of node
        try:
            if not (targetName in self.config.hostDict):
                raise virtNetError(
                    "Trying to get conncetion to virtual node {}, but this is not in configuration file".format(
                        targetName
                    )
                )
            remoteNode = yield self.get_connection(targetName)
        except Exception as e:
            raise e

        try:
            # Get lock to prevent access to qubits between sending and manipulating local list
            self._get_global_lock()

            # Check whether we are just the virtual, or also the simulating node
            if qubit.virtNode == qubit.simNode:
                logging.debug("VIRTUAL NODE %s: Sending qubit simulated locally", self.myID.name)
                # We are both the virtual as well as the simulating node
                # Pass a reference to our locally simulated qubit object to the remote node
                try:
                    newNum = yield remoteNode.root.callRemote("add_qubit", self.myID.name, qubit.simQubit)
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)
                except Exception as err:
                    raise err
            else:
                logging.debug(
                    "VIRTUAL NODE %s: Sending qubit simulated remotely at %s", self.myID.name, qubit.simNode.name
                )
                # We are only the virtual node, not the simulating one. In this case, we need to ask
                # the actual simulating node to do the transfer for us. Due to the pecularities of Twisted PB
                # we need to do this by the simulated qubit number
                try:
                    simQubitNum = yield qubit.simQubit.callRemote("get_sim_number")
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)
                except Exception as err:
                    raise err
                try:
                    newNum = yield qubit.simNode.root.callRemote("transfer_qubit", simQubitNum, targetName)
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)
                except Exception as err:
                    raise err

            # We gave it away so mark as inactive
            qubit.active = 0

            # Remove the qubit from the local virtual list. Note it remains in the simulated
            # list, since we continue to simulate this qubit if we did so before.
            self.virtQubits.remove(qubit)
        except Exception as err:
            raise err
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
        logging.debug("VIRTUAL NODE %s: Request to transfer qubit to %s.", self.myID.name, targetName)

        # Convert the number into the right local object
        simQubit = self._q_num_to_obj(simQubitNum)

        # Lookup host id of node
        try:
            if not (targetName in self.config.hostDict):
                raise virtNetError(
                    "Trying to get conncetion to virtual node {}, but this is not in configuration file".format(
                        targetName
                    )
                )
            remoteNode = yield self.get_connection(targetName)
        except Exception as e:
            raise e

        # Check if we are both the destination node and simulating node
        if self.myID.name == targetName:
            try:
                newNum = yield remoteNode.root.remote_add_qubit(self.myID.name, simQubit)
            except Exception as err:
                raise err
        else:
            try:
                newNum = yield remoteNode.root.callRemote("add_qubit", self.myID.name, simQubit)
            except RemoteError as remote_err:
                self.reraise_remote_error(remote_err)
            except Exception as err:
                raise err

        return newNum

    @inlineCallbacks
    def remote_add_qubit(self, name, simQubit):
        """
        Add a qubit to the local virtual node.

        Arguments
        name		name of the node simulating this qubit
        simQubit 	simulated qubit reference in the backend we're adding
        """

        logging.debug("VIRTUAL NODE %s: Request to add qubit from %s.", self.myID.name, name)

        # Get the details of the remote node
        try:
            if not (name in self.config.hostDict):
                raise virtNetError(
                    "Trying to get conncetion to virtual node {}, but this is not in configuration file".format(name)
                )
            nb = yield self.get_connection(name)
        except Exception as e:
            raise e

        try:
            # Get a lock to make sure IDs are assigned correctly
            self._get_global_lock()

            if len(self.virtQubits) >= self.maxQubits:
                raise noQubitError("Max virtual qubits reached")

            # Generate a new virtual qubit object for the qubit now at this node
            newNum = self.get_virtual_id()
            newQubit = virtualQubit(self.myID, nb, simQubit, newNum)

            # Add to local list
            self.virtQubits.append(newQubit)
        except Exception as err:
            raise err
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

    def remote_remove_sim_qubit_num(self, delNum):
        """
        Removes the simulated qubit delQubit from the node and also from the underlying engine. Relies on this qubit
        having been locked.

        Arguments
        delNum		simID of the simulated qubit to delete
        """

        self._remove_sim_qubit(self._q_num_to_obj(delNum))

    @inlineCallbacks
    def _remove_sim_qubit(self, delQubit):
        """
        Removes the simulated qubit object.

        Arguments
        delQubit	simulated qubit object to delete
        """

        # Caution: Only qubits simulated at this node can be removed
        if delQubit not in self.simQubits:
            logging.error("VIRTUAL NODE %s: Attempt to delete qubit not simulated at this node.", self.myID.name)
            raise quantumError("%s: Cannot delete qubits we don't simulate.")

        #
        delNum = delQubit.num
        delRegister = delQubit.register

        try:
            # We need to manipulate multiple qubits, get global lock
            yield self._get_global_lock()

            # Lock all relevant qubits first
            for q in self.simQubits:
                if q.register == delRegister:
                    yield q.lock()

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
            self.simQubits.remove(delQubit)

        except Exception as e:
            logging.error("VIRTUAL NODE {}: Cannot remove sim qubit - {}".format(self.myID.name, e))
        finally:
            # Release all relevant qubits again
            for q in self.simQubits:
                if q.register == delRegister:
                    q.unlock()

            # Release the global multi qubit lock
            self._release_global_lock()

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
        logging.debug(
            "VIRTUAL NODE %s: Request to merge local register for qubits simNum %d and simNum %d.",
            self.myID.name,
            qubit1.simNum,
            qubit2.simNum,
        )

        # This should only be called if locks are acquired
        assert qubit1._lock.locked
        assert qubit2._lock.locked
        assert self._lock.locked

        logging.debug("VIRTUAL NODE %s: Request to merge LOCKS PRESENT", self.myID.name)

        reg1 = qubit1.register
        reg2 = qubit2.register

        # Check if there's anything to do at all
        if reg1 == reg2:
            logging.debug("VIRTUAL NODE %s: Request to merge local register: not required", self.myID.name)
            return

        logging.debug("VIRTUAL NODE %s: Request to merge local register: need merge", self.myID.name)

        # Allow reg 1 to absorb reg 2
        reg1.maxQubits = reg1.maxQubits + reg2.activeQubits

        # For relabelling qubit numbers get the offset
        offset = reg1.activeQubits

        # Add reg2 to reg1
        reg1.absorb(reg2)

        # Update the simulated qubit numbering and register
        for q in self.simQubits:
            if q.register == reg2:
                logging.debug("VIRTUAL NODE %s: Updating register %d to %d.", self.myID.name, q.num, q.num + offset)
                q.register = reg1
                q.num = q.num + offset

        # reg2.reset()
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

        logging.debug("VIRTUAL NODE %s: Merging from %s", self.myID.name, simNodeName)

        # This should only be called if lock is acquired
        assert self._lock.locked

        logging.debug("VIRTUAL NODE %s: Merging from %s LOCKS PRESENT", self.myID.name, simNodeName)

        # Lookup the local connection for this simulating node
        try:
            if not (simNodeName in self.config.hostDict):
                raise virtNetError(
                    "Trying to get conncetion to virtual node {}, but this is not in configuration file".format(
                        simNodeName
                    )
                )
            simNode = yield self.get_connection(simNodeName)
        except Exception as e:
            raise e

        # Fetch the details of the remote register and qubit, and remove sim qubits at node
        try:
            (R, I, activeQ, oldRegNum, oldQubitNum) = yield simNode.root.callRemote("get_register_del", simQubitNum)
        except RemoteError as remote_err:
            self.reraise_remote_error(remote_err)
        except Exception as err:
            raise err

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
            self.simQubits.append(newQubit)
            newD[k] = newQubit

        # Issue an update call to all nodes to update their virtual qubits if necessary
        # for name in self.conn:
        for name in self.config.hostDict:
            if name != self.myID.name:
                try:
                    nb = yield self.get_connection(name)
                except Exception as err:
                    raise err
                try:
                    yield nb.root.callRemote("update_virtual_merge", self.myID.name, simNodeName, oldRegNum, newD)
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)
                except Exception as err:
                    raise err

        # Locally, we might also already have virtual qubits which were in the remote simulated
        # register. Update them as well
        logging.debug("VIRTUAL NODE %s: Updating local virtual qubits.", self.myID.name)
        try:
            yield self.remote_update_virtual_merge(self.myID.name, simNodeName, oldRegNum, newD)
        except Exception as err:
            raise err

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

        logging.debug("VIRTUAL NODE %s: Request to update local virtual qubits.", self.myID.name)

        # If this is a third node (not involved in the two qubit gate, but carrying virtual qubits
        # which were in the simulated register), then they will now be updated. We remark that this function
        # can only be called from the _simulating node_ now handing over simulation to someone else. Both the simulating
        # node and the new simulating node are globally locked so there should be no conflicts here in updating:
        # a third node that may wish to do a 2 qubit gate between the qubits to be updated needs to wait.

        # Lookup the local connections for the given node names
        try:
            if not (newSimNodeName in self.config.hostDict):
                raise virtNetError(
                    "Trying to get conncetion to virtual node {}, but this is not in configuration file".format(
                        newSimNodeName
                    )
                )
            if not (oldSimNodeName in self.config.hostDict):
                raise virtNetError(
                    "Trying to get conncetion to virtual node {}, but this is not in configuration file".format(
                        oldSimNodeName
                    )
                )
            newSimNode = yield self.get_connection(newSimNodeName)
            oldSimNode = yield self.get_connection(oldSimNodeName)
        except Exception as e:
            raise e

        for q in self.virtQubits:
            if q.virtNode == q.simNode and q.simNode == oldSimNode:
                logging.debug("VIRTUAL NODE %s: Simulating node update.", self.myID.name)
                # We previously simulated this qubit ourselves
                givenReg = q.simQubit.register.num
                givenNum = q.simQubit.num
            elif q.simNode == oldSimNode:
                logging.debug("VIRTUAL NODE %s: Previously remote simulator node update.", self.myID.name)
                # We had the virtual qubit but it was simulated elsewhere
                try:
                    (givenNum, givenReg) = yield q.simQubit.callRemote("get_numbers")
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)
                except Exception as err:
                    raise err

            # Check if this qubit needs updating
            if q.simNode == oldSimNode and givenReg == oldRegNum:
                logging.debug(
                    "VIRTUAL NODE %s: Updating virtual qubit %d, previously %s now %s",
                    self.myID.name,
                    q.num,
                    oldSimNode.name,
                    newSimNode.name,
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
            realM, imagM = yield qubit.callRemote("get_register_RI")
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

        assert self._lock.locked

        # Locate the qubit object for this ID
        gotQ = None
        for q in self.simQubits:
            if q.simNum == qubitNum:
                gotQ = q

        # If nothing is found, return
        if gotQ is None:
            logging.debug("VIRTUAL NODE %s: No simulated qubit with ID %d.", qubitNum)
            return ([], [], 0, 0, 0)

        (realM, imagM) = gotQ.register.get_register_RI()
        activeQ = gotQ.register.activeQubits
        oldRegNum = gotQ.register.num
        oldQubitNum = gotQ.num
        delRegister = gotQ.register

        # Remove all simulated qubits and the register
        # Need to iterate of simQubits in reverse, otherwise wrong elements are removed
        for q in reversed(self.simQubits):
            if q.register.num == oldRegNum:
                self.simQubits.remove(q)
                # gotQ.register.activeQubits -= 1

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
            logging.error(
                "VIRTUAL NODE %s: Getting multiple qubits from multiple simulators is currently not supported.",
                self.myID.name,
            )
            return ([0], [0])

        if localSim:
            # Qubits are local, simply retrieve from the simulation
            nums = []
            for q in qList:
                nums.append(q.simQubit.simNum)
            logging.debug("VIRTUAL NODE %s: Looking for simulated qubits. %s", self.myID.name, nums)
            (R, I) = self.remote_get_state(nums)
        else:
            # Qubits are located elsewhere.
            nums = []
            for q in qList:
                try:
                    (num, name) = yield q.simQubit.callRemote("get_details")
                except RemoteError as remote_err:
                    self.reraise_remote_error(remote_err)
                except Exception as err:
                    raise err
                nums.append(num)
            try:
                (R, I) = yield qList[0].simNode.root.callRemote("get_state", nums)
            except RemoteError as remote_err:
                self.reraise_remote_error(remote_err)
            except Exception as err:
                raise err

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
                        logging.error(
                            "VIRTUAL NODE %s: Getting multiple qubits from different registers not supported.",
                            self.myID.name,
                        )
                        return ([], [])
                    prev = q
                    foundOne = True
                    traceList.append(q.num)
        if not foundOne:
            logging.error("VIRTUAL NODE %s: No such qubits found.", self.myID.name)
            return

        traceList.sort()
        (realM, imagM) = prev.register.get_qubits_RI(traceList)

        return (realM, imagM)


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

        if self.active != 1:
            logging.error("VIRTUAL NODE %s: Attempt to manipulate qubits no longer at this node.", self.virtNode.name)
            return False

        # Construct the name of the method to call if the qubit is locally simulated
        # in which case we (ironically) need to append the prefix remote which is automatically
        # added if the method is called from remote by Twisted
        localName = "".join(["remote_", name])

        # Check whether the qubit is local or remote. Due to remote register merges, this may change
        # while we try and get a lock. For this reason, we have to wait until we have a lock on an _active_
        # qubit before proceeding. If it is no longer active when we get the lock, then it has been
        # moved elsewhere in the meantime and we need to wait for the remote message to update the virtual
        # qubit object in the background.
        waiting = True
        outcome = False
        while waiting:
            if self.virtNode == self.simNode:
                if not self.simQubit.isLocked():
                    try:
                        yield self.simQubit.lock()
                        if self.simQubit.active:
                            getattr(self.simQubit, localName)(*args)
                            waiting = False
                            outcome = True
                    except Exception as e:
                        logging.error("VIRTUAL NODE {}: Cannot apply {} - {}".format(self.virtNode.name, e, name))
                        waiting = False
                    finally:
                        self.simQubit.unlock()
            else:
                try:
                    isLocked = yield self.simQubit.callRemote("isLocked")
                except RemoteError as remote_err:
                    self.virtNode.root.reraise_remote_error(remote_err)
                except Exception as err:
                    raise err
                if not isLocked:
                    try:
                        yield self.simQubit.callRemote("lock")
                        active = yield self.simQubit.callRemote("isActive")
                        if active:
                            logging.debug(
                                "VIRTUAL NODE %s: Calling %s remotely to apply %s.",
                                self.virtNode.name,
                                self.simNode.name,
                                name,
                            )
                            yield self.simQubit.callRemote(name, *args)
                            waiting = False
                            outcome = True
                    except Exception as e:
                        logging.error("VIRTUAL NODE %s: Cannot apply %s - %s", e, name)
                        waiting = False
                    finally:
                        yield self.simQubit.callRemote("unlock")

            # If we did not get a lock on an active qubit, wait for update and try again
            if waiting:
                try:
                    yield deferLater(reactor, self.virtNode.root._delay, lambda: None)
                except Exception as err:
                    raise err

        return outcome

    @inlineCallbacks
    def remote_apply_X(self):
        """
        Apply X gate to itself by passing it onto the underlying register.
        """
        try:
            success = yield self._single_gate("apply_X")
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_apply_Y(self):
        """
        Apply Y gate.
        """
        try:
            success = yield self._single_gate("apply_Y")
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_apply_Z(self):
        """
        Apply Z gate.
        """
        try:
            success = yield self._single_gate("apply_Z")
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_apply_H(self):
        """
        Apply H gate.
        """
        try:
            success = yield self._single_gate("apply_H")
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_apply_K(self):
        """
        Apply K gate - taking computational basis to Y eigenbasis.
        """
        try:
            success = yield self._single_gate("apply_K")
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_apply_T(self):
        """
        Apply T gate.
        """
        try:
            success = yield self._single_gate("apply_T")
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_apply_rotation(self, n, a):
        """
        Apply rotation around axis n with angle a.
        Arguments:
        n	A tuple of three numbers specifying the rotation axis, e.g n=(1,0,0)
        a	The rotation angle in radians.
        """
        try:
            success = yield self._single_gate("apply_rotation", n, a)
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_measure(self, inplace=False):
        """
        Measure the qubit in the standard basis. If inplace=False, this does delete the qubit from the simulation.

        Returns the measurement outcome.
        """

        if self.active != 1:
            logging.error("VIRTUAL NODE %s: Attempt to manipulate qubits no longer at this node.", self.virtNode.name)
            return

        # Check whether the qubit is local or remote. Due to remote register merges, this may change
        # while we try and get a lock. For this reason, we have to wait until we have a lock on an _active_
        # qubit before proceeding.
        waiting = True
        outcome = None
        while waiting:
            if self.virtNode == self.simNode:
                if not self.simQubit.isLocked():
                    try:
                        yield self.simQubit.lock()
                        if self.simQubit.active:
                            logging.debug("VIRTUAL NODE %s: Measuring local qubit", self.virtNode.name)
                            outcome = self.simQubit.remote_measure_inplace()
                            if not inplace:
                                self.virtNode.root._remove_sim_qubit(self.simQubit)

                                # Delete from virtual qubits
                                self.virtNode.root.virtQubits.remove(self)
                            waiting = False
                    except Exception as e:
                        logging.error(
                            "VIRTUAL NODE {}: Cannot remove local qubit. Error: {}".format(self.virtNode.name, e)
                        )
                        waiting = False
                    finally:
                        self.simQubit.unlock()
            else:
                try:
                    isLocked = yield self.simQubit.callRemote("isLocked")
                except RemoteError as remote_err:
                    self.virtNode.root.reraise_remote_error(remote_err)
                except Exception as err:
                    raise err
                if not isLocked:
                    try:
                        yield self.simQubit.callRemote("lock")
                        active = yield self.simQubit.callRemote("isActive")
                        if active:
                            logging.debug(
                                "VIRTUAL NODE %s: Measuring remote qubit at %s.", self.virtNode.name, self.simNode.name
                            )
                            outcome = yield self.simQubit.callRemote("measure_inplace")
                            if not inplace:
                                num = yield self.simQubit.callRemote("get_sim_number")
                                yield self.simNode.root.callRemote("remove_sim_qubit_num", num)

                                # Delete from virtual qubits
                                self.virtNode.root.virtQubits.remove(self)
                            waiting = False
                    except Exception as e:
                        logging.error(
                            "VIRTUAL NODE {}: Cannot remove remote qubit. Error: {}".format(self.virtNode.name, e)
                        )
                        waiting = False
                    finally:
                        yield self.simQubit.callRemote("unlock")

            # If we did not get a lock on an active qubit, wait for update and try again
            if waiting:
                try:
                    yield deferLater(reactor, self.virtNode.root._delay, lambda: None)
                except Exception as err:
                    raise err

        return outcome

    def _lock_nodes(self, target):
        """
        Wrapper to acquire the global register lock on both nodes that involve the qubits, and local node.

        Arguments
        target		virtual qubit of the target qubit

        """
        lockedLocal = False
        lockedRemoteTarget = False

        # Lock qubits nodes
        if self.simNode == self.virtNode:
            # first qubit is locally simulated
            def1 = self.simNode.root._get_global_lock()
            lockedLocal = True
        else:
            # first qubit is remote
            def1 = self.simNode.root.callRemote("get_global_lock")

        # If target is a different node
        if target.simNode != self.simNode:
            if target.simNode == target.virtNode:
                # target qubit is local
                def2 = target.simNode.root._get_global_lock()
                lockedLocal = True
            else:
                # target qubit is remote
                def2 = target.simNode.root.callRemote("get_global_lock")
                lockedRemoteTarget = True

        if not lockedLocal:
            def0 = self.virtNode.root._get_global_lock()

            if lockedRemoteTarget:
                return DeferredList([def0, def1, def2], fireOnOneCallback=False, consumeErrors=True)
            else:
                return DeferredList([def0, def1], fireOnOneCallback=False, consumeErrors=True)
        else:
            if lockedRemoteTarget:
                return DeferredList([def1, def2], fireOnOneCallback=False, consumeErrors=True)
            else:
                return DeferredList([def1], fireOnOneCallback=False, consumeErrors=True)

    @inlineCallbacks
    def _unlock_nodes(self, q1simNode, q1virtNode, q2simNode, q2virtNode):
        """
        Wrapper to acquire the global register lock on both nodes that involve the qubits. This takes different
        arguments as lock nodes since we wish to call it with the _original_ simulated and target nodes from
        which we got the lock - not the updated ones.

        Arguments
        q1simNode	original simulating node of the first qubit
        q1virtNode	original virtual node of the first qubit
        q2simNode	original simulating node of the second qubit
        q2virtNode	original virtual node of the second qubit

        """

        try:
            # Release qubit node locks
            if q1simNode == q1virtNode:
                # first qubit was locally simulated
                yield self.simNode.root._release_global_lock()
            else:
                # first qubit was remote
                yield q1simNode.root.callRemote("release_global_lock")

            # If target was a different node
            if q1simNode != q2simNode:
                if q2simNode == q2virtNode:
                    # target qubit was local
                    yield q2simNode.root._release_global_lock()
                else:
                    # target qubit was remote
                    yield q2simNode.root.callRemote("release_global_lock")

            # Release local node (may be the same as above)
            self.virtNode.root._release_global_lock()
        except RemoteError as remote_err:
            self.virtNode.root.reraise_remote_error(remote_err)
        except Exception as err:
            raise err

    @inlineCallbacks
    def _lock_inreg(self, qubit):
        """
        Lock all qubits in the same register as the virtual qubit qubit.
        """

        try:
            if qubit.simNode == qubit.virtNode:
                yield qubit.simNode.root._lock_reg_qubits(qubit.simQubit)
            else:
                simNum = yield qubit.simQubit.callRemote("get_sim_number")
                yield qubit.simNode.root.callRemote("lock_reg_qubits", simNum)
        except RemoteError as remote_err:
            self.virtNode.root.reraise_remote_error(remote_err)
        except Exception as err:
            raise err

    @inlineCallbacks
    def _unlock_inreg(self, qubit):
        """
        Lock all qubits in the same register as the virtual qubit qubit.
        """

        try:
            if qubit.simNode == qubit.virtNode:
                yield qubit.simNode.root._unlock_reg_qubits(qubit.simQubit)
            else:
                simNum = yield qubit.simQubit.callRemote("get_sim_number")
                yield qubit.simNode.root.callRemote("unlock_reg_qubits", simNum)
        except RemoteError as remote_err:
            self.virtNode.root.reraise_remote_error(remote_err)
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_cnot_onto(self, target):
        """
        Performs a CNOT operation with this qubit as control, and the other qubit as target.

        Arguments
        target		the virtual qubit to use as the target of the CNOT
        """

        try:
            success = yield self._two_qubit_gate(target, "cnot_onto")
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def remote_cphase_onto(self, target):
        """
        Performs a CPHASE operation with this qubit as control, and the other qubit as target.

        Arguments
        target		the virtual qubit to use as the target of the CPHASE
        """

        try:
            success = yield self._two_qubit_gate(target, "cphase_onto")
            return success
        except Exception as err:
            raise err

    @inlineCallbacks
    def _two_qubit_gate(self, target, name):
        """
        Perform a two qubit gate including all the required locking.

        Arguments
        target		second virtual qubit (beyond self which is the first)
        name		name of the gate to perform
        """

        if self.active != 1 or target.active != 1:
            logging.error("VIRTUAL NODE %s: Attempt to manipulate qubits no longer at this node.", self.virtNode.name)
            return

        localName = "".join(["remote_", name])
        logging.debug(
            "VIRTUAL NODE %s: Doing 2 qubit gate name %s and local call %s", self.virtNode.name, name, localName
        )

        # Before we proceed, we need to acquire the gobal locks of the nodes holding the
        # registers of both qubits. We wrap this in a timeout with random repeat since there is
        # otherwise the possibility of a deadlock if two nodes compete for the _two_ locks
        waiting = True
        attempts = 0
        try:
            while waiting and attempts <= self.virtNode.root.maxAttempts:

                # Set up the timeout at a random time between 1s and 4s later
                timeoutD = Deferred()
                timeup = reactor.callLater(random.uniform(1, 4), timeoutD.callback, None)

                # Check if self simNode is locked
                if self.simNode == self.virtNode:
                    self_isLocked = self.simNode.root._lock.locked
                else:
                    self_isLocked = yield self.simNode.root.callRemote("isLocked")
                # Check if other simNode is locked
                if target.simNode == target.virtNode:
                    other_isLocked = target.simNode.root._lock.locked
                else:
                    other_isLocked = yield target.simNode.root.callRemote("isLocked")

                if self_isLocked:
                    logging.debug(
                        "VIRTUAL NODE {}: This SimNode {} already locked. Need to wait.".format(
                            self.virtNode.name, self.simNode.name
                        )
                    )
                    yield timeoutD
                    attempts += 1
                elif other_isLocked:
                    logging.debug(
                        "VIRTUAL NODE {}: Other SimNode {} already locked. Need to wait.".format(
                            self.virtNode.name, target.simNode.name
                        )
                    )
                    yield timeoutD
                    attempts += 1

                else:

                    # Set up the lock acquisition
                    lockD = self._lock_nodes(target)

                    try:
                        # Yield on both of them
                        gotLock, timeoutRes = yield DeferredList(
                            [lockD, timeoutD], fireOnOneCallback=True, fireOnOneErrback=True, consumeErrors=True
                        )
                    except Exception as e:
                        logging.debug("VIRTUAL NODE %s: Cannot get lock %s", self.virtNode.name, e)
                        yield self._unlock_nodes(self.simNode, self.virtNode, target.simNode, target.virtNode)
                        timeup.cancel()
                        return
                    else:
                        if timeoutD.called:
                            logging.debug("VIRTUAL NODE %s: Timing out getting locks.", self.virtNode.name)
                            lockD.cancel()
                            yield self._unlock_nodes(self.simNode, self.virtNode, target.simNode, target.virtNode)
                            attempts = attempts + 1
                        elif lockD.called:
                            waiting = False
                            timeup.cancel()
        except RemoteError as remote_err:
            self.virtNode.root.reraise_remote_error(remote_err)
        except Exception as err:
            raise err

        # We have now acquired the two relevant global node locks. If more than one qubit is locked, all code
        # will first acquire the global lock, so this should be safe from deadlocks now, so we will not timeout

        try:
            yield self._lock_inreg(self)
            yield self._lock_inreg(target)
        except Exception as err:
            raise err

        # When merging registers, we may need to update the virtual qubits. Remember the original ones so we can
        # send appropriate unlocks below. (note this assignment must be done after the locks are acquired)
        q1simNode = self.simNode
        q1virtNode = self.virtNode
        q2simNode = target.simNode
        q2virtNode = target.virtNode

        # Todo a 2 qubit gate, both qubits must be in the same simulated register. We will merge
        # registers if this is not already the case.
        try:
            if self.simNode == target.simNode:
                # Both qubits are simulated at the same node

                if self.simNode == self.virtNode:
                    # Both qubits are both locally simulated, check whether they are in the same register

                    if self.simQubit.register == target.simQubit.register:
                        # They are even in the same register, just do the gate
                        getattr(self.simQubit, localName)(target.simQubit.num)
                    else:
                        logging.debug("VIRTUAL NODE %s: 2qubit command demands register merge.", self.virtNode.name)
                        # Both are local but not in the same register
                        self.simNode.root.local_merge_regs(self.simQubit, target.simQubit)

                        # After the merge, just do the gate
                        getattr(self.simQubit, localName)(target.simQubit.num)
                else:
                    # Both are remotely simulated
                    logging.debug("VIRTUAL NODE %s: 2qubit command demands remote register merge.", self.virtNode.name)

                    # Fetch the details of the two simulated qubits from remote
                    (fNum, fNode) = yield self.simQubit.callRemote("get_details")
                    (tNum, tNode) = yield target.simQubit.callRemote("get_details")

                    # Sanity check: we really have the right simulating node
                    if fNode != self.simNode.name or tNode != target.simNode.name:
                        logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.", self.myID.name)
                        raise quantumError("Inconsistent simulation")

                    # Merge the remote register according to the simulation IDs of the qubits
                    yield self.simNode.root.callRemote("merge_regs", fNum, tNum)

                    # Get the number of the target in the new register
                    targetNum = yield target.simQubit.callRemote("get_number")

                    # Execute the 2 qubit gate
                    yield self.simQubit.callRemote(name, targetNum)
                    logging.debug(
                        "VIRTUAL NODE %s: Remote 2qubit command to %s.", self.virtNode.name, target.simNode.name
                    )
            else:
                # They are simulated at two different nodes

                if self.simNode == self.virtNode:

                    # We are the locally simulating node of the first qubit, merge all to us
                    logging.debug(
                        "VIRTUAL NODE %s: 2qubit command demands merge from remote target sim %s to us.",
                        self.simNode.name,
                        target.simNode.name,
                    )
                    (fNum, fNode) = yield target.simQubit.callRemote("get_details")
                    if fNode != target.simNode.name:
                        logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.", self.myID.name)
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
                    logging.debug(
                        "VIRTUAL NODE %s: 2qubit command demands merge from remote sim %s to us.",
                        target.simNode.name,
                        self.simNode.name,
                    )
                    (fNum, fNode) = yield self.simQubit.callRemote("get_details")
                    if fNode != self.simNode.name:
                        logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.", self.myID.name)
                        raise quantumError("Inconsistent simulation.")
                    self.simQubit = yield target.simNode.root.remote_merge_from(
                        self.simNode.name, fNum, target.simQubit.register
                    )

                    # Get the number of the target in the new register
                    targetNum = target.simQubit.num

                    # Execute the 2 qubit gate
                    getattr(self.simQubit, localName)(targetNum)

                else:
                    # Both qubits are remotely simulated - we will pull both registers to become one local register
                    logging.debug(
                        "VIRTUAL NODE %s: 2qubit command demands total remote merge from %s and %s.",
                        self.virtNode.name,
                        target.simNode.name,
                        self.simNode.name,
                    )

                    # Create a new local register
                    newLocalReg = self.virtNode.root.remote_add_register()

                    # Fetch the detail of the two registers from remote
                    (fNum, fNode) = yield self.simQubit.callRemote("get_details")
                    if fNode != self.simNode.name:
                        logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.", self.myID.name)
                        raise quantumError("Inconsistent simulation.")
                    (tNum, tNode) = yield target.simQubit.callRemote("get_details")
                    if tNode != target.simNode.name:
                        logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.", self.myID.name)
                        raise quantumError("Inconsistent simulation.")

                    # Pull the remote registers to this node
                    self.simQubit = yield self.virtNode.root.remote_merge_from(self.simNode.name, fNum, newLocalReg)
                    target.simQubit = yield target.virtNode.root.remote_merge_from(
                        target.simNode.name, tNum, newLocalReg
                    )
                    # Get the number of the target in the new register
                    targetNum = target.simQubit.num

                    # Finally, execute the two qubit gate
                    logging.debug("RUN GATE")
                    getattr(self.simQubit, localName)(targetNum)
        except RemoteError as remote_err:
            self.virtNode.root.reraise_remote_error(remote_err)
        except Exception as e:
            logging.error("VIRTUAL NODE %s: Cannot perform two qubit gate %s:", self.virtNode.name, e)
            raise e

        finally:
            # We need to release all the locks, no matter what happened
            yield self._unlock_inreg(self)
            yield self._unlock_inreg(target)
            yield self._unlock_nodes(q1simNode, q1virtNode, q2simNode, q2virtNode)

        return True

    @inlineCallbacks
    def remote_get_number(self):
        """
        Returns the number of this qubit in whatever local register it is in. Not useful for the client,
        but convenient for debugging.
        """

        if self.active != 1:
            logging.error("VIRTUAL NODE %s: Attempt to manipulate qubits no longer at this node.", self.virtNode.name)

        if self.virtNode == self.simNode:
            num = self.simQubit.num
        else:
            try:
                num = yield self.simQubit.callRemote("get_number")
            except ConnectionError:
                logging.error("VIRTUAL NODE %s: Connection failed: cannot get qubit number.")
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
            logging.error("VIRTUAL NODE %s: Attempt to manipulate qubits no longer at this node.", self.virtNode.name)

        if self.virtNode == self.simNode:
            (R, I) = self.simQubit.remote_get_qubit()
        else:
            try:
                try:
                    (R, I) = yield self.simQubit.callRemote("get_qubit")
                except RemoteError as remote_err:
                    self.virtNode.root.reraise_remote_error(remote_err)
            except ConnectionError:
                logging.error("VIRTUAL NODE %s: Connection failed: cannot get qubit number.")
            except Exception as err:
                raise err

        return (R, I)

    @inlineCallbacks
    def remote_get_register_RI(self):
        if self.simNode == self.virtNode:
            realM, imagM = self.simQubit.register.get_register_RI()
        else:
            realM, imagM = yield self.simQubit.callRemote("get_register_RI")
        return realM, imagM


############################################
#
# Keeping track of received qubits for CQC


class QubitCQC:
    def __init__(self, fromName, toName, from_app_id, to_app_id, new_virt_num, rawEntInfo=None):
        self.fromName = fromName
        self.toName = toName
        self.from_app_id = from_app_id
        self.to_app_id = to_app_id
        self.virt_num = new_virt_num
        self.rawEntInfo = rawEntInfo

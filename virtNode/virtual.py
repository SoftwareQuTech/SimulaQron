#
# Copyright (c) 2017, Stephanie Wehner
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

from collections import dqueue

from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred, DeferredList
from twisted.internet.task import deferLater

from SimulaQron.virtNode.basics import *
from SimulaQron.virtNode.quantum import *
from SimulaQron.general.hostConfig import *
from SimulaQron.virtNode.crudeSimulator import *

import logging
import random

######
#
# backEnd - starts the local virtual node and connects to the other virtual nodes
# forming the quantum network
#
class backEnd(object):

	def __init__(self, name, configName):
		"""
		Initialize. This will read the configuration file and populate the name,hostname,port information with the
		information found in the configuration file for the given name.
		"""

		# Read the configuration file
		self.config = networkConfig(configName)
		self.myID = self.config.hostDict[name]

	def start(self, maxQubits = 10):
		"""
		Start listening to requests from other nodes.

		Arguments
		maxQubits	maximum qubits in the default register
		"""

		logging.debug("VIRTUAL NODE %s: Starting on port %d", self.myID.name, self.myID.port)
		node = virtualNode(self.myID, self.config)
		reactor.listenTCP(self.myID.port, pb.PBServerFactory(node))

		logging.debug("VIRTUAL NODE %s: running reactor.", self.myID.name)
		reactor.run()

#######
#
# virtualNode - this is the virtual quantum node. It keeps track of registers simulated here, qubits
# virtually available at this node, etc
#


class virtualNode(pb.Root):

	def __init__(self,ID, config, maxQubits = 10, maxRegisters=1000):
		"""
		Initialize storing also our own name, hostname and port.

		Arguments:
		ID		host identifier of this node
		maxQubits	maximum number of qubits to use in the default engine (default 10)
		maxRegister	maximum number of registers
		"""

		# Store our own host identifiers and configuration
		self.myID = ID
		self.myID.root = self
		self.config = config

		# Initialize list of registers we simulate locally
		# self.simRegisters = []
		self.maxRegs = maxRegisters

		# List of connections
		self.conn = {}

		# Number of registers _created_ at this node
		# this may not equal the numbers of registers virtually carried
		self.numRegs = 0

		# Set up the default local register
		self.defaultReg = self.remote_new_register(maxQubits)

		# Initialize the list of qubits at this node
		self.virtQubits = []
		self.simQubits = []

		# Set up connections to the neighouring nodes in the network
		# Wait so servers have time to start
		reactor.callLater(2,self.connectNet)

		# Global lock: needs to be acquire whenever we want to manipulate more than one
		# qubit object
		self._lock = DeferredLock()

		# Time until retry
		self._delay = 1

		# Maximum number of attempts at getting locks
		self.maxAttempts = 300

	def remote_test(self):
		logging.debug("VIRTUAL NODE %s: Check call virtualNode.", self.myID.name)

	def remote_test_arg(self,  newSimNodeName, oldSimNodeName, oldRegNum, newD):
		# logging.debug("VIRTUAL NODE %s: Check call virtualNode %s.", self.myID.name, arg)
		logging.debug("VIRTUAL NODE %s: Check call virtualNode %s.", self.myID.name, newSimNodeName)

	def connectNet(self):
		"""
		Initialize the connections to the other virtual nodes in the network according to the available
		configuration.
		"""

		for key in self.config.hostDict:
			nb = self.config.hostDict[key]
			if nb.name != self.myID.name:
				logging.debug("VIRTUAL NODE %s: Attempting connection to node %s at %s:%d",self.myID.name,nb.name,nb.hostname,nb.port)
				nb.factory = pb.PBClientFactory()
				reactor.connectTCP(nb.hostname, nb.port, nb.factory)
				defer = nb.factory.getRootObject()
				defer.addCallback(self._gotRoot, nb)
				defer.addErrback(self._setupError)
			else:
				self.conn[nb.name] = nb

	def _gotRoot(self, obj, nb):
		"""
		Callback obtaining twisted root object when connection to the node given by the node details nb.
		"""
		logging.debug("VIRTUAL NODE %s: New connection to %s.",self.myID.name,nb.name)
		# Retrieve the root object: virtualNode on the remote
		nb.root = obj;

		# Add this node to the local connections
		self.conn[nb.name] = nb

	def _setupError(self):
		"""
		Callback error
		"""
		logging.critical("Cannot connect to node")
		reactor.stop()
		return

	def get_virtual_id(self):
		"""
		This is a crude and horrible cludge to generate unique IDs for virtual qubits.
		"""

		# Loop through the firt k numbers where k is the number of virtual qubits + 1
		# Note that this is guaranteed to find a an index which is not yet used
		for j in range(len(self.virtQubits)+1):
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
		for j in range(len(self.simQubits)+1):
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

	@inlineCallbacks
	def _get_global_lock(self):
		logging.debug("VIRTUAL NODE %s: Local GETTING LOCK",self.myID.name)
		yield self._lock.acquire()
		logging.debug("VIRTUAL NODE %s: Local GOT LOCK",self.myID.name)

	@inlineCallbacks
	def remote_get_global_lock(self):
		logging.debug("VIRTUAL NODE %s: Remote GETTING LOCK",self.myID.name)
		yield self._lock.acquire()
		logging.debug("VIRTUAL NODE %s: Remote GOT LOCK",self.myID.name)

	@inlineCallbacks
	def _release_global_lock(self):
		logging.debug("VIRTUAL NODE %s: Local RELEASE LOCK",self.myID.name)
		if self._lock.locked:
			yield self._lock.release()


	@inlineCallbacks
	def remote_release_global_lock(self):
		logging.debug("VIRTUAL NODE %s: Remote RELEASE LOCK",self.myID.name)
		if self._lock.locked:
			yield self._lock.release()

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
				if q._lock.locked:
					yield q.unlock()

	@inlineCallbacks
	def remote_unlock_reg_qubits(self, qubitNum):
		"""
		Release the lock on all qubits in the same register as qubitNum.
		"""

		yield self._unlock_reg_qubits(self._q_num_to_obj(qubitNum))

	def remote_new_register(self, maxQubits = 10):
		"""
		Initialize a local register. Right now, this simple creates a register according to the simple engine backend
		using qubit.

		Arguments:
		maxQubits	maximum number of qubits to use in the default engine (default 10)
		"""

		if self.numRegs >= self.maxRegs:
			logging.error("%s: Maximum number of registers reached.",self.myID.name)
			raise quantumError("Maximum number of registers reached.")

		self.numRegs = self.numRegs + 1
		newReg = quantumRegister(self.myID, self.numRegs, maxQubits)
		# self.simRegisters.append(newReg)

		logging.debug("VIRTUAL NODE %s: Initializing new simulated register.",self.myID.name)
		return newReg

	@inlineCallbacks
	def remote_new_qubit(self):
		"""
		Create a new qubit in the default local register.
		"""
		logging.debug("%s: Request to create new qubit.", self.myID.name)

		try:
			# Get a lock to assure IDs are assigned correctly
			yield self._get_global_lock()

			# Qubit in the simulation backend, initialized to |0>
			simNum = self.get_sim_id()
			simQubit = simulatedQubit(self.myID, self.defaultReg, simNum)
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

		try:
			# Get a lock to assure IDs are assigned correctly
			yield self._get_global_lock()

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

	def remote_reset_reg(self, reg):
		"""
		Reset the simulated register, including removing all simulated qubits. Caution: this does not
		update remote nodes XXX
		"""
		pass

	@inlineCallbacks
	def remote_cqc_send_qubit(self, qubit, targetName, app_id, remote_app_id):
		"""
		Send interface for CQC to add the qubit to the remote nodes received list for an application. 
		"""
		
		oldVirtNum = qubit.num
		newVirtNum = self.remote_send_qubit(qubit, targetName)

		# Lookup host ID of node
		remoteNode = self.conn[targetName]
		
		# Ask to add to list
		yield remoteNode.root.callRemote("cqc_add_recv_list", self.myID.name, app_id, remote_app_id, newVirtNum)

	def remote_cqc_add_recv_list(self, fromName, from_app_id, to_app_id, new_virt_num):
		"""
		Add an item to the received list for use in CQC.
		"""

		if not self.cqcRecv[to_app_id]:
			self.cqcRecv[to_app_id] = dqueue([])

		self.cqcRecv[to_app_id].append(QubitCQC(fromName, self.myID.name, from_app_id, to_app_id, new_virt_num));

	def remote_cqc_get_recv(self, fromName, to_app_id):
		"""
		Retrieve the next qubit with the given app ID form the received list.
		"""

		# Get the list corresponding to the specified application ID
		qQueue = self.cqcRecv[to_app_id]
		if not qQueue:
			return None

		# Retrieve the first element on that list (first in, first out)
		qc = qQueue.popleft();
		if not qc:
			return None
		
		return self.remote_get_virtual_ref(qc.virt_num)


	@inlineCallbacks
	def remote_send_qubit(self, qubit, targetName):
		"""
		Sends the qubit to the specified target node. This creates a new virtual qubit object at the remote node
		with the right qubit and backend details.

		Arguments
		qubit		virtual qubit to be sent
		targetName	target ndoe to place qubit at (host object)
		"""

		if qubit.active != 1:
			logging.debug("VIRTUAL NODE %s: Attempt to manipulate qubit no longer at this node.",self.myID.name)
			return

		logging.debug("VIRTUAL NODE %s: Request to transfer qubit sim Num %d to %s.",self.myID.name,qubit.num, targetName)

		# Lookup host id of node
		remoteNode = self.conn[targetName]

		# Check whether we are just the virtual, or also the simulating node
		if qubit.virtNode == qubit.simNode:
			# We are both the virtual as well as the simulating node
			# Pass a reference to our locally simulated qubit object to the remote node
			newNum = yield remoteNode.root.callRemote("add_qubit", self.myID.name, qubit.simQubit)
		else:
			# We are only the virtual node, not the simulating one. In this case, we need to ask
			# the actual simulating node to do the transfer for us.
			newNum = yield qubit.simNode.root.callRemote("transfer_qubit", qubit.simQubit, targetName)

		# We gave it away to mark as inactive
		qubit.active = 0

		# Remove the qubit from the local virtual list. Note it remains in the simulated
		# list, since we continue to simulate this qubit.
		self.virtQubits.remove(qubit)

		return newNum

	@inlineCallbacks
	def remote_transfer_qubit(self, simQubit, targetName):
		"""
		Transfer the qubit to the destination node if we are the simulating node. The reason why we cannot
		do this directly is that Twisted PB does not allow objects to be passed between connecting nodes.
		Only between the creator of the object and its immediate connections.

		Arguments
		simQubit	simulated qubit to be sent
		targetName	target node to place qubit at (host object)
		"""

		logging.debug("VIRTUAL NODE %s: Request to transfer qubit to %s.",self.myID.name, targetName)

		# Lookup host id of node
		remoteNode = self.conn[targetName]
		newNum = yield remoteNode.root.callRemote("add_qubit", self.myID.name, simQubit)

		return newNum

	def remote_add_qubit(self, name, qubit):
		"""
		Add a qubit to the local virtual node.

		Arguments
		name		name of the node simulating this qubit
		qubit		qubit reference in the backend we're adding
		"""

		logging.debug("VIRTUAL NODE %s: Request to add qubit from %s.",self.myID.name, name)

		# Get the details of the remote node
		nb = self.conn[name]

		try:
			# Get a lock to make sure IDs are assigned correctly
			self._get_global_lock()

			# Generate a new virtual qubit object for the qubit now at this node
			newNum = self.get_virtual_id()
			newQubit = virtualQubit(self.myID, nb, qubit, newNum)

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
		if not delQubit in self.simQubits:
			logging.error("VIRTUAL NODE %s: Attempt to delete qubit not simulated at this node.",self.myID.name)
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

			# When removing a qubit, we need to update the positions of the qubits in the underlying physical register
			# in all relevant qubit objects.
			for q in self.simQubits:
				# If they are in the same engine, and update is required
				if q.register == delRegister:
					if q.num > delNum:
						q.num = q.num - 1
			# Remove the qubit form the list of simulated qubits
			self.simQubits.remove(delQubit)

		except Exception as e:
			logging.error("VIRTUAL NODE %s: Cannot remove sim qubit - %s",self.myID.name, e.strerror)
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
		logging.debug("VIRTUAL NODE %s: Request to merge local register for qubits simNum %d and simNum %d.",self.myID.name, qubit1.simNum, qubit2.simNum)

		# This should only be called if locks are acquired
		assert qubit1._lock.locked
		assert qubit2._lock.locked
		assert self._lock.locked

		logging.debug("VIRTUAL NODE %s: Request to merge LOCKS PRESENT", self.myID.name)

		reg1 = qubit1.register
		reg2 = qubit2.register

		# Check if there's anything to do at all
		if reg1 == reg2:
			logging.debug("VIRTUAL NODE %s: Request to merge local register: not required",self.myID.name)
			return

		logging.debug("VIRTUAL NODE %s: Request to merge local register: need merge",self.myID.name)

		# Allow reg 1 to absorb reg 2
		reg1.maxQubits = reg1.maxQubits + reg2.activeQubits

		# Add reg2 to reg1
		reg1.absorb(reg2)

		# For relabelling qubit numbers get the offset
		offset = reg1.activeQubits - 1

		# Update the simulated qubit numbering and register
		for q in self.simQubits:
			if q.register == reg2:
				logging.debug("VIRTUAL NODE %s: Updating register %d to %d.", self.myID.name,q.num, q.num+offset)
				q.register = reg1
				q.num = q.num + offset

		reg2.reset()

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
		simNode = self.conn[simNodeName]

		# Fetch the details of the remote register and qubit, and remove sim qubits at node
		(R, I, activeQ, oldRegNum, oldQubitNum) = yield simNode.root.callRemote("get_register_del",simQubitNum)

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
		for name in self.conn:
			if name != self.myID.name:
				nb = self.conn[name]
				yield nb.root.callRemote("update_virtual_merge",self.myID.name, simNodeName, oldRegNum, newD)

		# Locally, we might also already have virtual qubits which were in the remote simulated
		# register. Update them as well
		logging.debug("VIRTUAL NODE %s: Updating local virtual qubits.",self.myID.name)
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

		logging.debug("VIRTUAL NODE %s: Request to update local virtual qubits.",self.myID.name)

		# If this is a third node (not involved in the two qubit gate, but carrying virtual qubits
		# which were in the simulated register), then they will now be updated. We remark that this function
		# can only be called from the _simulating node_ now handing over simulation to someone else. Both the simulating
		# node and the new simulating node are globally locked so there should be no conflicts here in updating:
		# a third node that may wish to do a 2 qubit gate between the qubits to be updated needs to wait.

		# Lookup the local connections for the given node names
		newSimNode = self.conn[newSimNodeName]
		oldSimNode = self.conn[oldSimNodeName]

		for q in self.virtQubits:
			if q.virtNode == q.simNode and q.simNode == oldSimNode:
				logging.debug("VIRTUAL NODE %s: Simulating node update.",self.myID.name)
				# We previously simulated this qubit ourselves
				givenReg = q.simQubit.register.num
				givenNum = q.simQubit.num
			elif q.simNode == oldSimNode:
				logging.debug("VIRTUAL NODE %s: Previously remote simulator node update.",self.myID.name)
				# We had the virtual qubit but it was simulated elsewhere
				(givenNum, givenReg) = yield q.simQubit.callRemote("get_numbers")

			# Check if this qubit needs updating
			if q.simNode == oldSimNode and givenReg == oldRegNum:
				logging.debug("VIRTUAL NODE %s: Updating virtual qubit %d, previously %s now %s",self.myID.name,q.num, oldSimNode.name,newSimNode.name)
				q.simNode = newSimNode
				q.simQubit = newD[givenNum]

	def remote_get_register(self, qubit):
		"""
		Return the value of of a locally simulated register which contains this virtual qubit.

		"""

		# XXX Move to virtual qubit?
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
		if gotQ == None:
			logging.debug("VIRTUAL NODE %s: No simulated qubit with ID %d.",qubitNum)
			return([],[],0,0,0)

		(realM, imagM) = gotQ.register.get_register_RI()
		activeQ = gotQ.register.activeQubits
		oldRegNum = gotQ.register.num
		oldQubitNum = gotQ.num

		# Remove all simulated qubits and the register
		for q in self.simQubits:
			if q.register.num == oldRegNum:
				self.simQubits.remove(q)
				toRemove = q.register

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
			logging.error("VIRTUAL NODE %s: Getting multiple qubits from multiple simulators is currently not supported.",self.myID.name)
			return ([0],[0])

		if localSim:
			# Qubits are local, simply retrieve from the simulation
			nums = []
			for q in qList:
				nums.append(q.simQubit.simNum)
			logging.debug("VIRTUAL NODE %s: Looking for simulated qubits. %s",self.myID.name, nums)
			(R,I) = self.remote_get_state(nums)
		else:
			# Qubits are located elsewhere.
			nums = []
			for q in qList:
				(num,name) = yield q.simQubit.callRemote("get_details")
				nums.append(num)
			(R,I) = yield qList[0].simNode.root.callRemote("get_state", nums)

		return (R,I)

	def remote_get_state(self, simNumList):
		"""
		Return the state of multiple qubits corresponding to the IDs in simNumList.
		"""

		# Convert simulation numbers to register and real number in register
		traceList = []
		foundOne = False
		prevReg = None
		for n in simNumList:
			for q in self.simQubits:
				if q.simNum == n:
					if foundOne == True and prev.register != q.register:
						logging.error("VIRTUAL NODE %s: Getting multiple qubits from different registers not supported.",self.myID.name)
						return ([],[])
					prev = q
					foundOne = True
					traceList.append(q.num)
		if not foundOne:
			logging.error("VIRTUAL NODE %s: No such qubits found.",self.myID.name)
			return

		traceList.sort()
		(realM, imagM) = prev.register.get_qubits_RI(traceList)

		return(realM, imagM)


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


	def remote_test(self):
		logging.debug("VIRTUAL NODE %s: Check call.", self.virtNode.name)

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
		localName = ''.join(["remote_",name])

		# Check whether the qubit is local or remote. Due to remote register merges, this may change
		# while we try and get a lock. For this reason, we have to wait until we have a lock on an _active_
		# qubit before proceeding. If it is no longer active when we get the lock, then it has been
		# moved elsewhere in the meantime and we need to wait for the remote message to update the virtual
		# qubit object in the background.
		waiting = True
		outcome = False
		while(waiting):
			if self.virtNode == self.simNode:
				try:
					yield self.simQubit.lock()
					if self.simQubit.active:
						getattr(self.simQubit, localName)(*args)
						waiting = False
						outcome = True
				except Exception as e:
					logging.error("VIRTUAL NODE %s: Cannot apply %s - %s", e, name)
					waiting = False
				finally:
					self.simQubit.unlock()
			else:
				try:
					defer = yield self.simQubit.callRemote("lock")
					active = yield self.simQubit.callRemote("isActive")
					if active:
						logging.debug("VIRTUAL NODE %s: Calling %s remotely to apply %s.",self.virtNode.name, self.simNode.name, name)
						defer = yield self.simQubit.callRemote(name,*args)
						waiting = False
						outcome = True
				except Exception as e:
					logging.error("VIRTUAL NODE %s: Cannot apply %s - %s", e, name)
					waiting = False
				finally:
					defer = yield self.simQubit.callRemote("unlock")

			# If we did not get a lock on an active qubit, wait for update and try again
			if waiting:
				yield deferLater(reactor, self._delay, lambda: none)

		return outcome

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
	def remote_apply_T(self):
		"""
		Apply T gate.
		"""
		yield self._single_gate("apply_T")

	@inlineCallbacks
	def remote_apply_rotation(self,n,a):
		"""
		Apply rotation around axis n with angle a
		"""
		yield self._single_gate("apply_rotation",n,a)

	@inlineCallbacks
	def remote_measure(self):
		"""
		Measure the qubit in the standard basis. This does delete the qubit from the simulation.

		Returns the measurement outcome.
		"""

		if self.active != 1:
			logging.error("VIRTUAL NODE %s: Attempt to manipulate qubits no longer at this node.", self.virtNode.name)
			return

		# Check whether the qubit is local or remote. Due to remote register merges, this may change
		# while we try and get a lock. For this reason, we have to wait until we have a lock on an _active_
		# qubit before proceeding.
		waiting = True
		while(waiting):
			if self.virtNode == self.simNode:
				try:
					yield self.simQubit.lock()
					if self.simQubit.active:
						logging.debug("VIRTUAL NODE %s: Measuring local qubit",self.virtNode.name)
						outcome = self.simQubit.remote_measure_inplace()
						self.virtNode.root._remove_sim_qubit(self.simQubit)
						waiting = False
				except Exception as e:
					logging.error("VIRTUAL NODE %s: Cannot remove qubit - %s", self.virtNode.name, e)
					waiting = False
				finally:
					self.simQubit.unlock()
			else:
				try:
					defer = yield self.simQubit.callRemote("lock")
					active = yield self.simQubit.callRemote("isActive")
					if active:
						logging.debug("VIRTUAL NODE %s: Measuring remote qubit at %s.",self.virtNode.name, self.simNode.name)
						outcome = yield self.simQubit.callRemote("measure_inplace")
						num = yield self.simQubit.callRemote("get_sim_number")
						defer = yield self.simNode.root.callRemote("remove_sim_qubit_num",num)
						waiting = False
				except Exception as e:
					logging.error("VIRTUAL NODE %s: Cannot remove qubit - %s", self.virtNode.name, e)
					waiting = False
				finally:
					defer = yield self.simQubit.callRemote("unlock")

			# If we did not get a lock on an active qubit, wait for update and try again
			if waiting:
				yield deferLater(reactor, self._delay, lambda: none)

		returnValue(outcome)

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
			def1 =  self.simNode.root.callRemote("get_global_lock")

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
				return(DeferredList([def0, def1, def2], fireOnOneCallback=False, consumeErrors=True))
			else:
				return(DeferredList([def0, def1], fireOnOneCallback=False, consumeErrors=True))
		else:
			if lockedRemoteTarget:
				return(DeferredList([def1, def2], fireOnOneCallback=False, consumeErrors=True))
			else:
				return(DeferredList([def1], fireOnOneCallback=False, consumeErrors=True))


	@inlineCallbacks
	def _unlock_nodes(self, q1simNode, q1virtNode, q2simNode, q2virtNode):
		"""
		Wrapper to acquire the global register lock on both nodes that involve the qubits. This takes different
		arguments as lock nodes since we wish to call it with the _original_ simulated and target nodes from which we got
		the lock - not the updated ones.

		Arguments
		q1simNode	original simulating node of the first qubit
		q1virtNode	original virtual node of the first qubit
		q2simNode	original simulating node of the second qubit
		q2virtNode	original virtual node of the second qubit

		"""

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


	@inlineCallbacks
	def _lock_inreg(self, qubit):
		"""
		Lock all qubits in the same register as the virtual qubit qubit.
		"""

		if qubit.simNode == qubit.virtNode:
			yield qubit.simNode.root._lock_reg_qubits(qubit.simQubit)
		else:
			simNum = yield qubit.simQubit.callRemote("get_sim_number")
			yield qubit.simNode.root.callRemote("lock_reg_qubits",simNum)

	@inlineCallbacks
	def _unlock_inreg(self, qubit):
		"""
		Lock all qubits in the same register as the virtual qubit qubit.
		"""

		if qubit.simNode == qubit.virtNode:
			yield qubit.simNode.root._unlock_reg_qubits(qubit.simQubit)
		else:
			simNum = yield qubit.simQubit.callRemote("get_sim_number")
			yield qubit.simNode.root.callRemote("unlock_reg_qubits",simNum)

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
			logging.error("VIRTUAL NODE %s: Attempt to manipulate qubits no longer at this node.", self.virtNode.name)
			return


		localName = ''.join(["remote_",name])
		logging.debug("VIRTUAL NODE %s: Doing 2 qubit gate name %s and local call %s",self.virtNode.name,name,localName)


		# Before we proceed, we need to acquire the gobal locks of the nodes holding the
		# registers of both qubits. We wrap this in a timeout with random repeat since there is
		# otherwise the possibility of a deadlock if two nodes compete for the _two_ locks
		waiting = True
		attempts = 0
		while(waiting and attempts <= self.virtNode.root.maxAttempts):

			# Set up the timeout at a random time between 1s and 4s later
			timeoutD = Deferred()
			timeup = reactor.callLater(random.uniform(1,4), timeoutD.callback, None)

			# Set up the lock acquisition
			lockD = self._lock_nodes(target)

			try:
				# Yield on both of them
				gotLock, timeoutRes = yield DeferredList([lockD, timeoutD], fireOnOneCallback=True, fireOnOneErrback=True, consumeErrors=True)
			except Exception as e:
				logging.debug("VIRTUAL NODE %s: Cannot get lock %s",self.virtNode.name, e)
				yield self._unlock_nodes(self.simNode, self.virtNode, target.simNode, target.virtNode)
				timeup.cancel()
				return
			else:
				if timeoutD.called:
					logging.debug("VIRTUAL NODE %s: Timing out getting locks.",self.virtNode.name)
					lockD.cancel()
					yield self._unlock_nodes(self.simNode, self.virtNode, target.simNode, target.virtNode)
					attempts = attempts + 1
				elif lockD.called:
					waiting = False
					timeup.cancel()

		# We have now acquired the two relevant global node locks. If more than one qubit is locked, all code
		# will first acquire the global lock, so this should be safe from deadlocks now, so we will not timeout

		yield self._lock_inreg(self)
		yield self._lock_inreg(target)

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
						logging.debug("VIRTUAL NODE %s: 2qubit command demands register merge.",self.virtNode.name)
						# Both are local but not in the same register
						self.simNode.root.local_merge_regs(self.simQubit, target.simQubit)

						# After the merge, just do the gate
						getattr(self.simQubit, localName)(target.simQubit.num)
				else:
					# Both are remotely simulated
					logging.debug("VIRTUAL NODE %s: 2qubit command demands remote register merge.",self.virtNode.name)

					# Fetch the details of the two simulated qubits from remote
					(fNum, fNode) = yield self.simQubit.callRemote("get_details")
					(tNum, tNode) = yield target.simQubit.callRemote("get_details")

					# Sanity check: we really have the right simulating node
					if fNode != self.simNode.name or tNode != target.simNode.name:
						logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.",self.myID.name)
						raise quantumError("Inconsistent simulation")

					# Merge the remote register according to the simulation IDs of the qubits
					defer = yield self.simNode.root.callRemote("merge_regs", fNum, tNum)

					# Get the number of the target in the new register
					targetNum = yield target.simQubit.callRemote("get_number")

					# Execute the 2 qubit gate
					defer = yield self.simQubit.callRemote(name,targetNum)
					logging.debug("VIRTUAL NODE %s: Remote 2qubit command to %s.",self.virtNode.name, target.simNode.name)
			else:
				# They are simulated at two different nodes

				if self.simNode == self.virtNode:

					# We are the locally simulating node of the first qubit, merge all to us
					logging.debug("VIRTUAL NODE %s: 2qubit command demands merge from remote target sim %s to us.",self.simNode.name, target.simNode.name)
					(fNum, fNode) = yield target.simQubit.callRemote("get_details")
					if fNode != target.simNode.name:
						logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.",self.myID.name)
						raise quantumError("Inconsistent simulation.")
					target.simQubit = yield self.simNode.root.remote_merge_from(target.simNode.name, fNum, self.simQubit.register)

					# Get the number of the target in the new register
					targetNum = target.simQubit.num

					# Execute the 2 qubit gate
					getattr(self.simQubit, localName)(targetNum)

				elif target.simNode == target.virtNode:

					# We are the locally simulating node of the target qubit, merge all to us
					logging.debug("VIRTUAL NODE %s: 2qubit command demands merge from remote sim %s to us.",target.simNode.name, self.simNode.name)
					(fNum, fNode) = yield self.simQubit.callRemote("get_details")
					if fNode != self.simNode.name:
						logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.",self.myID.name)
						raise quantumError("Inconsistent simulation.")
					self.simQubit = yield target.simNode.root.remote_merge_from(self.simNode.name, fNum, target.simQubit.register)

					# Get the number of the target in the new register
					targetNum = target.simQubit.num

					# Execute the 2 qubit gate
					getattr(self.simQubit, localName)(targetNum)

				else:
					# Both qubits are remotely simulated - we will pull both registers to become one local register
					logging.debug("VIRTUAL NODE %s: 2qubit command demands total remote merge from %s and %s.",self.virtNode.name, target.simNode.name, self.simNode.name)

					# Create a new local register
					newLocalReg = self.virtNode.root.remote_new_register()

					# Fetch the detail of the two registers from remote
					(fNum, fNode) = yield self.simQubit.callRemote("get_details")
					if fNode != self.simNode.name:
						logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.",self.myID.name)
						raise quantumError("Inconsistent simulation.")
					(tNum, tNode) = yield target.simQubit.callRemote("get_details")
					if tNode != target.simNode.name:
						logging.error("VIRTUAL NODE %s: Inconsistent simulation. Cannot merge.",self.myID.name)
						raise quantumError("Inconsistent simulation.")

					# Pull the remote registers to this node
					self.simQubit = yield self.virtNode.root.remote_merge_from(self.simNode.name, fNum, newLocalReg)
					target.simQubit = yield target.virtNode.root.remote_merge_from(target.simNode.name, tNum, newLocalReg)
					# Get the number of the target in the new register
					targetNum = target.simQubit.num

					# Finally, execute the two qubit gate
					logging.debug("RUN GATE")
					getattr(self.simQubit, localName)(targetNum)
		except Exception as e:
			logging.error("VIRTUAL NODE %s: Cannot perform two qubit gate %s", self.virtNode.name, e) 

		finally:
			# We need to release all the locks, no matter what happened
			yield self._unlock_inreg(self)
			yield self._unlock_inreg(target)
			yield self._unlock_nodes(q1simNode, q1virtNode, q2simNode, q2virtNode)


	@inlineCallbacks
	def remote_get_number(self):
		"""
		Returns the number of this qubit in whatever local register it is in. Not useful for the client, but convenient for debugging.
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

	@inlineCallbacks
	def remote_get_qubit(self):
		"""
		Returns the state of this qubit in real and imaginary parts separated. This is required
		single Twisted cannot natively transfer complex valued objects.
		"""

		if self.active != 1:
			logging.error("VIRTUAL NODE %s: Attempt to manipulate qubits no longer at this node.", self.virtNode.name)

		if self.virtNode == self.simNode:
			(R,I) = self.simQubit.remote_get_qubit()
		else:
			try:
				(R,I) = yield self.simQubit.callRemote("get_qubit")
			except ConnectionError:
				logging.error("VIRTUAL NODE %s: Connection failed: cannot get qubit number.")

		return (R,I)



############################################
#
# Keeping track of received qubits for CQC

class QubitCQC:
	
	def __init__(self, fromName, toName, from_app_id, to_app_id, new_virt_num):
		self.fromName = fromName;
		self.toName = toName;
		self.from_app_id = from_app_id;
		self.to_app_id = to_app_id;
		self.virt_num = virt_num;


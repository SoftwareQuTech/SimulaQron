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
# 	 documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from SimulaQron.virtNode.crudeSimulator import SimpleEngine
from twisted.spread import pb
from twisted.internet.defer import *

import logging

def qubit_error(reason):
	logging.error("An error occurred when applying a gate. Reason: %s", str(reason))


class SimulatedQubit(pb.Referenceable):
	"""
	Simulated qubit object in the specified local simulation engine.

	- **Arguments**
		:node:		network node that this qubit lives at
		:register:	register on that node that the qubit is in

	.. note::
		Qubit objects are local to each node that is simulating a particular quantum register.
		A qubit object provides the backing for a virtual qubit, which may be at another node.
	"""

	def __init__(self, node, register, simNum, num=0):
		# Node where this qubit is located
		self.node = node

		# Register where this qubit is simulated
		self.register = register

		# Number in the register, if known
		self.num = num

		# Number of the simulated qubit, unique at each virtual node
		self.simNum = simNum

		# Lock marshalling access to this qubit
		self._lock = DeferredLock()

		# Mark this qubit as active (still connected to a register)
		self.active = True

	def lock(self):
		logging.warning("Locking local %s", self.num)
		return self._lock.acquire()

	def remote_lock(self):
		logging.warning("Locking remotely %s", self.num)
		return self._lock.acquire()

	def unlock(self):
		logging.warning("Unlocking local %s", self.num)
		self._lock.release()

	def remote_unlock(self):
		logging.warning("Unlocking remotely %s", self.num)
		self._lock.release()

	def isLocked(self):
		return self._lock.locked

	def remote_isLocked(self):
		return self._lock.locked

	def remote_isActive(self):
		return self.active

	def make_fresh(self):
		"""
		Make this a fresh qubit.
		"""
		# Create a fresh qubit in the |0> state
		num = self.register.add_fresh_qubit()
		self.num = num

		logging.debug("QUANTUM %s: Adding qubit number %d to register %d", self.node.name, num, self.register.num)

	def _do_operation(self, name, func, **kwargs):
		logging.warning("QUANTUM NODE %s: applying %s to number %d. Active: %s", self.node.name, name, self.num, self.active)
		res = func(self.num, **kwargs)
		logging.warning("DONE Applying!")
		print(res)
		return res

	def _apply_single_gate(self, gate_name, gate, **kwargs):
		logging.warning("Locking %s to do %s", self.num, gate_name)
		d = self._lock.run(self._do_operation, gate_name, gate, **kwargs)
		d.addErrback(qubit_error)
		logging.warning("%s to do %s Done", self.num, gate_name)
		return d

	def remote_apply_X(self):
		"""
		Apply X gate to itself by passing it onto the underlying register.
		"""
		return self._apply_single_gate("X", self.register.apply_X)

	def remote_apply_K(self):
		"""
		Apply K gate to itself by passing it onto the underlying register. Maps computational to Y eigenbasis.
		"""
		return self._apply_single_gate("K", self.register.apply_K)

	def remote_apply_Y(self):
		"""
		Apply Y gate.
		"""
		return self._apply_single_gate("Y", self.register.apply_Y)

	def remote_apply_Z(self):
		"""
		Apply Z gate.
		"""
		return self._apply_single_gate("Z", self.register.apply_Z)

	def remote_apply_H(self):
		"""
		Apply H gate.
		"""
		return self._apply_single_gate("H", self.register.apply_H)

	def remote_apply_T(self):
		"""
		Apply T gate.
		"""
		return self._apply_single_gate("T", self.register.apply_T)

	def remote_apply_rotation(self, *args):
		"""
		Apply rotation around axis n with angle a.
		Arguments:
		n	A tuple of three numbers specifying the rotation axis, e.g n=(1,0,0)
		a	The rotation angle in radians.
		"""
		n = args[0]
		a = args[1]
		return self._apply_single_gate("rotation. Axis={},angle={}".format(str(tuple(n)), a),
										self.register.apply_rotation, n=n, a=a)

	def remote_measure_inplace(self):
		"""
		Measure the qubit in the standard basis. This does NOT delete the qubit, but replace the relevant
		qubit with the measurement outcome.

		Returns the measurement outcome.
		"""
		return self._apply_single_gate("Measure inplace", self.register.measure_qubit_inplace)

	def remote_measure(self):
		"""
		Measure the qubit in the standard basis. This does delete the qubit.

		Returns the measurement outcome.
		"""

		# Measure the qubit
		return self._apply_single_gate("Measure", self.register.measure_qubit)

	def remote_cnot_onto(self, targetNum):
		"""
		Performs a CNOT operation with this qubit as control, and the other qubit as target.

		Arguments
		targetNum	the qubit to use as the target of the CNOT
		"""

		logging.debug("QUANTUM NODE %s: CNOT from %d to %d", self.node.name, self.num, targetNum)
		self.register.apply_CNOT(self.num, targetNum)

	def remote_cphase_onto(self, targetNum):
		"""
		Performs a CPHASE operation with this qubit as control, and the other qubit as target.

		Arguments
		targetNum	the qubit to use as the target of the CPHASE
		"""

		self.register.apply_CPHASE(self.num, targetNum)

	def remote_get_sim_number(self):
		"""
		Returns the simulation number of this qubit.
		"""
		return self.simNum

	def remote_get_number(self):
		"""
		Returns the local number of this qubit.
		"""
		return self.num

	def remote_get_register(self):
		"""
		Returns the register where this qubit is simulated.
		"""
		return self.register

	def remote_get_numbers(self):
		"""
		Returns the number of the simulating register.
		"""
		return self.num, self.register.num

	def remote_get_qubit(self):
		"""
		Returns the state of the qubits in the list qList by tracing out the rest.
		"""
		logging.debug("QUANTUM NODE %s: Returning qubit %d", self.node.name, self.num)
		return self.register.get_qubits_RI([self.num])

	def remote_get_details(self):
		"""
		Returns out simulation number as well as the details of this simulating node.
		"""
		return self.simNum, self.node.name

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


from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

from SimulaQron.virtNode.basics import *
from SimulaQron.virtNode.quantum import *
from SimulaQron.virtNode.crudeSimulator import *
from SimulaQron.general.hostConfig import *

from itertools import repeat

def main():

	# Read config file
	config = networkConfig("../../config/virtualNodes.cfg")

	# We are Alice
	myName = "Alice"

	# Connect to the local virtual Node	
	node = config.hostDict[myName]
	factory = pb.PBClientFactory()
	reactor.connectTCP(node.hostname, node.port, factory)
	def1 = factory.getRootObject()
	def1.addCallback(got_root)
	def1.addErrback(err_obj1)
	reactor.run()

def err_obj1(reason):
    	print("error getting first object", reason)
    	reactor.stop()

@inlineCallbacks
def got_root(obj):

	print("Got root object", obj)

	###
	# Do some operations in the default register
	reg1 = yield obj.callRemote("new_register")
	q = yield obj.callRemote("new_qubit_inreg",reg1)

	defer = yield q.callRemote("test")
	defer = yield q.callRemote("apply_X")
	defer = yield q.callRemote("apply_T")
	defer = yield q.callRemote("apply_Y")
	defer = yield q.callRemote("apply_H")
	outcome = yield q.callRemote("measure")
	print("Got outcome:",outcome)

	# Generate EPR pair between two qubits
	q1 = yield obj.callRemote("new_qubit")
	defer = yield q1.callRemote("apply_H")

	q2 = yield obj.callRemote("new_qubit")
	defer = yield q1.callRemote("cnot_onto",q2)

	(R,I) = yield obj.callRemote("get_multiple_qubits",[q1,q2])
	M = I

	for s in range(len(I)):
		for t in range(len(I)):
			M[s][t] = R[s][t] + I[s][t] * 1j


	# M = []
	qt = Qobj(M)
	print("EPR Matrix: ", qt)

	outcome = yield q2.callRemote("measure")
	print("Got outcome from EPR:",outcome)

	### 
	# Make a new register
	reg1 = yield obj.callRemote("new_register")
	reg2 = yield obj.callRemote("new_register")
	
	q1 = yield obj.callRemote("new_qubit_inreg",reg1)
	q2 = yield obj.callRemote("new_qubit_inreg",reg2)

	(R,I) = yield obj.callRemote("get_multiple_qubits",[q1])
	# (R,I, activeQ, oldRegNum, oldQubitNum) = yield obj.callRemote("get_register",q1)
	M = I

	for s in range(len(I)):
		for t in range(len(I)):
			M[s][t] = R[s][t] + I[s][t] * 1j


	# M = []
	qt = Qobj(M)
	print("Q1 Matrix: ", qt)
	(R,I) = yield obj.callRemote("get_multiple_qubits",[q2])
	M = I

	for s in range(len(I)):
		for t in range(len(I)):
			M[s][t] = R[s][t] + I[s][t] * 1j


	# M = []
	qt = Qobj(M)
	print("Q2 Matrix: ", qt)

	print("Applying CNOT")

	defer = yield q1.callRemote("apply_H")
	defer = yield q1.callRemote("cnot_onto",q2)

	(R,I) = yield obj.callRemote("get_multiple_qubits",[q1,q2])
	M = I

	for s in range(len(I)):
		for t in range(len(I)):
			M[s][t] = R[s][t] + I[s][t] * 1j


	# M = []
	qt = Qobj(M)
	print("Matrix: ", qt)

	outcome = yield q2.callRemote("measure")
	print("Got outcome from cross register EPR:",outcome)

	###
	#
	num = yield q1.callRemote("get_number")
	print("Got number:", num)
	
	(R,I, activeQ, oldRegNum, oldQubitNum) = yield obj.callRemote("get_register",q1)
	M = I

	for s in range(len(I)):
		for t in range(len(I)):
			M[s][t] = R[s][t] + I[s][t] * 1j


	# M = []
	qt = Qobj(M)
	print("Matrix: ", qt)

	####
	# Send qubits
	defer = yield obj.callRemote("send_qubit", q1, "Bob")

	defer = yield q1.callRemote("apply_H")


	reactor.stop()

	
main()

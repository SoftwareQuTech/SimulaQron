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

from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *
from SimulaQron.cqc.pythonLib.cqc import *
import qutip
import numpy as np
import sys

def calc_exp_values(q):
	"""
	Calculates the expected value for measurements in the X,Y and Z basis and returns these in a tuple.
	q should be a qutip object representing a density matrix
	"""
	#eigenvectors
	z0=qutip.basis(2,0)
	z1=qutip.basis(2,1)
	x1=1/np.sqrt(2)*(z0-z1)
	y1=1/np.sqrt(2)*(z0-1j*z1)

	#projectors
	P_X1=x1*x1.dag()
	P_Y1=y1*y1.dag()
	P_Z1=z1*z1.dag()

	#probabilities
	p_x=(P_X1*q).tr()
	p_y=(P_Y1*q).tr()
	p_z=(P_Z1*q).tr()

	return (p_x,p_y,p_z)

def prep_CNOT_control_CQC(cqc):
	q1=qubit(cqc,print_info=False)
	q2=qubit(cqc,print_info=False)
	q1.H(print_info=False)
	q1.cnot(q2,print_info=False)
	q2.measure(print_info=False)
	return q1

def prep_CNOT_target_CQC(cqc):
	q1=qubit(cqc,print_info=False)
	q2=qubit(cqc,print_info=False)
	q1.H(print_info=False)
	q1.cnot(q2,print_info=False)
	q1.measure(print_info=False)
	return q2

def prep_CPHASE_control_CQC(cqc):
	q1=qubit(cqc,print_info=False)
	q2=qubit(cqc,print_info=False)
	q1.H(print_info=False)
	q2.H(print_info=False)
	q1.cphase(q2,print_info=False)
	q2.H(print_info=False)
	q2.measure(print_info=False)
	return q1

def prep_CPHASE_target_CQC(cqc):
	q1=qubit(cqc,print_info=False)
	q2=qubit(cqc,print_info=False)
	q1.H(print_info=False)
	q2.H(print_info=False)
	q1.cphase(q2,print_info=False)
	q2.H(print_info=False)
	q1.measure(print_info=False)
	return q2

def prep_EPR1_CQC(cqc):
	Alice=CQCConnection("Alice",appID=1)
	qA=Alice.createEPR("Bob",print_info=False)
	qB=cqc.createEPR("Alice",remote_appID=1,print_info=False)
	qA.measure(print_info=False)
	Alice.close()
	return qB

def prep_EPR2_CQC(cqc):
	Charlie=CQCConnection("Charlie",appID=1)
	qB=cqc.createEPR("Charlie",remote_appID=1,print_info=False)
	qC=Charlie.createEPR("Bob",print_info=False)
	qC.measure(print_info=False)
	Charlie.close()
	return qB

def prep_send_CQC(cqc):
	Alice=CQCConnection("Alice",appID=1)
	qA=qubit(cqc,print_info=False)
	qB=qubit(cqc,print_info=False)
	qA.H(print_info=False)
	qA.cnot(qB,print_info=False)
	cqc.sendQubit(qA,"Alice",remote_appID=1,print_info=False)
	qA=Alice.recvQubit(print_info=False)
	m=qA.measure(print_info=False)
	Alice.close()
	if m==1:
		qB.X(print_info=False)
	qB.H(print_info=False)
	return qB

def prep_recv_CQC(cqc):
	Alice=CQCConnection("Alice",appID=1)
	qA=qubit(Alice,print_info=False)
	qA.H(print_info=False)
	Alice.sendQubit(qA,"Bob",print_info=False)
	qB=cqc.recvQubit(print_info=False)
	Alice.close()
	return qB

def prep_mixed_qutip():
	q=qutip.qeye(2)/2
	return q

def prep_H_qutip():
	q=qutip.basis(2)
	H=1/np.sqrt(2)*(qutip.sigmax()+qutip.sigmaz())
	return qutip.ket2dm(H*q)

#####################################################################################################
#
# main
#
def main():

	# Initialize the connection
	cqc=CQCConnection("Bob")

	iterations=100

	# Test CNOT control
	sys.stdout.write("Testing CNOT control:")
	exp_values=calc_exp_values(prep_mixed_qutip())
	ans=cqc.test_preparation(prep_CNOT_control_CQC,exp_values,iterations=iterations)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test CNOT target
	sys.stdout.write("Testing CNOT target:")
	exp_values=calc_exp_values(prep_mixed_qutip())
	ans=cqc.test_preparation(prep_CNOT_target_CQC,exp_values,iterations=iterations)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test CPHASE control
	sys.stdout.write("Testing CPHASE control:")
	exp_values=calc_exp_values(prep_mixed_qutip())
	ans=cqc.test_preparation(prep_CPHASE_control_CQC,exp_values,iterations=iterations)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test CPHASE target
	sys.stdout.write("Testing CPHASE target:")
	exp_values=calc_exp_values(prep_mixed_qutip())
	ans=cqc.test_preparation(prep_CPHASE_target_CQC,exp_values,iterations=iterations)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test EPR1
	sys.stdout.write("Testing EPR1:")
	exp_values=calc_exp_values(prep_mixed_qutip())
	ans=cqc.test_preparation(prep_EPR1_CQC,exp_values,iterations=iterations)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test EPR2
	sys.stdout.write("Testing EPR2:")
	exp_values=calc_exp_values(prep_mixed_qutip())
	ans=cqc.test_preparation(prep_EPR2_CQC,exp_values,iterations=iterations)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test send control
	sys.stdout.write("Testing send:")
	exp_values=calc_exp_values(prep_H_qutip())
	ans=cqc.test_preparation(prep_send_CQC,exp_values,iterations=iterations)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test recv target
	sys.stdout.write("Testing recv:")
	exp_values=calc_exp_values(prep_H_qutip())
	ans=cqc.test_preparation(prep_recv_CQC,exp_values,iterations=iterations)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Stop the connection
	cqc.close()


##################################################################################################
main()


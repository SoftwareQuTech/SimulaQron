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

from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *
from SimulaQron.cqc.pythonLib.cqc import *
import qutip
import numpy as np
import sys

def calc_exp_values(q):
	"""
	Calculates the expected value for measurements in the X,Y and Z basis and returns these in a tuple.
	q should be a qutip object
	"""
	#eigenvectors
	z0=qutip.basis(2,0)
	z1=qutip.basis(2,1)
	x1=1/np.sqrt(2)*(z0+z1)
	y1=1/np.sqrt(2)*(z0-1j*z1)

	#projectors
	P_X1=x1*x1.dag()
	P_Y1=y1*y1.dag()
	P_Z1=z1*z1.dag()

	#probabilities
	p_x=(q.dag()*P_X1*q).tr()
	p_y=(q.dag()*P_Y1*q).tr()
	p_z=(q.dag()*P_Z1*q).tr()

	return (p_x,p_y,p_z)

def prep_X_CQC(cqc):
	q=qubit(cqc,print_info=False)
	q.X(print_info=False)
	return q

def prep_X_qutip():
	q=qutip.basis(2)
	X=qutip.sigmax()
	return X*q

def prep_Y_CQC(cqc):
	q=qubit(cqc,print_info=False)
	q.Y(print_info=False)
	return q

def prep_Y_qutip():
	q=qutip.basis(2)
	Y=qutip.sigmay()
	return Y*q

def prep_Z_CQC(cqc):
	q=qubit(cqc,print_info=False)
	q.Z(print_info=False)
	return q

def prep_Z_qutip():
	q=qutip.basis(2)
	Z=qutip.sigmaz()
	return Z*q

def prep_H_CQC(cqc):
	q=qubit(cqc,print_info=False)
	q.H(print_info=False)
	return q

def prep_H_qutip():
	q=qutip.basis(2)
	X=1/np.sqrt(2)*(qutip.sigmax()+qutip.sigmaz())
	return X*q

def prep_T_CQC(cqc):
	q=qubit(cqc,print_info=False)
	q.T(print_info=False)
	return q

def prep_T_qutip():
	q=qutip.basis(2)
	T=qutip.Qobj([[1,0],[0,np.exp(1j*np.pi/4)]],dims=[[2],[2]])
	return T*q


#####################################################################################################
#
# main
#
def main():

	# Initialize the connection
	cqc=CQCConnection("Alice")

	# Test X
	sys.stdout.write("Testing X gate:")
	exp_values=calc_exp_values(prep_X_qutip())
	ans=cqc.test_preparation(prep_X_CQC,exp_values,None,iterations=10)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test Y
	sys.stdout.write("Testing Y gate:")
	exp_values=calc_exp_values(prep_Y_qutip())
	ans=cqc.test_preparation(prep_Y_CQC,exp_values,None,iterations=10)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test Z
	sys.stdout.write("Testing Z gate:")
	exp_values=calc_exp_values(prep_Z_qutip())
	ans=cqc.test_preparation(prep_Z_CQC,exp_values,None,iterations=10)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test H
	sys.stdout.write("Testing H gate:")
	exp_values=calc_exp_values(prep_H_qutip())
	ans=cqc.test_preparation(prep_H_CQC,exp_values,None,iterations=10)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Test T
	sys.stdout.write("Testing T gate:")
	exp_values=calc_exp_values(prep_T_qutip())
	ans=cqc.test_preparation(prep_T_CQC,exp_values,None,iterations=10)
	sys.stdout.write('\r')
	if ans:
		print("OK")
	else:
		print("FAIL")

	# Stop the connection
	cqc.close()


##################################################################################################
main()


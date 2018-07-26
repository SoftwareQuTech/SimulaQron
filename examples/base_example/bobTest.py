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
from SimulaQron.toolbox.measurements import parity_meas

import random



#####################################################################################################
#
# main
#
def main():

	# Initialize the connection
	Bob=CQCConnection("Bob")

	# Create EPR pairs
	q1=Bob.recvEPR()
	q2=Bob.recvEPR()

	# Make sure we order the qubits consistently with Alice
	# Get entanglement IDs
	q1_ID = q1.get_entInfo().id_AB
	q2_ID = q2.get_entInfo().id_AB

	if q1_ID < q2_ID:
		qb=q1
		qd=q2
	else:
		qb=q2
		qd=q1

	# Put the qubits in the correct state (|++> + |-->)
	qb.H()
	qd.H()

	# Get col
	col = random.randint(0,2)

	# Perform the three measurements
	if col == 0:
		m0 = parity_meas([qb, qd], "XI", Bob)
		m1 = parity_meas([qb, qd], "XZ", Bob, negative=True)
		m2 = parity_meas([qb, qd], "IZ", Bob)
	elif col == 1:
		m0 = parity_meas([qb, qd], "XX", Bob)
		m1 = parity_meas([qb, qd], "YY", Bob)
		m2 = parity_meas([qb, qd], "ZZ", Bob)
	elif col == 2:
		m0 = parity_meas([qb, qd], "IX", Bob)
		m1 = parity_meas([qb, qd], "ZX", Bob, negative=True)
		m2 = parity_meas([qb, qd], "ZI", Bob)
	else:
		raise RuntimeError("Invalid row")

	print("\n")
	print("==========================")
	print("App {}: column is:".format(Bob.name))
	print("(" + "_"*col + str(m0) + "_"*(2-col) + ")")
	print("(" + "_"*col + str(m1) + "_"*(2-col) + ")")
	print("(" + "_"*col + str(m2) + "_"*(2-col) + ")")
	print("==========================")
	print("\n")

	# Clear qubits
	qb.measure()
	qd.measure()

	# Stop the connection
	Bob.close()


##################################################################################################
main()


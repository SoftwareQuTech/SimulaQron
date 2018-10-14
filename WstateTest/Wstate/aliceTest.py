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
from additional_functions import *

#####################################################################################################
#
# main
#

def main():

	# Initialize the connection
	with CQCConnection("Alice") as Alice:
		# Create an EPR pair
		Nodenames = Alice._cqcNet.hostDict.keys()
		print(Nodenames, " size = ", len(Nodenames))
		num_qubit = len(Nodenames);
		qubits = initialize_Qubit_register(num_qubit, Alice)
		prepare_Nqubit_Wstate(qubits)

		print("Number of qubits as W state = ", len(qubits))
		index = 0
		for key in Alice._cqcNet.hostDict.keys():
			if key != Alice.name:
				print("Sending qubit[",index, "] to ",key)
				Alice.sendQubit(qubits[index],key)
				index = index + 1

		m=qubits[len(qubits)-1].measure()
		to_print="(Alice) App {}: Measurement outcome is: {}".format(Alice.name,m)
		print("|"+"-"*(len(to_print)+2)+"|\n", "| "+to_print+" |", "\n|"+"-"*(len(to_print)+2)+"|")

		if m==1:
			print("| (Alice) I'm the leader")
			ordlist = string_to_int("Alice is the leader")
			broadbastClassical(ordlist,Alice)

		data=Alice.recvClassical()
		message=list(data)
		msg = int_to_string(message)
		print("(Alice)",msg)


##################################################################################################
main()

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


from SimulaQron.cqc.pythonLib.cqc import *


#####################################################################################################
#
# main
#
def main():

	# Initialize the connection
	with CQCConnection("T2") as T2:

		# Make EPR-pairs with S1 and R2
		qtmp1=T2.recvEPR()
		qtmp2=T2.recvEPR()

		# Check where qubit are sent from
		if qtmp1.get_remote_entNode()=="R2":
			q11=qtmp1
			q1=qtmp2
		else:
			q11=qtmp2
			q1=qtmp1

		# Receive corrections from R2 (step 3)
		msg=T2.recvClassical()
		if msg[2]==1:
			q11.X()

		# Entangle (step 4)
		q11.cnot(q1)

		# H and measure (step 5)
		q11.H()
		m=q11.measure()

		# Send corrections to R2 (step 5)
		msg="T2".encode('utf-8')+bytes([m])
		T2.sendClassical("R2",msg)

		# Measure out
		m=q1.measure()
		to_print="1: Measurement outcome: {}".format(m)
		print("|"+"-"*(len(to_print)+2)+"|")
		print("| "+to_print+" |")
		print("|"+"-"*(len(to_print)+2)+"|")


##################################################################################################
main()

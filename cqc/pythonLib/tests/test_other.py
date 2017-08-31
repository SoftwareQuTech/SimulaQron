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
import time


#####################################################################################################
#
# main
#
def main():

	# Initialize the connection
	cqc=CQCConnection("Alice")

	# Test Measure inplace
	print("Testing measure inplace:")
	q=qubit(cqc,print_info=False)
	q.H(print_info=False)
	m1=q.measure(inplace=True,print_info=False)
	failed=False
	for _ in range(10):
		m2=q.measure(inplace=True,print_info=False)
		if m1!=m2:
			print("OK")
			failed=True
			break
	if not failed:
		print("OK")
	q.measure(print_info=False)

	# Test Get time
	print("Testing getTime:")
	q1=qubit(cqc,print_info=False)
	time.sleep(3)
	q2=qubit(cqc,print_info=False)
	t1=q1.getTime(print_info=False)
	t2=q2.getTime(print_info=False)
	if (t2-t1)==3:
		print("OK")
	else:
		print("FAIL")
	q1.measure(print_info=False)
	q2.measure(print_info=False)

	# Stop the connection
	cqc.close()


##################################################################################################
main()


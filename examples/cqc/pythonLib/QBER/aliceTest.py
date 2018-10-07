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

import sys
import json
from SimulaQron.cqc.pythonLib.cqc import CQCConnection

def main(nr_runs):
	meas_outcomes = {}

	print("Estimating QBER by measuring {} produced EPR pairs.".format(nr_runs))

	# Initialize the connection
	with CQCConnection("Alice") as Alice:

		for i in range(nr_runs):

			# Create an EPR pair
			q = Alice.createEPR("Bob")

			# Get the identifier of this EPR pair such that we can relate our measurement outcomes to Bobs
			sequence_nr = q.get_entInfo().id_AB

			print("Generated EPR pair number {}.".format(sequence_nr))

			if (i % 3) == 0:
				# Measure in Z
				basis = 'Z'
			elif (i % 3) == 1:
				# Measure in X
				q.H()
				basis = 'X'
			else:
				# Measure in Y
				q.K()
				basis = 'Y'

			m = q.measure()
			# We save both the measurement outcome and the measurement basis
			meas_outcomes[sequence_nr] = (m, basis)

	# Get the measurement outcomes from Bob
	msg = Alice.recvClassical(msg_size=10000)

	# Decode the message
	bob_meas_outcomes = json.loads(msg.decode('utf-8'))

	# Check the measurement outcomes
	errors = []
	for (sequence_nr, mB) in bob_meas_outcomes.items():
		mA, basis = meas_outcomes[int(sequence_nr)]
		if basis == 'Y':
			if mA == mB:
				errors.append(True)
			else:
				errors.append(False)
		else:
			if mA != mB:
				errors.append(True)
			else:
				errors.append(False)

	nr_data_points = len(errors)
	avg_QBER = errors.count(True) / nr_data_points
	to_print="Estimated QBER is {} (from {} data-points.".format(avg_QBER, nr_data_points)
	print("|"+"-"*(len(to_print)+2)+"|")
	print("| "+to_print+" |")
	print("|"+"-"*(len(to_print)+2)+"|")

if __name__ == '__main__':
	try:
		nr_runs = int(sys.argv[1])
	except Exception:
		nr_runs = 500
	main(nr_runs)

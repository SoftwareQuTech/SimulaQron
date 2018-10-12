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


def main(nr_runs, cqc_file):
	meas_outcomes = {}

	# Initialize the connection
	with CQCConnection("Node1", cqcFile=cqc_file) as Bob:

		for _ in range(nr_runs):

			# Create an EPR pair
			q = Bob.recvEPR()

			# Get the identifier of this EPR pair such that Alice can relate the measuement outcomes to hers
			sequence_nr = q.get_entInfo().id_AB

			if (sequence_nr % 3) == 0:
				# Measure in Z
				pass
			elif (sequence_nr % 3) == 1:
				# Measure in X
				q.H()
			else:
				# Measure in Y
				q.K()

			m = q.measure()
			meas_outcomes[sequence_nr] = m

	# Encode the measurement outcomes to bytes, such that we can send them
	msg = json.dumps(meas_outcomes).encode('utf-8')

	# Send the measurement outcomes to Alice
	Bob.sendClassical(name="Node0", msg=msg)

if __name__ == '__main__':
	try:
		nr_runs = int(sys.argv[1])
		cqc_file = sys.argv[2]
	except Exception:
		nr_runs = 500
	if nr_runs > 1000:
		raise ValueError("Number of EPR pairs for this example is currently restricted to less than 1000")
	main(nr_runs, cqc_file)

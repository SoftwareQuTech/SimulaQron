Estimating QBER
===============

In this example the two nodes Alice and Bob will estimate the QBER (qubit error rate) of their produced entangled pairs.
To make the below example more interesting you should try to turn on the probabilistic noise option in SimulaQron.
You can do this be setting the entry :code:`noisy-qubits` to :code:`True` by::

    ./cli/SimulaQron set noisy-qubits on

You can also tune the coherence time :code:`t1` of the qubits (lower means more noisy).

.. note:: This probabilistic noise in SimulaQron is not intended and should not be used to benchmark the performence of protocols in noisy settings, since noise is applied in a rate related to the wall clock time of your computer. Thus, if your computer or network is slower, more noise will be applied to the qubits! However you can use this example to tune the :code:`t1`-parameter to a realistic value for your setup. A realistic QBER is around 5 -10 %.


------------
The protocol
------------

Alice and Bob will produce EPR pairs between them and measure their qubits in either the :math:`X`-, :math:`Y`- or :math:`Z`-basis, where :math:`X=\begin{pmatrix}0 & 1 \\ 1 & 0\end{pmatrix}`, :math:`Y=\begin{pmatrix}0 & -i \\ i & 0\end{pmatrix}` or :math:`Z=\begin{pmatrix}1 & 0 \\ 0 & -1\end{pmatrix}`. If there is no noise Alice's and Bob's measurement will be perfectly correlated if they both measure in the :math:`Z`-basis and the same for the :math:`X`-basis but perfectly anti-correlated for the :math:`Y`-basis. The QBER (qubit error rate) is then the number of rounds where this is not the case, i.e. when the nodes measurement outcomes are anti-correlated for the :math:`Z` and :math:`X` bases and correlated for the :math:`Y`-basis.

Alice and Bob have beforehand agreed that they will measure the the first EPR pair in the :math:`Z`-basis, the second in the :math:`X`-basis, the third in the :math:`Y`-basis and then back to :math:`Z`-basis and so on. However, the qubits received from the entanglement generation process are not necessarily ordered. They therefore need to use the entanglement identifier that is attached to any entangled qubit. In particular the entanglement identifier contains a sequence number which is guaranteed to be consistent between the two nodes. This sequence number can be accessed from an entangled qubit as::

    q.get_entInfo().id_AB

Alice and Bob will therefore make use of the following decision rules for the measurement basis:

* Measure in the :math:`Z`-basis if the sequence number modulus 3 is 0.
* Measure in the :math:`X`-basis if the sequence number modulus 3 is 1.
* Measure in the :math:`Y`-basis if the sequence number modulus 3 is 2.

.. note:: More details on the explicit entanglement generation protocol and the generation of the entanglement identifiers will soon be available in a paper which is under construction.

-----------
Setting up
-----------

We will run everything locally (localhost) using two nodes, Alice and Bob. Start up the backend of the simulation by running (to make this example more interesting you should before turn on the noise on the qubits as described above)::

    ./cli/SimulaQron start --nodes Alice,Bob

The below example can then be executed when in the folder `examples/pythonLib/QBER <https://github.com/SoftwareQuTech/CQC-Python/tree/master/examples/pythonLib/QBER>`_ in the repo `pythonLib <https://github.com/SoftwareQuTech/CQC-Python>`_  by typing::

    sh run.sh

which will execute the Python scripts `aliceTest.py` and `bobTest.py` containing the code below. By default 500 EPR pairs are produced to estimate the QBER, see above. You can choose to produce a different number of pairs by passing this as an argument. For example::

    sh run.sh 300

When running this example the estimated QBER will be printed. If the noise in SimulaQron is off the QBER should be 0.

-----------------
Programming Alice
-----------------

Here we program what Alice should do using the python library::

	meas_outcomes = {}

	print("Estimating QBER by measuring {} produced EPR pairs.".format(nr_runs))

	# Initialize the connection
	with CQCConnection("Alice") as Alice:

		for _ in range(nr_runs):

			# Create an EPR pair
			q = Alice.createEPR("Bob")

			# Get the identifier of this EPR pair such that we can relate our measurement outcomes to Bobs
			sequence_nr = q.get_entInfo().id_AB

			print("Generated EPR pair number {}.".format(sequence_nr))

			if (sequence_nr % 3) == 0:
				# Measure in Z
				basis = 'Z'
			elif (sequence_nr % 3) == 1:
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

-----------------
Programming Bob
-----------------

Here we program what Bob should do using the python library::

	meas_outcomes = {}

	# Initialize the connection
	with CQCConnection("Bob") as Bob:

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
	Bob.sendClassical(name="Alice", msg=msg)


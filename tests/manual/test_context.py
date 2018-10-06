from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit

for _ in range(100):

	with CQCConnection("Alice") as cqc:

		q = qubit(cqc)

	# q.H()
	#
	# q.measure()

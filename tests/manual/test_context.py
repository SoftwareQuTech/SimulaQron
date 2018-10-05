from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit

cqc = CQCConnection("Alice")
for _ in range(100):


	q = qubit(cqc)

	q.H()

	# m = q.measure()
	#
	# print(m)
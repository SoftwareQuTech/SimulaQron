from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit

<<<<<<< HEAD
for _ in range(100):

	with CQCConnection("Alice") as cqc:

		q = qubit(cqc)

	# q.H()
	#
	# q.measure()
=======
cqc = CQCConnection("Alice")
for _ in range(100):


	q = qubit(cqc)

	q.H()

	# m = q.measure()
	#
	# print(m)
>>>>>>> b2af0281e7d3d7f228cdf6e4fec229ea5768b762

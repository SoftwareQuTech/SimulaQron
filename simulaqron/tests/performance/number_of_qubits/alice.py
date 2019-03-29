from cqc.pythonLib import CQCConnection, qubit

import sys

from timeit import default_timer as timer

import matplotlib.pyplot as plt

min_nr = int(sys.argv[1])
max_nr = int(sys.argv[2])

Alice = CQCConnection("Alice")

times = []

for n in range(min_nr, max_nr + 1):

    qubits = []

    t1 = timer()

    for _ in range(n):
        qubits.append(qubit(Alice))

    for q in qubits:
        q.measure()

    t2 = timer()

    times.append(t2 - t1)

with open("times_qubits.txt", "w") as f:
    for t in times:
        f.write(str(t) + "\n")

plt.plot(list(range(min_nr, max_nr + 1)), times, marker=".", markersize=10, linestyle="none", color="red")
plt.xlabel("nr of qubits")
plt.ylabel("time (s)")

plt.savefig("times_qubits.pdf")

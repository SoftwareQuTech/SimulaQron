import sys

from cqc.pythonLib import CQCConnection, qubit
from simulaqron.settings import simulaqron_settings

from timeit import default_timer as timer

with CQCConnection("Alice") as cqc:
    nmax = int(sys.argv[1])
    backend = simulaqron_settings.backend
    times = []
    sizes = []
    for n in range(1, nmax + 1):
        t1 = timer()
        qubits = [qubit(cqc)]
        qubits[0].H()
        for i in range(n - 1):
            q = qubit(cqc)
            qubits[0].cnot(q)
            qubits.append(q)
        [q.measure() for q in qubits]
        t2 = timer()
        times.append(t2 - t1)
        sizes.append(n)
        print("Creating GHZ state on {} qubits took {} s using {} as backend".format(n, t2 - t1, backend))
    with open("run_time_ghz_state_{}.txt".format(backend), "w") as f:
        for (n, t) in zip(sizes, times):
            f.write("{} {}\n".format(n, t))

import sys

from cqc.pythonLib import CQCConnection
from cqc.pythonLib_protocols import wstate
from simulaqron.settings import simulaqron_settings

from timeit import default_timer as timer

with CQCConnection("Alice") as cqc:
    nmax = int(sys.argv[1])
    backend = simulaqron_settings.backend
    times = []
    sizes = []
    for n in range(1, nmax + 1):
        t1 = timer()
        qubits = wstate.create_Nqubit_Wstate(n, cqc)
        [q.measure() for q in qubits]
        t2 = timer()
        times.append(t2 - t1)
        sizes.append(n)
        print("Creating W state on {} qubits took {} s using {} as backend".format(n, t2 - t1, backend))
    with open("run_time_w_state_{}.txt".format(backend), "w") as f:
        for (n, t) in zip(sizes, times):
            f.write("{} {}\n".format(n, t))

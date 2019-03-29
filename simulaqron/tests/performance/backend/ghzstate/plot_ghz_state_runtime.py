from matplotlib import pyplot as plt

qutip_sizes = []
qutip_times = []
projectq_sizes = []
projectq_times = []
stabilizer_sizes = []
stabilizer_times = []

with open("run_time_ghz_state_qutip.txt", "r") as f:
    for line in f.readlines():
        words = line.split(" ")
        n = int(words[0].strip())
        t = float(words[1].strip())
        qutip_sizes.append(n)
        qutip_times.append(t)

with open("run_time_ghz_state_projectq.txt", "r") as f:
    for line in f.readlines():
        words = line.split(" ")
        n = int(words[0].strip())
        t = float(words[1].strip())
        projectq_sizes.append(n)
        projectq_times.append(t)

with open("run_time_ghz_state_stabilizer.txt", "r") as f:
    for line in f.readlines():
        words = line.split(" ")
        n = int(words[0].strip())
        t = float(words[1].strip())
        stabilizer_sizes.append(n)
        stabilizer_times.append(t)

plt.plot(qutip_sizes, qutip_times)
plt.plot(projectq_sizes, projectq_times)
plt.plot(stabilizer_sizes, stabilizer_times)
plt.xlabel("Size of GHZ state (nr qubits)")
plt.ylabel("Runtime (s)")
plt.legend(["Backend: QuTip", "Backend: Project Q", "Backend: Stabilizer"])

plt.savefig("runtime_qutip_vs_projectq_vs_stabilizer.pdf")

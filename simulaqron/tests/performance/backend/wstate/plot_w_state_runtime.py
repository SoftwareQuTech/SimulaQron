from matplotlib import pyplot as plt

qutip_sizes = []
qutip_times = []
projectq_sizes = []
projectq_times = []

with open("run_time_w_state_qutip.txt", "r") as f:
    for line in f.readlines():
        words = line.split(" ")
        n = int(words[0].strip())
        t = float(words[1].strip())
        qutip_sizes.append(n)
        qutip_times.append(t)

with open("run_time_w_state_projectq.txt", "r") as f:
    for line in f.readlines():
        words = line.split(" ")
        n = int(words[0].strip())
        t = float(words[1].strip())
        projectq_sizes.append(n)
        projectq_times.append(t)

plt.plot(qutip_sizes, qutip_times)
plt.plot(projectq_sizes, projectq_times)
plt.xlabel("Size of W state (nr qubits)")
plt.ylabel("Runtime (s)")
plt.legend(["Backend: QuTip", "Backend: Project Q"])

plt.savefig("runtime_qutip_vs_projectq.png")

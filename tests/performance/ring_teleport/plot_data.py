import matplotlib.pyplot as plt
import sys

filename = sys.argv[1]

with open(filename + ".txt", "r") as f:
    data = f.readlines()

times = {}
avg = {}
for datapoint_str in data:
    datapoint = datapoint_str.split(", ")
    nr = int(datapoint[0])
    time = float(datapoint[1])
    if nr in times:
        times[nr].append(time)
    else:
        times[nr] = [time]

for (nr, tims) in times.items():
    avg[nr] = sum(tims) / len(tims)

plt.plot(list(avg.keys()), list(avg.values()), marker=".", markersize=10, linestyle="none", color="green")

with open(filename + "_v2.txt", "r") as f:
    data2 = f.readlines()

times2 = {}
avg2 = {}
for datapoint_str in data2:
    datapoint = datapoint_str.split(", ")
    nr = int(datapoint[0])
    time = float(datapoint[1])
    if nr in times2:
        times2[nr].append(time)
    else:
        times2[nr] = [time]

for (nr, tims) in times2.items():
    avg2[nr] = sum(tims) / len(tims)

plt.plot(list(avg2.keys()), list(avg2.values()), marker=".", markersize=10, linestyle="none", color="red")

plt.xlabel("nr of nodes")
plt.ylabel("time (s)")
plt.legend(["EPR on the fly", "EPR first"])

plt.savefig(filename + ".pdf")

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

plt.plot(list(avg.keys()), list(avg.values()), marker=".", markersize=10, linestyle="none", color="red")

plt.xlabel("nr of teleport (back & fourth)")
plt.ylabel("time (s)")

plt.savefig(filename + ".pdf")

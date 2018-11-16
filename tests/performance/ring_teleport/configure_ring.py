import sys
import os

netsim_path = os.environ["NETSIM"] + "/"
tot_nr = int(sys.argv[1])

# configure run files for nodes

with open("run.sh", "w") as f:
    f.write("#!/bin/sh\n\n")
    for i in range(tot_nr - 1):
        f.write("python node.py {} {} &\n".format(i, tot_nr))
    f.write("python node.py {} {}\n".format(tot_nr - 1, tot_nr))

with open("run_v2.sh", "w") as f:
    f.write("#!/bin/sh\n\n")
    for i in range(tot_nr - 1):
        f.write("python node_v2.py {} {} &\n".format(i, tot_nr))
    f.write("python node_v2.py {} {}\n".format(tot_nr - 1, tot_nr))

# configure network

nodes = "".join(["n" + str(i) + " " for i in range(tot_nr)])

os.system("python " + netsim_path + "configFiles.py " + nodes)

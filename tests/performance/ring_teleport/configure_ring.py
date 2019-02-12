import sys
import os

from simulaqron.toolbox import get_simulaqron_path

# Get path to SimulaQron folder
simulaqron_path = get_simulaqron_path.main()

tot_nr = int(sys.argv[1])

# configure run files for nodes

with open("run.sh", "w") as f:
    f.write("#!/bin/sh\n\n")
    for i in range(tot_nr - 1):
        f.write("python3 node.py {} {} &\n".format(i, tot_nr))
    f.write("python3 node.py {} {}\n".format(tot_nr - 1, tot_nr))

with open("run_v2.sh", "w") as f:
    f.write("#!/bin/sh\n\n")
    for i in range(tot_nr - 1):
        f.write("python3 node_v2.py {} {} &\n".format(i, tot_nr))
    f.write("python3 node_v2.py {} {}\n".format(tot_nr - 1, tot_nr))

# configure network

nodes = "".join(["n" + str(i) + " " for i in range(tot_nr)])

os.system("python3 " + simulaqron_path + "configFiles.py " + nodes)

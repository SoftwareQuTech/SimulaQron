import sys
import os

from simulaqron.toolbox import get_simulaqron_path

# Get path to SimulaQron folder
simulaqron_path = get_simulaqron_path.main()

input_data = sys.argv[1:]
if len(input_data) == 0:
    min_nodes = 2
    max_nodes = 3
    iterations = 1
elif len(input_data) == 1:
    min_nodes = 2
    max_nodes = int(input_data[0])
    iterations = 1
elif len(input_data) == 2:
    min_nodes = int(input_data[0])
    max_nodes = int(input_data[1])
    iterations = 1
else:
    min_nodes = int(input_data[0])
    max_nodes = int(input_data[1])
    iterations = int(input_data[2])


with open("times.txt", "w") as f:
    pass

with open("times_v2.txt", "w") as f:
    pass

for n in range(min_nodes, max_nodes + 1):
    os.system("python3 configure_ring.py {}".format(n))
    os.system("sh " + simulaqron_path + "run/startAll.sh")
    # time.sleep(30)
    for _ in range(iterations):
        os.system("sh doNew.sh")
        # time.sleep(10)
        os.system("sh doNew_v2.sh")
        # time.sleep(10)

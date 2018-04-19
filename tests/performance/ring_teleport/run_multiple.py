import sys
import os
import time

netsim_path=os.environ['NETSIM']+'/'
input_data=sys.argv[1:]
if len(input_data)==0:
	min_nodes=2
	max_nodes=3
elif len(input_data)==1:
	min_nodes=2
	max_nodes=int(input_data[0])
elif len(input_data)==2:
	min_nodes=int(input_data[0])
	max_nodes=int(input_data[1])
else:
	min_nodes=int(input_data[0])
	max_nodes=int(input_data[1])
	iterations=int(input_data[2])


with open('times.txt','w') as f:
	pass

with open('times_v2.txt','w') as f:
	pass

for n in range(min_nodes,max_nodes+1):
	os.system("python configure_ring.py {}".format(n))
	os.system("sh "+netsim_path+"run/startAll.sh")
	# time.sleep(5)
	for _ in range(iterations):
		os.system("sh donew.sh")
		# time.sleep(10)
		os.system("sh donew_v2.sh")
		# time.sleep(10)

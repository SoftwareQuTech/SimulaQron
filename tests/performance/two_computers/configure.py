import sys
import os

netsim_path=os.environ['NETSIM']+'/'
my_ip=sys.argv[1]
other_ip=sys.argv[2]
client=int(sys.argv[3])
min_tel=int(sys.argv[4])
max_tel=int(sys.argv[5])
number=int(sys.argv[6])

with open(netsim_path+"config/virtualNodes.cfg",'w') as f:
	if client:
		f.write("Alice, "+my_ip+", 8801\n")
		f.write("Bob, "+other_ip+", 8802")
	else:
		f.write("Alice, "+other_ip+", 8801\n")
		f.write("Bob, "+my_ip+", 8802")

with open(netsim_path+"config/cqcNodes.cfg",'w') as f:
	if client:
		f.write("Alice, "+my_ip+", 8803\n")
		f.write("Bob, "+other_ip+", 8804")
	else:
		f.write("Alice, "+other_ip+", 8803\n")
		f.write("Bob, "+my_ip+", 8804")

with open(netsim_path+"config/appNodes.cfg",'w') as f:
	if client:
		f.write("Alice, "+my_ip+", 8805\n")
		f.write("Bob, "+other_ip+", 8806")
	else:
		f.write("Alice, "+other_ip+", 8805\n")
		f.write("Bob, "+my_ip+", 8806")

with open('run.sh','w') as f:
	f.write('#!/bin/sh\n\n')
	if client:
		f.write("python "+netsim_path+"run/startNode.py Alice &\n")
		f.write("python "+netsim_path+"run/startCQC.py Alice &\n")
		# f.write("python "+netsim_path+"run/startNode.py Bob &\n")
		# f.write("python "+netsim_path+"run/startCQC.py Bob &\n")

		f.write("\nsleep 10s\n\n")

		# f.write("python server.py {} {} {}&\n".format(min_tel,max_tel,number))

		f.write("python client.py {} {} {}\n".format(min_tel,max_tel,number))
	else:
		f.write("python "+netsim_path+"run/startNode.py Bob\n")
		f.write("python "+netsim_path+"run/startCQC.py Bob\n")

		f.write("\nsleep 10s\n\n")

		f.write("python server.py {} {} {}\n".format(min_tel,max_tel,number))

def main():

	# Initialize the connection
	with CQCConnection("Alice") as Alice:

		print("Test")
		# Create an EPR pair
		q = Alice.createEPR("Bob")
		#q1 = qubit(Alice)
		#q2 = qubit(Alice)
		#q1.H()
		#q1.cnot(q2)

		#q1.send("Bob")
		#q.X();
		# Measure qubit
		#m1=q2.measure()
		#m2=q1.measure()
		m=q.measure()
		to_print="b App {}: Measurement outcome is: {}".format(Alice.name,m)
		#to_print2="b App {}: Measurement outcome is: {}".format(Alice.name,m2)
		print("|"+"-"*(len(to_print)+2)+"|")
		print("| "+to_print+" |")
		#print("| "+to_print2+" |")
		print("|"+"-"*(len(to_print)+2)+"|")
##################################################################################################
main()

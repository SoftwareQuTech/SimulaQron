#
# Copyright (c) 2017, Stephanie Wehner and Axel Dahlberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from cqc.pythonLib import CQCConnection, qubit

import sys
from timeit import default_timer as timer


#####################################################################################################
#
# main
#
def main():

    input_data = sys.argv[1:]

    # Set node numbers
    node_nr = int(input_data[0])
    tot_nr = int(input_data[1])
    next_node_nr = (node_nr + 1) % tot_nr

    # Initialize the connection
    node = CQCConnection("n" + str(node_nr))

    if node_nr == 0:  # this is the first node so create qubit

        # start timer
        t1 = timer()

        # Create a qubit to teleport
        q = qubit(node)

        # Prepare the qubit to teleport in |+>
        q.H()

        # ------
        # Qubit is created, send it to next node
        # ------

    else:  # we are node in chain so receive qubit

        # Make an EPR pair with previous node
        q = node.recvEPR()

        # Receive info about corrections
        data = node.recvClassical()
        message = list(data)
        a = message[0]
        b = message[1]

        # Apply corrections
        if b == 1:
            q.X()
        if a == 1:
            q.Z()

            # ------
            # Qubit is receive, send it to next node
            # ------

            # Make an EPR pair with next node
    qEPR = node.createEPR("n" + str(next_node_nr))

    # Apply the local teleportation operations
    q.cnot(qEPR)
    q.H()

    # Measure the qubits
    a = q.measure()
    b = qEPR.measure()
    to_print = "App {}: Measurement outcomes are: a={}, b={}".format(node.name, a, b)
    print("|" + "-" * (len(to_print) + 2) + "|")
    print("| " + to_print + " |")
    print("|" + "-" * (len(to_print) + 2) + "|")

    # Send corrections to next node
    node.sendClassical("n" + str(next_node_nr), [a, b])
    # node.closeClassicalChannel('n'+str(next_node_nr))

    if node_nr == 0:  # this is first node, so receive again after qubit traversed chain

        # Make an EPR pair with last node
        q = node.recvEPR()

        # Receive info about corrections
        data = node.recvClassical()
        message = list(data)
        a = message[0]
        b = message[1]

        # Apply corrections
        if b == 1:
            q.X()
        if a == 1:
            q.Z()

            # ------
            # Qubit is receive, so measure it
            # ------

            # measure the qubit, print the outcome and record the time it took
        m = q.measure()
        t2 = timer()
        to_print = "App {}: Measurement outcome is: m={}".format(node.name, m)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")
        to_print = "App {}: Time elapsed: t={}".format(node.name, t2 - t1)
        print("|" + "-" * (len(to_print) + 2) + "|")
        print("| " + to_print + " |")
        print("|" + "-" * (len(to_print) + 2) + "|")

        with open("times.txt", "a") as f:
            f.write("{}, {}\n".format(tot_nr, t2 - t1))

            # Stop the connection
    node.close()


##################################################################################################
main()

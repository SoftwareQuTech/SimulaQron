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

from cqc.pythonLib import CQCConnection

import sys


#####################################################################################################
#
# main
#
def main():

    input_data = sys.argv[1:]

    # Set node numbers
    min_tel = int(input_data[0])
    max_tel = int(input_data[1])
    number = int(input_data[2])

    # Initialize the connection
    Bob = CQCConnection("Bob")

    for n in range(min_tel, max_tel + 1):

        for _ in range(number):

            # Start teleporting back and fourth

            for _ in range(n):

                # Make an EPR pair with other node
                q = Bob.recvEPR()

                # Receive info about corrections
                data = Bob.recvClassical(timout=3600)
                Bob.closeClassicalServer()
                message = list(data)
                a = message[0]
                b = message[1]

                # Apply corrections
                if b == 1:
                    q.X()
                if a == 1:
                    q.Z()

                    # Make an EPR pair with next node
                qEPR = Bob.recvEPR()

                # Apply the local teleportation operations
                q.cnot(qEPR)
                q.H()

                # Measure the qubits
                a = q.measure()
                b = qEPR.measure()
                to_print = "App {}: Measurement outcomes are: a={}, b={}".format(Bob.name, a, b)
                print("|" + "-" * (len(to_print) + 2) + "|")
                print("| " + to_print + " |")
                print("|" + "-" * (len(to_print) + 2) + "|")

                # Send corrections to other node
                Bob.sendClassical("Alice", [a, b])
                Bob.closeClassicalChannel("Alice")

                # Stop the connection
    Bob.close()


##################################################################################################
main()

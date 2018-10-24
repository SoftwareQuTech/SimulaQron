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


from SimulaQron.cqc.pythonLib.cqc import *


#####################################################################################################
#
# main
#
def main():

    # Initialize the connection
    with CQCConnection("R1") as R1:

        # Make EPR-pairs with S1,S2 and R2
        qtmp1 = R1.recvEPR()
        qtmp2 = R1.recvEPR()
        q8 = R1.createEPR("R2")

        # Check where qubit are sent from
        if qtmp1.get_remote_entNode() == "S1":
            q3 = qtmp1
            q7 = qtmp2
        else:
            q3 = qtmp2
            q7 = qtmp1

            # Receive corrections
        msg1 = R1.recvClassical()
        msg2 = R1.recvClassical()

        # Do corrections
        if msg1[:2].decode("utf-8") == "S1":
            if msg1[2] == 1:
                q3.X()
            if msg2[2] == 1:
                q7.X()
        else:
            if msg1[2] == 1:
                q7.X()
            if msg2[2] == 1:
                q3.X()

                # Entangle and measure (step 2)
        q3.cnot(q8)
        q7.cnot(q8)
        m = q8.measure()

        # Send corrections to R2 (including sender) (step 2)
        msg = "R1".encode("utf-8") + bytes([m])
        R1.sendClassical("R2", msg)

        # Get correction from R2 (step 6)
        msg = R1.recvClassical()
        if msg[2] == 1:
            q3.Z()
            q7.Z()

            # H and measure qubits (step 7)
        q3.H()
        m1 = q3.measure()
        q7.H()
        m2 = q7.measure()

        # Send corrections to S1 and S2 (step 7)
        msg1 = "R1".encode("utf-8") + bytes([m1])
        R1.sendClassical("S1", msg1)
        msg2 = "R1".encode("utf-8") + bytes([m2])
        R1.sendClassical("S2", msg2)


##################################################################################################
main()

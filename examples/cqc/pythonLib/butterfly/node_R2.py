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


#####################################################################################################
#
# main
#
def main():

    # Initialize the connection
    with CQCConnection("R2") as R2:

        # Make EPR-pairs with T1,T2 and R1
        q9 = R2.recvEPR()
        q10 = R2.createEPR("T2")
        q12 = R2.createEPR("T1")

        # Receive corrections from R1 (step 2)
        msg = R2.recvClassical()
        if msg[2] == 1:
            q9.X()

            # Entangle and measure (step 3)
        q9.cnot(q10)
        q9.cnot(q12)
        m1 = q10.measure()
        m2 = q12.measure()

        # Send corrections to T1 and T2 (step 3)
        msg1 = "R2".encode("utf-8") + bytes([m1])
        R2.sendClassical("T2", msg1)
        msg2 = "R2".encode("utf-8") + bytes([m2])
        R2.sendClassical("T1", msg2)

        # Receive corrections from T1 and T2 (step 5)
        m1 = R2.recvClassical()[2]
        m2 = R2.recvClassical()[2]
        if (m1 + m2) % 2 == 1:
            q9.Z()

            # H and measure (step 6)
        q9.H()
        m = q9.measure()

        # Send corrections to R1 (step 6)
        msg = "R1".encode("utf-8") + bytes([m])
        R2.sendClassical("R1", msg)


##################################################################################################
main()

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

import logging
import os
import socket

from simulaqron.general.hostConfig import networkConfig
from cqc.backend.cqcHeader import CQCHeader, CQC_TP_HELLO, CQC_VERSION
from simulaqron.toolbox import get_simulaqron_path


#####################################################################################################
#
# init
#
def init(name, cqcFile=None):
    """
    Initialize a connection to the cqc server with the name given as input.
    A path to a configure file for the cqc network can be given,
    if it's not given the config file 'config/cqcNodes.cfg' will be used.
    Returns a socket object.
    """

    # This file defines the network of CQC servers interfacing to virtual quantum nodes
    if cqcFile is None:
        simulaqron_path = get_simulaqron_path.main()
        cqcFile = os.path.join(simulaqron_path, "config/cqcNodes.cfg")

        # Read configuration files for the cqc network
    cqcNet = networkConfig(cqcFile)

    # Host data
    if name in cqcNet.hostDict:
        myHost = cqcNet.hostDict[name]
    else:
        logging.error("The name '%s' is not in the cqc network.", name)
        raise LookupError("The name '%s' is not in the cqc network.".format(name))

    addr = myHost.addr

    # Connect to cqc server and run protocol
    cqc = None
    try:
        cqc = socket.socket(addr[0], addr[1], addr[2])
    except socket.error:
        logging.error("Could not connect to cqc server: %s", name)
    try:
        cqc.connect(addr[4])
    except socket.error:
        cqc.close()
        logging.error("Could not connect to cqc server: %s", name)
    return cqc


#####################################################################################################
#
# main
#
def main():

    # In this example, we are Alice.
    myName = "Alice"

    # Initialize the connection
    cqc = init(myName)

    # Send Hello message
    print("App {} tells CQC: 'HELLO'".format(myName))
    hdr = CQCHeader()
    hdr.setVals(CQC_VERSION, CQC_TP_HELLO, 0, 0)
    msg = hdr.pack()
    cqc.send(msg)

    # Receive return message
    data = cqc.recv(192)
    hdr = CQCHeader(data)
    if hdr.tp == CQC_TP_HELLO:
        print("CQC tells App {}: 'HELLO'".format(myName))
    else:
        print("Did not receive a hello message, but rather: {}".format(hdr.printable()))

        # Close the connection
    cqc.close()


##################################################################################################
main()

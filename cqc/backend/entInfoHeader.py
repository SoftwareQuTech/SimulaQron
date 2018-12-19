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
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES
# LOSS OF USE, DATA, OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging

import struct
import bitstring

from SimulaQron.cqc.backend.cqcHeader import Header

# Lengths of the headers in bytes
ENT_INFO_LENGTH = 40  # Length of a entanglement information header
ENT_INFO_CREATE_KEEP_LENGTH = 28  # Length of a entanglement information header (for create and keep)
ENT_INFO_MEAS_DIRECT_LENGTH = 24  # Length of a entanglement information header (for measure directly)

ENT_INFO_TP_CREATE_KEEP = 1  # Type of message when entanglement is kept
ENT_INFO_TP_MEAS_DIRECT = 2  # Type of message when entanglement is measured directly (for classical correlations)


class EntInfoHeader(Header):
    """
    Header for a entanglement information packet. Fo
    """

    HDR_LENGTH = ENT_INFO_LENGTH
    packaging_format = "!LHHLHHLQQHBB"

    def _setVals(self, node_A=0, port_A=0, app_id_A=0, node_B=0, port_B=0, app_id_B=0, id_AB=0, timestamp=0, ToG=0,
                 goodness=0, DF=0):
        """
        Set using given values.
        """
        self.type = type
        self.node_A = node_A
        self.port_A = port_A
        self.app_id_A = app_id_A

        self.node_B = node_B
        self.port_B = port_B
        self.app_id_B = app_id_B

        self.id_AB = id_AB

        self.timestamp = timestamp
        self.ToG = ToG
        self.goodness = goodness
        self.DF = DF

        self.is_set = True

    def _pack(self):
        """
        Pack data into packet format. For defnitions see cLib/cgc.h
        """
        ent_info = struct.pack(
            self.packaging_format,
            self.node_A,
            self.port_A,
            self.app_id_A,
            self.node_B,
            self.port_B,
            self.app_id_B,
            self.id_AB,
            self.timestamp,
            self.ToG,
            self.goodness,
            self.DF,
            0,
        )
        return ent_info

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For definitions see cLib/cqc.h
        """
        ent_info = struct.unpack(self.packaging_format, headerBytes)

        self.node_A = ent_info[0]
        self.port_A = ent_info[1]
        self.app_id_A = ent_info[2]

        self.node_B = ent_info[3]
        self.port_B = ent_info[4]
        self.app_id_B = ent_info[5]

        self.id_AB = ent_info[6]

        self.timestamp = ent_info[7]
        self.ToG = ent_info[8]
        self.goodness = ent_info[9]
        self.DF = ent_info[10]

    def _printable(self):
        """
        Produce a printable string for information purposes.
        """
        toPrint = "A: ({}, {}, {})".format(self.node_A, self.port_A, self.app_id_A) + " "
        toPrint += "B: ({}, {}, {})".format(self.node_B, self.port_B, self.app_id_B) + " "
        toPrint += "Entanglement ID: " + str(self.id_AB) + " "
        toPrint += "Timestamp: " + str(self.timestamp) + " "
        toPrint += "Time of Goodness: " + str(self.ToG) + " "
        toPrint += "Goodness: " + str(self.goodness) + " "
        toPrint += "Directionality Flag: " + str(self.DF)
        return toPrint

    def switch_nodes(self):
        """
        Switches the ip and port of the nodes and flips the directionality flag.
        Used to give correct message to both nodes.
        """

        # Get current info
        node_A = self.node_A
        port_A = self.port_A
        app_id_A = self.app_id_A
        node_B = self.node_B
        port_B = self.port_B
        app_id_B = self.app_id_B
        DF = self.DF

        # Update
        self.node_A = node_B
        self.port_A = port_B
        self.app_id_A = app_id_B
        self.node_B = node_A
        self.port_B = port_A
        self.app_id_B = app_id_A
        if DF == 0:
            self.DF = 0
        elif DF == 1:
            self.DF = 2
        elif DF == 2:
            self.DF = 1
        else:
            logging.warning("Unknown directionality flag")
            self.DF = DF


class EntInfoCreateKeepHeader(Header):
    """
        Header for a entanglement information packet, where entanglement is kept after generation
    """

    type = ENT_INFO_TP_CREATE_KEEP
    package_format = (
        "uint:4=type, "
        "uint:16=mhp_seq, "
        "uint:1=DF, "
        "uint:11=0, "
        "uint:32=ip_A, "
        "uint:32=ip_B, "
        "uint:16=port_A, "
        "uint:16=port_B, "
        "float:32=t_create, "
        "float:32=t_goodness, "
        "float:32=goodness, "
        "uint:32=create_id"
    )

    HDR_LENGTH = ENT_INFO_CREATE_KEEP_LENGTH

    def _setVals(self, ip_A=0, port_A=0, ip_B=0, port_B=0, mhp_seq=0, t_create=0.0, t_goodness=0.0, goodness=0.0, DF=0,
                 create_id=0):
        """
        Set using given values.
        """
        self.ip_A = ip_A
        self.port_A = port_A

        self.ip_B = ip_B
        self.port_B = port_B

        self.mhp_seq = mhp_seq

        self.t_create = t_create
        self.t_goodness = t_goodness
        self.goodness = goodness
        self.DF = DF
        self.create_id = create_id

    def _pack(self):
        """
        Pack data into packet format. For defnitions see cLib/cgc.h
        """

        to_pack = {
            "type": self.type,
            "ip_A": self.ip_A,
            "port_A": self.port_A,
            "ip_B": self.ip_B,
            "port_B": self.port_B,
            "mhp_seq": self.mhp_seq,
            "t_create": self.t_create,
            "t_goodness": self.t_goodness,
            "goodness": self.goodness,
            "DF": self.DF,
            "create_id": self.create_id,
        }
        ent_info_Bitstring = bitstring.pack(self.package_format, **to_pack)
        ent_info = ent_info_Bitstring.tobytes()
        return ent_info

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For definitions see cLib/cqc.h
        """
        ent_info_Bitstring = bitstring.BitString(headerBytes)
        type = ent_info_Bitstring.read("uint:4")
        if type != self.type:
            raise ValueError("Not an OK of type create-keep")

        ent_info = ent_info_Bitstring.unpack(self.package_format)

        self.mhp_seq = ent_info[1]
        self.DF = ent_info[2]
        self.ip_A = ent_info[4]
        self.ip_B = ent_info[5]
        self.port_A = ent_info[6]
        self.port_B = ent_info[7]
        self.t_create = ent_info[8]
        self.t_goodness = ent_info[9]
        self.goodness = ent_info[10]
        self.create_id = ent_info[11]

    def _printable(self):
        """
        Produce a printable string for information purposes.
        """
        toPrint = "Create and Keep OK with createID={}".format(self.create_id) + " "
        toPrint += "A: ({}, {})".format(self.ip_A, self.port_A) + " "
        toPrint += "B: ({}, {})".format(self.ip_B, self.port_B) + " "
        toPrint += "MHP seq.: " + str(self.mhp_seq) + " "
        toPrint += "Time of creation: " + str(self.t_create) + " "
        toPrint += "Time of Goodness: " + str(self.t_goodness) + " "
        toPrint += "Goodness: " + str(self.goodness) + " "
        toPrint += "Directionality Flag: " + str(self.DF)
        return toPrint

    def switch_nodes(self):
        """
        Switches the ip and port of the nodes and flips the directionality flag.
        Used to give correct message to both nodes.
        """

        # Get current info
        ip_A = self.ip_A
        port_A = self.port_A
        ip_B = self.ip_B
        port_B = self.port_B
        DF = self.DF

        # Update
        self.ip_A = ip_B
        self.port_A = port_B
        self.ip_B = ip_A
        self.port_B = port_A
        if DF == 0:
            self.DF = 0
        elif DF == 1:
            self.DF = 2
        elif DF == 2:
            self.DF = 1
        else:
            logging.warning("Unknown directionality flag")
            self.DF = DF


class EntInfoMeasDirectHeader(Header):
    """
        Header for a entanglement information packet, where communication qubit is measured directly after emission.
    """

    type = ENT_INFO_TP_MEAS_DIRECT
    package_format = (
        "uint:4=type, "
        "uint:16=mhp_seq, "
        "uint:1=DF, "
        "uint:1=meas_out, "
        "uint:2=basis, "
        "uint:9=0, "
        "uint:32=ip_A, "
        "uint:32=ip_B, "
        "uint:16=port_A, "
        "uint:16=port_B, "
        "float:32=t_create, "
        "float:32=goodness, "
        "uint:32=create_id"
    )

    HDR_LENGTH = ENT_INFO_MEAS_DIRECT_LENGTH

    def _setVals(self, ip_A=0, port_A=0, ip_B=0, port_B=0, mhp_seq=0, meas_out=0, basis=0, t_create=0.0, goodness=0.0,
                 DF=0, create_id=0):
        """
        Set using given values.
        """
        self.ip_A = ip_A
        self.port_A = port_A

        self.ip_B = ip_B
        self.port_B = port_B

        self.mhp_seq = mhp_seq

        self.meas_out = meas_out
        self.basis = basis

        self.t_create = t_create
        self.goodness = goodness
        self.DF = DF
        self.create_id = create_id

    def _pack(self):
        """
        Pack data into packet format. For defnitions see cLib/cgc.h
        """
        to_pack = {
            "type": self.type,
            "ip_A": self.ip_A,
            "port_A": self.port_A,
            "ip_B": self.ip_B,
            "port_B": self.port_B,
            "mhp_seq": self.mhp_seq,
            "meas_out": self.meas_out,
            "basis": self.basis,
            "t_create": self.t_create,
            "goodness": self.goodness,
            "DF": self.DF,
            "create_id": self.create_id,
        }
        ent_info_Bitstring = bitstring.pack(self.package_format, **to_pack)
        ent_info = ent_info_Bitstring.tobytes()
        return ent_info

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For definitions see cLib/cqc.h
        """
        ent_info_Bitstring = bitstring.BitString(headerBytes)
        type = ent_info_Bitstring.read("uint:4")
        if type != self.type:
            raise ValueError("Not an OK of type measure-directly")

        ent_info = ent_info_Bitstring.unpack(self.package_format)

        self.mhp_seq = ent_info[1]
        self.DF = ent_info[2]
        self.meas_out = ent_info[3]
        self.basis = ent_info[4]
        self.ip_A = ent_info[6]
        self.ip_B = ent_info[7]
        self.port_A = ent_info[8]
        self.port_B = ent_info[9]
        self.t_create = ent_info[10]
        self.goodness = ent_info[11]
        self.create_id = ent_info[12]

    def _printable(self):
        """
        Produce a printable string for information purposes.
        """
        toPrint = "Measure Direclty OK with createID={}".format(self.create_id) + " "
        toPrint += "A: ({}, {})".format(self.ip_A, self.port_A) + " "
        toPrint += "B: ({}, {})".format(self.ip_B, self.port_B) + " "
        toPrint += "MHP seq.: " + str(self.mhp_seq) + " "
        toPrint += "Measurement outcome: " + str(self.meas_out) + " "
        toPrint += "Measurement basis: " + str(self.basis) + " "
        toPrint += "Time of creation: " + str(self.t_create) + " "
        toPrint += "Goodness: " + str(self.goodness) + " "
        toPrint += "Directionality Flag: " + str(self.DF)
        return toPrint

    def switch_nodes(self):
        """
        Switches the ip and port of the nodes and flips the directionality flag.
        Used to give correct message to both nodes.
        """

        # Get current info
        ip_A = self.ip_A
        port_A = self.port_A
        ip_B = self.ip_B
        port_B = self.port_B
        DF = self.DF

        # Update
        self.ip_A = ip_B
        self.port_A = port_B
        self.ip_B = ip_A
        self.port_B = port_A
        if DF == 0:
            self.DF = 0
        elif DF == 1:
            self.DF = 2
        elif DF == 2:
            self.DF = 1
        else:
            logging.warning("Unknown directionality flag")
            self.DF = DF

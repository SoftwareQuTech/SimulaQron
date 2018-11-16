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

import warnings

import struct
import bitstring

# Constant defining CQC version
CQC_VERSION = 1

# Lengths of the headers in bytes
CQC_HDR_LENGTH = 8  # Length of the CQC Header
CQC_CMD_HDR_LENGTH = 4  # Length of a command header
CQC_CMD_XTRA_LENGTH = 16  # Length of extra command information
CQC_NOTIFY_LENGTH = 20  # Length of a notification send from the CQC upwards
CQC_EPR_REQ_LENGTH = 16  # Length of EPR request header

# Constants defining the messages types
CQC_TP_HELLO = 0  # Alive check
CQC_TP_COMMAND = 1  # Execute a command list
CQC_TP_FACTORY = 2  # Start executing command list repeatedly
CQC_TP_EXPIRE = 3  # Qubit has expired
CQC_TP_DONE = 4  # Done with command
CQC_TP_RECV = 5  # Received qubit
CQC_TP_EPR_OK = 6  # Created EPR pair
CQC_TP_MEASOUT = 7  # Measurement outcome
CQC_TP_GET_TIME = 8  # Get creation time of qubit
CQC_TP_INF_TIME = 9  # Return timinig information
CQC_TP_NEW_OK = 10  # Created a new qubit

CQC_ERR_GENERAL = 20  # General purpose error (no details
CQC_ERR_NOQUBIT = 21  # No more qubits available
CQC_ERR_UNSUPP = 22  # No sequence not supported
CQC_ERR_TIMEOUT = 23  # Timeout
CQC_ERR_INUSE = 24  # Qubit already in use
CQC_ERR_UNKNOWN = 25  # Unknown qubit ID

# Possible commands
CQC_CMD_I = 0  # Identity (do nothing, wait one step)
CQC_CMD_NEW = 1  # Ask for a new qubit
CQC_CMD_MEASURE = 2  # Measure qubit
CQC_CMD_MEASURE_INPLACE = 3  # Measure qubit inplace
CQC_CMD_RESET = 4  # Reset qubit to |0>
CQC_CMD_SEND = 5  # Send qubit to another node
CQC_CMD_RECV = 6  # Ask to receive qubit
CQC_CMD_EPR = 7  # Create EPR pair with the specified node
CQC_CMD_EPR_RECV = 8  # Receive half of EPR pair created with other node

CQC_CMD_X = 10  # Pauli X
CQC_CMD_Z = 11  # Pauli Z
CQC_CMD_Y = 12  # Pauli Y
CQC_CMD_T = 13  # T Gate
CQC_CMD_ROT_X = 14  # Rotation over angle around X in 2pi/256 increments
CQC_CMD_ROT_Y = 15  # Rotation over angle around Y in 2pi/256 increments
CQC_CMD_ROT_Z = 16  # Rotation over angle around Z in 2pi/256 increments
CQC_CMD_H = 17  # Hadamard H
CQC_CMD_K = 18  # K Gate - taking computational to Y eigenbasis

CQC_CMD_CNOT = 20  # CNOT Gate with this as control
CQC_CMD_CPHASE = 21  # CPHASE Gate with this as control

CQC_CMD_ALLOCATE = 22  # Allocate a number of qubits
CQC_CMD_RELEASE = 23  # Release a qubit

# Command options
CQC_OPT_NOTIFY = 0x01  # Send a notification when cmd done
CQC_OPT_ACTION = 0x02  # On if there are actions to execute when done
CQC_OPT_BLOCK = 0x04  # Block until command is done


class CQCHeader:
    """
        Definition of the general CQC header.
    """

    def __init__(self, headerBytes=None):
        """
            Initialize using values received from a packet.
        """
        if headerBytes is None:
            self.is_set = False
            self.version = 0
            self.tp = 0
            self.app_id = 0
            self.length = 0
        else:
            self.unpack(headerBytes)

    def setVals(self, version, tp, app_id, length):
        """
            Set using given values.
        """
        self.version = version
        self.tp = tp
        self.app_id = app_id
        self.length = length
        self.is_set = True

    def pack(self):
        """
            Pack data into packet format. For defnitions see cLib/cgc.h
        """
        if not self.is_set:
            return 0
        cqcH = struct.pack("!BBHL", self.version, self.tp, self.app_id, self.length)
        return cqcH

    def unpack(self, headerBytes):
        """
            Unpack packet data. For definitions see cLib/cqc.h
        """
        cqcH = struct.unpack("!BBHL", headerBytes)
        self.version = cqcH[0]
        self.tp = cqcH[1]
        self.app_id = cqcH[2]
        self.length = cqcH[3]
        self.is_set = True

    def printable(self):
        """
            Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "CQC Header. Version: " + str(self.version) + " "
        toPrint = toPrint + "Type: " + str(self.tp) + " "
        toPrint = toPrint + "App ID: " + str(self.app_id) + " "
        toPrint += "Length: " + str(self.length)
        return toPrint


class CQCCmdHeader:
    """
        Header for a command instruction packet.
    """

    HDR_LENGTH = CQC_CMD_HDR_LENGTH

    def __init__(self, headerBytes=None):
        """
        Initialize using values received from a packet, if available.
        """
        self.notify = False
        self.block = False
        self.action = False

        if headerBytes is None:
            self.is_set = False
            self.qubit_id = 0
            self.instr = 0
        else:
            self.unpack(headerBytes)

    def setVals(self, qubit_id, instr, notify, block, action):
        """
        Set using given values.
        """
        self.qubit_id = qubit_id
        self.instr = instr
        self.notify = notify
        self.block = block
        self.action = action
        self.is_set = True

    def pack(self):
        """
        Pack data into packet format. For defnitions see cLib/cgc.h
        """

        if not self.is_set:
            return 0

        opt = 0
        if self.notify:
            opt = opt | CQC_OPT_NOTIFY
        if self.block:
            opt = opt | CQC_OPT_BLOCK
        if self.action:
            opt = opt | CQC_OPT_ACTION

        cmdH = struct.pack("!HBB", self.qubit_id, self.instr, opt)
        return cmdH

    def unpack(self, headerBytes):
        """
        Unpack packet data. For definitions see cLib/cqc.h
        """
        cmdH = struct.unpack("!HBB", headerBytes)

        self.qubit_id = cmdH[0]
        self.instr = cmdH[1]

        if cmdH[2] & CQC_OPT_NOTIFY:
            self.notify = True
        if cmdH[2] & CQC_OPT_BLOCK:
            self.block = True
        if cmdH[2] & CQC_OPT_ACTION:
            self.action = True

        self.is_set = True

    def printable(self):
        """
        Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "Command Header. Qubit ID: " + str(self.qubit_id) + " "
        toPrint = toPrint + "Instruction: " + str(self.instr) + " "
        toPrint = toPrint + "Notify: " + str(self.notify) + " "
        toPrint = toPrint + "Block: " + str(self.block) + " "
        toPrint = toPrint + "Action: " + str(self.action)
        return toPrint


class CQCXtraHeader:
    """
    Optional addtional cmd header information. Only relevant for certain commands.
    """

    HDR_LENGTH = 16

    # Deprecated, split into multiple headers
    def __init__(self, headerBytes=None):
        """
        Initialize using values received from a packet.
        """
        warnings.warn("Xtra Header is deprecated, it is split into different headers", DeprecationWarning)
        if headerBytes is None:
            self.is_set = False
            self.qubit_id = 0
            self.step = 0
            self.remote_app_id = 0
            self.remote_node = 0
            self.remote_port = 0
            self.cmdLength = 0
        else:
            self.unpack(headerBytes)

    def setVals(self, xtra_qubit_id, step, remote_app_id, remote_node, remote_port, cmdLength):
        """
            Set using given values.
        """
        self.qubit_id = xtra_qubit_id
        self.step = step
        self.remote_app_id = remote_app_id
        self.remote_node = remote_node
        self.remote_port = remote_port
        self.cmdLength = cmdLength
        self.is_set = True

    def pack(self):
        """
            Pack data into packet form. For definitions see cLib/cqc.h
        """
        if not self.is_set:
            return 0

        xtraH = struct.pack(
            "!HHLLHBB",
            self.qubit_id,
            self.remote_app_id,
            self.remote_node,
            self.cmdLength,
            self.remote_port,
            self.step,
            0,
        )
        return xtraH

    def unpack(self, headerBytes):
        """
            Unpack packet data. For defnitions see cLib/cqc.h
        """
        xtraH = struct.unpack("!HHLLHBB", headerBytes)

        self.qubit_id = xtraH[0]
        self.remote_app_id = xtraH[1]
        self.remote_node = xtraH[2]
        self.cmdLength = xtraH[3]
        self.remote_port = xtraH[4]
        self.step = xtraH[5]
        self.is_set = True

    def printable(self):
        """
            Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "Xtra Qubit: " + str(self.qubit_id) + " "
        toPrint = toPrint + "Angle Step: " + str(self.step) + " "
        toPrint = toPrint + "Remote App ID: " + str(self.remote_app_id) + " "
        toPrint = toPrint + "Remote Node: " + str(self.remote_node) + " "
        toPrint = toPrint + "Remote Port: " + str(self.remote_port) + " "
        toPrint = toPrint + "Command Length: " + str(self.cmdLength)

        return toPrint


class CQCSequenceHeader:
    """
        Header used to indicate size of a sequence.
        Currently exactly the same as CQCRotationHeaer.
        Seperate classes used clearity and for possible future adaptability. (Increase length for example)
    """

    packaging_format = "!B"
    HDR_LENGTH = 1

    def __init__(self, headerBytes=None):
        """
        Initialize from packet data
        :param headerBytes:  packet data
        """
        if headerBytes is None:
            self.is_set = False
            self.cmd_length = 0

        else:
            self.unpack(headerBytes)

    def setVals(self, cmd_length):
        """
        Set header using given values
        :param cmd_length: The step size of the rotation
        """
        self.is_set = True
        self.cmd_length = cmd_length

    def pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        if not self.is_set:
            return 0

        q_header = struct.pack(self.packaging_format, self.cmd_length)
        return q_header

    def unpack(self, headerBytes):
        """
        Unpack packet data. For defnitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        seq_header = struct.unpack(self.packaging_format, headerBytes)
        self.cmd_length = seq_header[0]
        self.is_set = True

    def printable(self):
        """
            Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "Sequence header. "
        toPrint += "Command length: " + str(self.cmd_length) + " "

        return toPrint


class CQCRotationHeader:
    """
        Header used to define the rotation angle of a gate
    """

    packaging_format = "!B"
    HDR_LENGTH = 1

    def __init__(self, headerBytes=None):
        """
        Initialize from packet data
        :param headerBytes:  packet data
        """
        if headerBytes is None:
            self.is_set = False
            self.step = 0

        else:
            self.unpack(headerBytes)

    def setVals(self, step):
        """
        Set header using given values
        :param step: The step size of the rotation
        """
        self.is_set = True
        self.step = step

    def pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        if not self.is_set:
            return 0

        q_header = struct.pack(self.packaging_format, self.step)
        return q_header

    def unpack(self, headerBytes):
        """
        Unpack packet data. For defnitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        rot_header = struct.unpack(self.packaging_format, headerBytes)
        self.step = rot_header[0]
        self.is_set = True

    def printable(self):
        """
            Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "Rotation header. "
        toPrint += "step size: " + str(self.step) + " "

        return toPrint


class CQCXtraQubitHeader:
    """
        Header used to send qubit of a secondary qubit for two qubit gates
    """

    packaging_format = "!H"
    HDR_LENGTH = 2

    def __init__(self, headerBytes=None):
        """
        Initialize from packet data
        :param headerBytes:  packet data
        """
        if headerBytes is None:
            self.is_set = False
            self.qubit_id = 0

        else:
            self.unpack(headerBytes)

    def setVals(self, qubit_id):
        """
        Set header using given values
        :param qubit_id: The id of the secondary qubit
        """
        self.is_set = True
        self.qubit_id = qubit_id

    def pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        if not self.is_set:
            return 0

        q_header = struct.pack(self.packaging_format, self.qubit_id)
        return q_header

    def unpack(self, headerBytes):
        """
        Unpack packet data. For defnitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        com_header = struct.unpack(self.packaging_format, headerBytes)
        self.qubit_id = com_header[0]
        self.is_set = True

    def printable(self):
        """
            Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "Extra Qubit header. "
        toPrint += "qubit id: " + str(self.qubit_id) + " "

        return toPrint


class CQCCommunicationHeader:
    """
        Header used to send information to which node to send information to.
        Used for example in Send and EPR commands
        This header has a size of 8
    """

    packaging_format = "!HLH"
    HDR_LENGTH = 8

    def __init__(self, headerBytes=None):
        """
        Initialize from packet data
        :param headerBytes:  packet data
        """
        if headerBytes is None:
            self.is_set = False
            self.remote_app_id = 0
            self.remote_node = 0
            self.remote_port = 0

        else:
            self.unpack(headerBytes)

    def setVals(self, remote_app_id, remote_node, remote_port):
        """
        Set header using given values
        :param remote_app_id: Application ID of remote host
        :param remote_node: IP of remote host in cqc network
        :param remote_port: port of remote hode in cqc network
        """
        self.is_set = True
        self.remote_app_id = remote_app_id
        self.remote_node = remote_node
        self.remote_port = remote_port

    def pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        if not self.is_set:
            return 0

        com_header = struct.pack(self.packaging_format, self.remote_app_id, self.remote_node, self.remote_port)
        return com_header

    def unpack(self, headerBytes):
        """
        Unpack packet data. For defnitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        com_header = struct.unpack(self.packaging_format, headerBytes)
        self.remote_app_id = com_header[0]
        self.remote_node = com_header[1]
        self.remote_port = com_header[2]
        self.is_set = True

    def printable(self):
        """
            Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "Communication header. "
        toPrint += "Remote App ID: " + str(self.remote_app_id) + " "
        toPrint += "Remote Node: " + str(self.remote_node) + " "
        toPrint += "Remote Port: " + str(self.remote_port) + " "

        return toPrint


class CQCFactoryHeader:
    """
    Header used to send factory information
    """

    # could maybe include the notify flag in num_iter?
    # That halfs the amount of possible num_iter from 256 to 128
    package_format = "!BB"
    HDR_LENGTH = 2

    def __init__(self, headerBytes=None):
        """
            Initialize from packet data.
        """
        if headerBytes is None:
            self.is_set = False
            self.num_iter = 0
            self.notify = False
            self.block = False
        else:
            self.unpack(headerBytes)

    def setVals(self, num_iter, notify, block):
        """
        Set using give values
        :param num_iter: The amount of iterations to this factory
        :param notify: 		True if the factory should send a done message back
        :param block:		True if all commands in this factory should be blocked
        """
        self.num_iter = num_iter
        self.notify = notify
        self.block = block
        self.is_set = True

    def pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        """
        if not self.is_set:
            return 0

        opt = 0
        if self.notify:
            opt = opt | CQC_OPT_NOTIFY
        if self.block:
            opt = opt | CQC_OPT_BLOCK

        factH = struct.pack(self.package_format, self.num_iter, opt)
        return factH

    def unpack(self, headerBytes):
        """
            Unpack packet data. For defnitions see cLib/cqc.h
        """
        fact_hdr = struct.unpack(self.package_format, headerBytes)

        self.notify = fact_hdr[1] & CQC_OPT_NOTIFY
        self.block = fact_hdr[1] & CQC_OPT_BLOCK

        self.num_iter = fact_hdr[0]
        self.is_set = True

    def printable(self):
        """
            Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "Factory Header. "
        toPrint += "Number of iterations: " + str(self.num_iter) + " "
        return toPrint


class CQCNotifyHeader:
    """
        Header used to specify notification details.
    """

    def __init__(self, headerBytes=None):
        """
            Initialize from packet data.
        """
        if headerBytes is None:
            self.is_set = False
            self.qubit_id = 0
            self.outcome = 0
            self.remote_app_id = 0
            self.remote_node = 0
            self.remote_port = 0
            self.datetime = 0
        else:
            self.unpack(headerBytes)

    def setVals(self, qubit_id, outcome, remote_app_id, remote_node, remote_port, datetime):
        """
        Set using given values.
        """
        self.qubit_id = qubit_id
        self.outcome = outcome
        self.remote_app_id = remote_app_id
        self.remote_node = remote_node
        self.remote_port = remote_port
        self.datetime = datetime
        self.is_set = True

    def pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        """
        if not self.is_set:
            return 0

        xtraH = struct.pack(
            "!HHLQHBB",
            self.qubit_id,
            self.remote_app_id,
            self.remote_node,
            self.datetime,
            self.remote_port,
            self.outcome,
            0,
        )
        return xtraH

    def unpack(self, headerBytes):
        """
            Unpack packet data. For defnitions see cLib/cqc.h
        """
        xtraH = struct.unpack("!HHLQHBB", headerBytes)

        self.qubit_id = xtraH[0]
        self.remote_app_id = xtraH[1]
        self.remote_node = xtraH[2]
        self.datetime = xtraH[3]
        self.remote_port = xtraH[4]
        self.outcome = xtraH[5]
        self.is_set = True

    def printable(self):
        """
            Produce a printable string for information purposes.
        """
        if not self.is_set:
            return " "

        toPrint = "Qubit ID: " + str(self.qubit_id) + " "
        toPrint = toPrint + "Outcome: " + str(self.outcome) + " "
        toPrint = toPrint + "Remote App ID: " + str(self.remote_app_id) + " "
        toPrint = toPrint + "Remote Node: " + str(self.remote_node) + " "
        toPrint = toPrint + "Remote Port: " + str(self.remote_port) + " "
        toPrint = toPrint + "Datetime: " + str(self.datetime)
        return toPrint


class CQCEPRRequestHeader:
    package_format = (
        "uint:32=remote_ip, "
        "float:32=min_fidelity, "
        "float:32=max_time, "
        "uint:16=remote_port, "
        "uint:8=num_pairs, "
        "uint:4=priority",
        "uint:1=store, " "uint:1=measure_directly, " "uint:2=0",
    )
    HDR_LENGTH = 16

    def __init__(self, headerBytes=None):
        """
        Initialize using values received from a packet.
        :param headerBytes: bytes
        """
        if headerBytes is None:
            self.is_set = False
            self.remote_ip = 0
            self.remote_port = 0
            self.num_pairs = 0
            self.min_fidelity = 0.0
            self.max_time = 0.0
            self.priority = 0
            self.store = True
            self.measure_directly = False

            self.is_set = False
        else:
            self.unpack(headerBytes)

    def setVals(self, remote_ip, remote_port, num_pairs, min_fidelity, max_time, priority, store, measure_directly):
        """
        Stores required parameters of Entanglement Generation Protocol Request

        :param remote_ip: int
            IP of the other node we are attempting to generate entanglement with
        :param remote_port: int
            Port number of other node.
        :param num_pairs: int
            The number of entangled pairs we are trying to generate
        :param min_fidelity: float
            The minimum acceptable fidelity for the pairs we are generating
        :param max_time: float
            The maximum amount of time we are permitted to take when generating the pairs
        :param priority: obj
            Priority on the request
        :param store: bool
            Specifies whether entangled qubits should be stored within a storage qubit or left within the communication
            qubit
        :param measure_directly: bool
            Specifies whether to measure the communication qubit directly after the photon is emitted
        """
        self.is_set = True
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.num_pairs = num_pairs
        self.min_fidelity = min_fidelity
        self.max_time = max_time
        self.priority = priority
        self.store = store
        self.measure_directly = measure_directly

        self.is_set = True

    def pack(self):
        """
        Pack the data in packet form.
        :return: str
        """
        if not self.is_set:
            return 0

        to_pack = {
            "remote_ip": self.remote_ip,
            "remote_port": self.remote_port,
            "min_fidelity": self.min_fidelity,
            "max_time": self.max_time,
            "num_pairs": self.num_pairs,
            "priority": self.priority,
            "store": self.store,
            "measure_directly": self.measure_directly,
        }
        request_Bitstring = bitstring.pack(self.package_format, **to_pack)
        requestH = request_Bitstring.tobytes()

        return requestH

    def unpack(self, headerBytes):
        """
        Unpack data.
        :param headerBytes: str
        :return:
        """
        request_Bitstring = bitstring.BitString(headerBytes)
        request_fields = request_Bitstring.unpack(self.package_format)
        self.remote_ip = request_fields[0]
        self.min_fidelity = request_fields[1]
        self.max_time = request_fields[2]
        self.remote_port = request_fields[3]
        self.num_pairs = request_fields[4]
        self.priority = request_fields[5]
        self.store = request_fields[6]
        self.measure_directly = request_fields[7]

        self.is_set = True

    def printable(self):
        """
        Produce printable string for information purposes
        :return: str
        """
        if not self.is_set:
            return " "
        else:
            to_print = "EPR Request Header."
            to_print += "Remote IP: {}".format(self.remote_ip)
            to_print += "Remote port: {}".format(self.remote_port)
            to_print += "Min Fidelity: {}".format(self.min_fidelity)
            to_print += "Max Time: {}".format(self.max_time)
            to_print += "Num Pairs: {}".format(self.num_pairs)
            to_print += "Priority: {}".format(self.priority)
            to_print += "Store: {}".format(self.store)
            to_print += "Measure Directly: {}".format(self.measure_directly)

            return to_print

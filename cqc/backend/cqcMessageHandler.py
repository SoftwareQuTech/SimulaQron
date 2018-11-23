# Copyright (c) 2017-2018, Stephanie Wehner and Axel Dahlberg
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

from abc import ABC, abstractmethod
from heapq import heappush, heappop
from collections import defaultdict
import logging
import numpy as np
import time

from SimulaQron.cqc.backend.cqcConfig import CQC_CONF_WAIT_TIME_RECV, CQC_CONF_RECV_TIMEOUT, CQC_CONF_RECV_EPR_TIMEOUT
from SimulaQron.cqc.backend.cqcHeader import (
    CQCCmdHeader,
    CQC_CMD_SEND,
    CQC_CMD_EPR,
    CQC_CMD_CNOT,
    CQC_CMD_CPHASE,
    CQC_CMD_ROT_X,
    CQC_CMD_ROT_Y,
    CQC_CMD_ROT_Z,
    CQC_TP_HELLO,
    CQC_TP_COMMAND,
    CQC_TP_FACTORY,
    CQC_TP_GET_TIME,
    CQC_CMD_I,
    CQC_CMD_X,
    CQC_CMD_Y,
    CQC_CMD_Z,
    CQC_CMD_T,
    CQC_CMD_H,
    CQC_CMD_K,
    CQC_CMD_NEW,
    CQC_CMD_MEASURE,
    CQC_CMD_MEASURE_INPLACE,
    CQC_CMD_RESET,
    CQC_CMD_RECV,
    CQC_CMD_EPR_RECV,
    CQC_CMD_ALLOCATE,
    CQC_CMD_RELEASE,
    CQCCommunicationHeader,
    CQCXtraQubitHeader,
    CQC_XTRA_QUBIT_HDR_LENGTH,
    CQCRotationHeader,
    CQCXtraHeader,
    CQC_CMD_XTRA_LENGTH,
    CQC_VERSION,
    CQCHeader,
    CQC_TP_DONE,
    CQC_ERR_UNSUPP,
    CQC_ERR_UNKNOWN,
    CQC_ERR_GENERAL,
    CQCSequenceHeader,
    CQCFactoryHeader,
    CQC_CMD_HDR_LENGTH,
    CQC_TP_INF_TIME,
    CQC_NOTIFY_LENGTH,
    CQC_ERR_NOQUBIT,
    CQCNotifyHeader,
    CQCMeasOutHeader,
    CQC_MEAS_OUT_HDR_LENGTH,
    CQCTimeinfoHeader,
    CQC_TIMEINFO_HDR_LENGTH,
    CQC_TP_MEASOUT,
    CQC_ERR_TIMEOUT,
    CQC_ERR_INUSE,
    CQC_TP_RECV,
    CQC_TP_EPR_OK,
    CQC_TP_NEW_OK,
)
from SimulaQron.cqc.backend.entInfoHeader import EntInfoHeader, ENT_INFO_LENGTH
from SimulaQron.virtNode.basics import quantumError, noQubitError
from twisted.internet.defer import DeferredLock, inlineCallbacks
from twisted.spread.pb import RemoteError

"""
Abstract class. Classes that inherit this class define how to handle incoming cqc messages.
"""


def has_extra(cmd):
    """
    Check whether this command includes an extra header with additional information.
    """
    if cmd.instr == CQC_CMD_SEND:
        return True
    if cmd.instr == CQC_CMD_EPR:
        return True
    if cmd.instr == CQC_CMD_CNOT:
        return True
    if cmd.instr == CQC_CMD_CPHASE:
        return True
    if cmd.instr == CQC_CMD_ROT_X:
        return True
    if cmd.instr == CQC_CMD_ROT_Y:
        return True
    if cmd.instr == CQC_CMD_ROT_Z:
        return True
    if cmd.action:
        return True

    return False


def print_error(error):
    logging.error("Uncaught twisted error found: {}".format(error))


class CQCMessageHandler(ABC):
    _sequence_lock = DeferredLock()

    def __init__(self, factory):
        # Functions to invoke when receiving a CQC Header of a certain type
        self.messageHandlers = {
            CQC_TP_HELLO: self.handle_hello,
            CQC_TP_COMMAND: self.handle_command,
            CQC_TP_FACTORY: self.handle_factory,
            CQC_TP_GET_TIME: self.handle_time,
        }

        # Functions to invoke when receiving a certain command
        self.commandHandlers = {
            CQC_CMD_I: self.cmd_i,
            CQC_CMD_X: self.cmd_x,
            CQC_CMD_Y: self.cmd_y,
            CQC_CMD_Z: self.cmd_z,
            CQC_CMD_T: self.cmd_t,
            CQC_CMD_H: self.cmd_h,
            CQC_CMD_K: self.cmd_k,
            CQC_CMD_ROT_X: self.cmd_rotx,
            CQC_CMD_ROT_Y: self.cmd_roty,
            CQC_CMD_ROT_Z: self.cmd_rotz,
            CQC_CMD_CNOT: self.cmd_cnot,
            CQC_CMD_CPHASE: self.cmd_cphase,
            CQC_CMD_MEASURE: self.cmd_measure,
            CQC_CMD_MEASURE_INPLACE: self.cmd_measure_inplace,
            CQC_CMD_RESET: self.cmd_reset,
            CQC_CMD_SEND: self.cmd_send,
            CQC_CMD_RECV: self.cmd_recv,
            CQC_CMD_EPR: self.cmd_epr,
            CQC_CMD_EPR_RECV: self.cmd_epr_recv,
            CQC_CMD_NEW: self.cmd_new,
            CQC_CMD_ALLOCATE: self.cmd_allocate,
            CQC_CMD_RELEASE: self.cmd_release,
        }

        # Convenience
        self.name = factory.name
        self.return_messages = []  # List of all cqc messages to return

    def get_error_class(self, remote_err):
        """
        This is a function to get the error class of a remote thrown error when using callRemote.
        :param remote_err: :obj:`twisted.spread.pb.RemoteError`
        :return: class
        """
        # Get name of remote error
        error_name = remote_err.remoteType.split(b".")[-1].decode()

        # Get class of remote error
        error_class = eval(error_name)

        return error_class

    @inlineCallbacks
    def handle_cqc_message(self, header, message, transport=None):
        """
        This calls the correct method to handle the cqcmessage, based on the type specified in the header
        """
        self.return_messages = []
        if header.tp in self.messageHandlers:
            try:
                should_notify = yield self.messageHandlers[header.tp](header, message)
                if should_notify:
                    # Send a notification that we are done if successful
                    logging.debug("CQC %s: Command successful, sent done.", self.name)
                    self.return_messages.append(
                        self.create_return_message(header.app_id, CQC_TP_DONE, cqc_version=header.version))
            except UnknownQubitError:
                logging.error("CQC {}: Couldn't find qubit with given ID".format(self.name))
                self.return_messages.append(
                    self.create_return_message(header.app_id, CQC_ERR_UNKNOWN, cqc_version=header.version))
            except NotImplementedError:
                logging.error("CQC {}: Command not implemented yet".format(self.name))
                self.return_messages.append(
                    self.create_return_message(header.app_id, CQC_ERR_UNSUPP, cqc_version=header.version))
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when handling CQC message: {}".format(self.name, err)
                )
                self.return_messages.append(
                    self.create_return_message(header.app_id, CQC_ERR_GENERAL, cqc_version=header.version))
        else:
            logging.error("CQC %s: Could not find cqc type %d in handlers.", self.name, header.yp)
            self.return_messages.append(
                self.create_return_message(header.app_id, CQC_ERR_UNSUPP, cqc_version=header.version))

    def retrieve_return_messages(self):
        return self.return_messages

    @staticmethod
    def create_return_message(app_id, msg_type, length=0, cqc_version=CQC_VERSION):
        """
        Creates a messaage that the protocol should send back
        :param app_id: the app_id to which the message should be send
        :param msg_type: the type of message to return
        :param length: the length of additional message
        :param cqc_version: The cqc version of the message
        :return: a new header message to be send back
        """
        hdr = CQCHeader()
        hdr.setVals(cqc_version, msg_type, app_id, length)
        return hdr.pack()

    @staticmethod
    def create_extra_header(cmd, cmd_data, cqc_version=CQC_VERSION):
        """
        Create the extra header (communication header, rotation header, etc) based on the command
        """
        if cqc_version < 1:
            if has_extra(cmd):
                cmd_length = CQC_CMD_XTRA_LENGTH
                hdr = CQCXtraHeader(cmd_data[:cmd_length])
                return hdr
            else:
                return None

        instruction = cmd.instr
        if instruction == CQC_CMD_SEND or instruction == CQC_CMD_EPR:
            cmd_length = CQCCommunicationHeader.HDR_LENGTH
            hdr = CQCCommunicationHeader(cmd_data[:cmd_length], cqc_version=cqc_version)
        elif instruction == CQC_CMD_CNOT or instruction == CQC_CMD_CPHASE:
            cmd_length = CQCXtraQubitHeader.HDR_LENGTH
            hdr = CQCXtraQubitHeader(cmd_data[:cmd_length])
        elif instruction == CQC_CMD_ROT_X or instruction == CQC_CMD_ROT_Y or instruction == CQC_CMD_ROT_Z:
            cmd_length = CQCRotationHeader.HDR_LENGTH
            hdr = CQCRotationHeader(cmd_data[:cmd_length])
        else:
            return None
        return hdr

    @inlineCallbacks
    def handle_command(self, header, data):
        """
        Handle incoming command requests.
        """
        logging.debug("CQC %s: Command received", self.name)
        # Run the entire command list, incl. actions after completion which here we will do instantly
        try:
            success, should_notify = yield self._process_command(header, header.length, data)
        except Exception as err:
            print_error(err)
            return False
        return success and should_notify

    @inlineCallbacks
    def _process_command(self, cqc_header, length, data, is_locked=False):
        """
            Process the commands - called recursively to also process additional command lists.
        """
        cmd_data = data
        # Read in all the commands sent
        cur_length = 0
        should_notify = None
        while cur_length < length:
            cmd = CQCCmdHeader(cmd_data[cur_length: cur_length + CQC_CMD_HDR_LENGTH])
            logging.debug("CQC %s got command header %s", self.name, cmd.printable())

            newl = cur_length + cmd.HDR_LENGTH
            # Should we notify
            should_notify = should_notify or cmd.notify

            # Create the extra header if it exist
            try:
                xtra = self.create_extra_header(cmd, cmd_data[newl:], cqc_header.version)
            except IndexError:
                xtra = None
                logging.debug("CQC %s: Missing XTRA Header", self.name)

            if xtra is not None:
                newl += xtra.HDR_LENGTH
                logging.debug("CQC %s: Read XTRA Header: %s", self.name, xtra.printable())

            # Run this command
            logging.debug("CQC %s: Executing command: %s", self.name, cmd.printable())
            if cmd.instr not in self.commandHandlers:
                logging.debug("CQC {}: Unknown command {}".format(self.name, cmd.instr))
                msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
                self.return_messages.append(msg)
                return False, 0
            try:
                succ = yield self.commandHandlers[cmd.instr](cqc_header, cmd, xtra)
            except NotImplementedError:
                logging.error("CQC {}: Command not implemented yet".format(self.name))
                self.return_messages.append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.verstion))
                return False, 0
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when process command {}: {}".format(
                        self.name, cmd.instr, err
                    )
                )
                msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
                self.return_messages.append(msg)
                return False, 0
            if succ is False:  # only if it explicitly is false, if succ is None then we assume it went fine
                return False, 0

            # Check if there are additional commands to execute afterwards
            if cmd.action:
                # lock the sequence
                if not is_locked:
                    self._sequence_lock.acquire()
                sequence_header = CQCSequenceHeader(data[newl: newl + CQCSequenceHeader.HDR_LENGTH])
                newl += sequence_header.HDR_LENGTH
                logging.debug("CQC %s: Reading extra action commands", self.name)
                try:
                    (succ, retNotify) = yield self._process_command(
                        cqc_header,
                        sequence_header.cmd_length,
                        data[newl: newl + sequence_header.cmd_length],
                        is_locked=True,
                    )
                except Exception as err:
                    logging.error(
                        "CQC {}: Got the following unexpected error when process commands: {}".format(self.name, err)
                    )
                    msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
                    self.return_messages.append(msg)
                    return False, 0

                should_notify = should_notify or retNotify
                if not succ:
                    return False, 0
                newl = newl + sequence_header.cmd_length
                if not is_locked:
                    logging.debug("CQC %s: Releasing lock", self.name)
                    # unlock
                    self._sequence_lock.release()

            cur_length = newl
        return True, should_notify

    @inlineCallbacks
    def handle_factory(self, header, data):
        fact_l = CQCFactoryHeader.HDR_LENGTH
        # Get factory header
        if len(data) < header.length:
            logging.debug("CQC %s: Missing header(s) in factory", self.name)
            self.return_messages.append(
                self.create_return_message(header.app_id, CQC_ERR_UNSUPP, cqc_version=header.version))
            return False
        fact_header = CQCFactoryHeader(data[:fact_l])
        num_iter = fact_header.num_iter
        # Perform operation multiple times
        succ = True
        should_notify = fact_header.notify
        block_factory = fact_header.block
        logging.debug("CQC %s: Performing factory command with %s iterations", self.name, num_iter)
        if block_factory:
            logging.debug("CQC %s: Acquire lock for factory", self.name)
            self._sequence_lock.acquire()

        for _ in range(num_iter):
            try:
                succ, _ = yield self._process_command(header, header.length - fact_l, data[fact_l:], block_factory)
                if succ is False:
                    return False
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when processing factory: {}".format(self.name, err)
                )
                self.return_messages.append(
                    self.create_return_message(header.app_id, CQC_ERR_GENERAL, cqc_version=header.version))
                return False

        if block_factory:
            logging.debug("CQC %s: Releasing lock for factory", self.name)
            self._sequence_lock.release()

        return succ and should_notify

    @abstractmethod
    def handle_hello(self, header, data):
        pass

    @abstractmethod
    def handle_time(self, header, data):
        pass

    @abstractmethod
    def cmd_i(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_x(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_y(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_z(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_t(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_h(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_k(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_rotx(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_roty(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_rotz(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_cnot(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_cphase(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_measure(self, cqc_header, cmd, xtra, inplace=False):
        pass

    @abstractmethod
    def cmd_measure_inplace(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_reset(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_send(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_recv(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_epr(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_epr_recv(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_new(self, cqc_header, cmd, xtra, return_q_id=False):
        pass

    @abstractmethod
    def cmd_allocate(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_release(self, cqc_header, cmd, xtra):
        pass


class SimulaqronCQCHandler(CQCMessageHandler):
    # Dictionary storing the next unique qubit id for each used app_id
    _available_q_ids = {}

    # Dictionary storing the next unique entanglement id for each used (host_app_id,remote_node,remote_app_id)
    _next_ent_id = {}

    def __init__(self, factory):
        super().__init__(factory)
        self.factory = factory

        # Dictionary that keeps qubit dictorionaries for each application
        # TODO this is in factory right?
        self.qubitList = {}

    def handle_hello(self, header, data):
        """
        Hello just requires us to return hello - for testing availability.
        """
        qubits = defaultdict(list)
        for appID, qID in self.factory.qubitList.keys():
            qubits[appID].append(qID)

        to_print = "Hello! I'm node {} with the following qubits:\n".format(self.name)
        for appID, qIDs in qubits.items():
            to_print += "    App ID {}: {}\n".format(appID, qIDs)
        logging.info(to_print[:-1])
        msg = self.create_return_message(header.app_id, CQC_TP_HELLO, cqc_version=header.version)
        self.return_messages.append(msg)

    def handle_time(self, header, data):

        # Read the command header to learn the qubit ID
        raw_cmd_header = data[:CQC_CMD_HDR_LENGTH]
        cmd_hdr = CQCCmdHeader(raw_cmd_header)

        # Get the qubit list
        q_list = self.factory.qubitList

        # Lookup the desired qubit
        if (header.app_id, cmd_hdr.qubit_id) in q_list:
            q = q_list[(header.app_id, cmd_hdr.qubit_id)]
        else:
            # Specified qubit is unknown
            self.return_messages.append(
                self.create_return_message(header.app_id, CQC_ERR_NOQUBIT, cqc_version=header.version))
            return False

        # Craft reply
        # First send an appropriate CQC Header
        if header.version < 2:
            length = CQC_NOTIFY_LENGTH
        else:
            length = CQC_TIMEINFO_HDR_LENGTH
        cqc_msg = self.create_return_message(header.app_id, CQC_TP_INF_TIME, length=length, cqc_version=header.version)
        self.return_messages.append(cqc_msg)

        # Then we send a notify header with the timing details
        if header.version < 2:
            hdr = CQCNotifyHeader()
            hdr.setVals(cmd_hdr.qubit_id, 0, 0, 0, 0, q.timestamp)
        else:
            hdr = CQCTimeinfoHeader()
            hdr.setVals(q.timestamp)
        msg = hdr.pack()
        self.return_messages.append(msg)

    def cmd_i(self, cqc_header, cmd, xtra):
        """
        Do nothing. In reality we would wait a timestep but in SimulaQron we just do nothing.
        """
        logging.debug("CQC %s: Doing Nothing to App ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)

    def cmd_x(self, cqc_header, cmd, xtra):
        """
        Apply X Gate
        """
        try:
            return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_X")
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a X gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_y(self, cqc_header, cmd, xtra):
        """
        Apply Y Gate
        """
        try:
            return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_Y")
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a Y gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_z(self, cqc_header, cmd, xtra):
        """
        Apply Z Gate
        """
        try:
            return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_Z")
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a Z gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_t(self, cqc_header, cmd, xtra):
        """
        Apply T Gate
        """
        try:
            return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_T")
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a T gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_h(self, cqc_header, cmd, xtra):
        """
        Apply H Gate
        """
        try:
            return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_H")
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a H gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_k(self, cqc_header, cmd, xtra):
        """
        Apply K Gate
        """
        try:
            return self.apply_single_qubit_gate(cqc_header, cmd.qubit_id, "apply_K")
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a K gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    @inlineCallbacks
    def apply_rotation(self, cqc_header, cmd, xtra, axis):
        """
        Apply a rotation of the qubit specified in cmd with an angle specified in xtra
        around the axis
        """
        logging.debug(
            "CQC %s: Applying a rotation around %s to App ID %d qubit id %d",
            self.name,
            axis,
            cqc_header.app_id,
            cmd.qubit_id,
        )
        try:
            virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
        except UnknownQubitError as e:
            logging.debug(e)
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version))
            return False
        try:
            success = yield virt_qubit.callRemote("apply_rotation", axis, 2 * np.pi / 256 * xtra.step)
            if success is False:
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
                return False
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a rotation gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

        return True

    def cmd_rotx(self, cqc_header, cmd, xtra):
        """
        Rotate around x axis
        """
        try:
            return self.apply_rotation(cqc_header, cmd, xtra, [1, 0, 0])
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a ROTX gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_roty(self, cqc_header, cmd, xtra):
        """
        Rotate around y axis
        """
        try:
            return self.apply_rotation(cqc_header, cmd, xtra, [0, 1, 0])
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a ROTY gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_rotz(self, cqc_header, cmd, xtra):
        """
        Rotate around z axis
        """
        try:
            return self.apply_rotation(cqc_header, cmd, xtra, [0, 0, 1])
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a ROTZ gate to qubit {}: Error: {}".format(
                    cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_cnot(self, cqc_header, cmd, xtra):
        """
        Apply CNOT Gate
        """
        try:
            return self.apply_two_qubit_gate(cqc_header, cmd, xtra, "cnot_onto")
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a CNOT gate to qubit {} and {}: Error: {}".format(
                    cmd.qubit_id, xtra.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    def cmd_cphase(self, cqc_header, cmd, xtra):
        """
        Apply CPHASE Gate
        """
        try:
            return self.apply_two_qubit_gate(cqc_header, cmd, xtra, "cphase_onto")
        except Exception as err:
            logging.error(
                "Following error occurred when trying to apply a CPHASE gate to qubit {} and {}: Error: {}".format(
                    cmd.qubit_id, xtra.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

    @inlineCallbacks
    def cmd_measure(self, cqc_header, cmd, xtra, inplace=False):
        """
        Measure
        """
        logging.debug("CQC %s: Measuring App ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
        try:
            virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
        except UnknownQubitError as e:
            logging.warning(e)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False
        try:
            outcome = yield virt_qubit.callRemote("measure", inplace)
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to measure qubit {}: {}".format(
                    self.name, cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

        if outcome is None:
            logging.warning("CQC %s: Measurement failed", self.name)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        logging.debug("CQC %s: Measured outcome %d", self.name, outcome)
        # Send the outcome back as MEASOUT
        if cqc_header.version < 2:
            length = CQC_NOTIFY_LENGTH
        else:
            length = CQC_MEAS_OUT_HDR_LENGTH
        cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_MEASOUT, length=length,
                                             cqc_version=cqc_header.version)
        self.return_messages.append(cqc_msg)

        # Send notify header with outcome
        if cqc_header.version < 2:
            hdr = CQCNotifyHeader()
            hdr.setVals(cmd.qubit_id, outcome, 0, 0, 0, 0)
        else:
            hdr = CQCMeasOutHeader()
            hdr.setVals(meas_out=outcome)
        msg = hdr.pack()
        self.return_messages.append(msg)
        # self.protocol.transport.write(msg)
        logging.debug("CQC %s: Notify %s", self.name, hdr.printable())

        if not inplace:
            # Remove from active mapped qubits
            self.remove_qubit_id(cqc_header.app_id, cmd.qubit_id)

        return True

    def cmd_measure_inplace(self, cqc_header, cmd, xtra):
        return self.cmd_measure(cqc_header, cmd, xtra, inplace=True)

    @inlineCallbacks
    def cmd_reset(self, cqc_header, cmd, xtra):
        """
        Reset Qubit to |0>
        """
        logging.debug("CQC %s: Reset App ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
        try:
            virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
        except UnknownQubitError as e:
            logging.debug(e)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        try:
            outcome = yield virt_qubit.callRemote("measure", inplace=True)
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to reset qubit {}: {}".format(
                    self.name, cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

        # If state is |1> do correction
        if outcome:
            try:
                yield virt_qubit.callRemote("apply_X")
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when trying to correct a the reset qubit {}: {}".format(
                        self.name, cmd.qubit_id, err
                    )
                )
                self.return_messages.append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
                return False
        return True

    @inlineCallbacks
    def cmd_send(self, cqc_header, cmd, xtra):
        """
        Send qubit to another node.
        """
        # Lookup the name of the remote node used within SimulaQron
        target_name = self.factory.lookup(xtra.remote_node, xtra.remote_port)
        if target_name is None:
            logging.debug("CQC %s: Remote node not found %s", self.name, xtra.printable())
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        # Check so that it is not the same node
        if self.name == target_name:
            logging.debug("CQC %s: Trying to send from node to itself.", self.name)
            # self.protocol._send_back_cqc(cqc_header, CQC_ERR_GENERAL)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        # Check that other node is adjacent to us
        if not self.factory.is_adjacent(target_name):
            logging.debug(
                "CQC {}: Node {} is not adjacent to {} in the specified topology.".format(
                    self.name, target_name, self.name
                )
            )
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        # Lookup the virtual qubit from identifier
        try:
            virt_num = yield self.get_virt_qubit_indep(cqc_header, cmd.qubit_id)
        except UnknownQubitError as e:
            logging.debug(e)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        # Send instruction to transfer the qubit
        try:
            yield self.factory.virtRoot.callRemote(
                "cqc_send_qubit", virt_num, target_name, cqc_header.app_id, xtra.remote_app_id
            )
        except RemoteError as remote_err:
            error_class = self.get_error_class(remote_err)
            if error_class == noQubitError:
                logging.error("CQC {}: Trying to send qubit but remote node is out of qubits".format(self.name))
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
                return False
            elif error_class == quantumError:
                logging.error("CQC {}: Unknown quantum error occurred when trying to send qubit.".format(self.name))
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
                return False
            else:
                logging.error(
                    "CQC {}: Got the following unexpected error when trying to send qubit {}: {}".format(
                        self.name, cmd.qubit_id, remote_err
                    )
                )
                self.return_messages.append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
                return False
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to send qubit {}: {}".format(
                    self.name, cmd.qubit_id, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

        logging.debug(
            "CQC %s: Sent App ID %d qubit id %d to %s", self.name, cqc_header.app_id, cmd.qubit_id, target_name
        )

        # Remove from active mapped qubits
        self.remove_qubit_id(cqc_header.app_id, cmd.qubit_id)
        return True

    @inlineCallbacks
    def cmd_recv(self, cqc_header, cmd, xtra):
        """
        Receive qubit from another node. Block until qubit is received.
        """
        logging.debug("CQC %s: Asking to receive for App ID %d", self.name, cqc_header.app_id)

        # First get the app_id
        app_id = cqc_header.app_id

        # This will block until a qubit is received.
        no_qubit = True
        virt_qubit = None
        # CQC_CONF_RECV_TIMEOUT is in 100ms (for legacy reasons there are no plans to change it to seconds)
        sleep_time = CQC_CONF_WAIT_TIME_RECV  # seconds
        for _ in range(int(CQC_CONF_RECV_TIMEOUT * 0.1 / sleep_time)):
            try:
                virt_qubit = yield self.factory.virtRoot.callRemote("cqc_get_recv", cqc_header.app_id)
            except RemoteError as remote_err:
                error_class = self.get_error_class(remote_err)
                if error_class == quantumError:
                    logging.error("CQC {}: Unknown quantum error occurred when trying to recv qubit.".format(self.name))
                    err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL,
                                                         cqc_version=cqc_header.version)
                    self.return_messages.append(err_msg)
                    return False
                else:
                    logging.error(
                        "CQC {}: Got the following unexpected error when trying to recv a qubit: {}".format(
                            self.name, remote_err
                        )
                    )
                    self.return_messages.append(
                        self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
                    return False
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when trying to recv a qubit: {}".format(self.name, err)
                )
                self.return_messages.append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
                return False

            if virt_qubit:
                no_qubit = False
                break
            else:
                time.sleep(sleep_time)
        if no_qubit:
            logging.debug("CQC %s: TIMEOUT, no qubit received.", self.name)
            # self.protocol._send_back_cqc(cqc_header, CQC_ERR_TIMEOUT)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_TIMEOUT, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        logging.debug("CQC %s: Qubit received for app_id %d", self.name, cqc_header.app_id)

        # Once we have the qubit, add it to the local list and send a reply we received it. Note that we will
        # recheck whether it exists: it could have been added by another connection in the mean time
        try:
            self.factory._lock.acquire()

            # Get new qubit ID
            q_id = self.new_qubit_id(app_id)

            if (app_id, q_id) in self.factory.qubitList:
                logging.debug("CQC %s: Qubit already in use (%d,%d)", self.name, app_id, q_id)
                # self.protocol._send_back_cqc(cqc_header, CQC_ERR_INUSE)
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_INUSE, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
                return

            q = CQCQubit(q_id, int(time.time()), virt_qubit)
            self.factory.qubitList[(app_id, q_id)] = q
        finally:
            self.factory._lock.release()

        # Send message we received a qubit back
        if cqc_header.version < 2:
            length = CQC_NOTIFY_LENGTH
        else:
            length = CQC_XTRA_QUBIT_HDR_LENGTH
        recv_msg = self.create_return_message(cqc_header.app_id, CQC_TP_RECV, length=length,
                                              cqc_version=cqc_header.version)
        self.return_messages.append(recv_msg)

        # Send notify header with qubit ID
        if cqc_header.version < 2:
            hdr = CQCNotifyHeader()
            hdr.setVals(q_id, 0, 0, 0, 0, 0)
        else:
            hdr = CQCXtraQubitHeader()
            hdr.setVals(qubit_id=q_id)
        msg = hdr.pack()
        # self.protocol.transport.write(msg)
        logging.debug("CQC %s: Notify %s", self.name, hdr.printable())
        self.return_messages.append(msg)
        return True

    @inlineCallbacks
    def cmd_epr(self, cqc_header, cmd, xtra):
        """
        Create EPR pair with another node.
        Depending on the ips and ports this will either create an EPR-pair and send one part, or just receive.
        """
        # Get ip and port of this host
        host_node = self.factory.host.ip
        host_port = self.factory.host.port
        host_app_id = cqc_header.app_id

        # Get ip and port of remote host
        remote_node = xtra.remote_node
        remote_port = xtra.remote_port
        remote_app_id = xtra.remote_app_id

        # Lookup the name of the remote node used within SimulaQron
        target_name = self.factory.lookup(remote_node, remote_port)
        if target_name is None:
            logging.debug("CQC %s: Remote node not found %s", self.name, xtra.printable())
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        # Check so that it is not the same node
        if self.name == target_name:
            logging.debug("CQC %s: Trying to create EPR from node to itself.", self.name)
            # self.protocol._send_back_cqc(cqc_header, CQC_ERR_GENERAL)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        # Check that other node is adjacent to us
        if not self.factory.is_adjacent(target_name):
            logging.debug(
                "CQC {}: Node {} is not adjacent to {} in the specified topology.".format(
                    self.name, target_name, self.name
                )
            )
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        # Create the first qubit
        try:
            (succ, q_id1) = yield self.cmd_new(cqc_header, cmd, xtra, return_q_id=True)
        except RemoteError as remote_err:
            error_class = self.get_error_class(remote_err)
            succ = False
            if error_class == noQubitError:
                logging.error("CQC {}: Trying to create qubit for EPR but out of qubits".format(self.name))
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
            elif error_class == quantumError:
                logging.error(
                    "CQC {}: Unknown quantum error occurred when trying to create qubit for EPR.".format(self.name)
                )
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
            else:
                logging.error(
                    "CQC {}: Got the following unexpected error when trying to create qubit for EPR: {}".format(
                        self.name, remote_err
                    )
                )
                self.return_messages.append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to create qubit for EPR: {}".format(
                    self.name, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

        if not succ:
            return False

        # Create the second qubit
        try:
            (succ, q_id2) = yield self.cmd_new(cqc_header, cmd, xtra, return_q_id=True, ignore_max_qubits=True)
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to create qubit for EPR: {}".format(
                    self.name, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

        if not succ:
            # Failed to create the second qubit, destroy the first
            logging.warning("CQC %s: Failed to create second qubit, destroying the first", self.name)
            try:
                cmd1 = CQCCmdHeader()
                cmd1.setVals(q_id1, 0, 0, 0, 0)
                yield self.cmd_release(cqc_header, cmd1, None)
            except Exception as err:
                logging.warning("CQC %s: Failed to destroy qubits", self.name)
                logging.error(err)
            return False

        # Create headers for qubits
        cmd1 = CQCCmdHeader()
        cmd1.setVals(q_id1, CQC_CMD_H, 0, 0, 0)

        cmd2 = CQCCmdHeader()
        cmd2.setVals(q_id2, 0, 0, 0, 0)

        xtra_cnot = CQCXtraQubitHeader()
        xtra_cnot.setVals(q_id2)

        # Produce EPR-pair
        try:
            yield self.cmd_h(cqc_header, cmd1, None)
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to apply H to EPR qubit: {}".format(
                    self.name, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            succ = False

        if not succ:
            # Failed to perform H, destroy qubits
            logging.warning("CQC %s: Failed to perform H, destroying qubits", self.name)
            try:
                yield self.cmd_release(cqc_header, cmd1, None)
            except Exception as err:
                logging.warning("CQC %s: Failed to destroy qubits", self.name)
                logging.error(err)
            try:
                yield self.cmd_release(cqc_header, cmd2, None)
            except Exception as err:
                logging.warning("CQC %s: Failed to destroy qubits", self.name)
                logging.error(err)
            return False

        try:
            yield self.cmd_cnot(cqc_header, cmd1, xtra_cnot)
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to apply CNOT to EPR qubit: {}".format(
                    self.name, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            succ = False

        if not succ:
            # Failed to perform CNOT, destroy qubits
            logging.warning("CQC %s: Failed to perform CNOT, destroying qubits", self.name)
            try:
                yield self.cmd_release(cqc_header, cmd1, None)
            except Exception as err:
                logging.warning("CQC %s: Failed to destroy qubits", self.name)
                logging.error(err)
            try:
                yield self.cmd_release(cqc_header, cmd2, None)
            except Exception as err:
                logging.warning("CQC %s: Failed to destroy qubits", self.name)
                logging.error(err)
            return False

        # Get entanglement id XXX lock here?
        ent_id = self.new_ent_id(host_app_id, remote_node, remote_app_id)

        # Prepare ent_info header with entanglement information
        ent_info = EntInfoHeader()
        ent_info.setVals(
            host_node,
            host_port,
            host_app_id,
            remote_node,
            remote_port,
            remote_app_id,
            ent_id,
            int(time.time()),
            int(time.time()),
            0,
            1,
        )
        # Send second qubit
        try:
            succ = yield self.send_epr_half(cqc_header, cmd2, xtra, ent_info)
        except RemoteError as remote_err:
            error_class = self.get_error_class(remote_err)
            succ = False
            if error_class == noQubitError:
                logging.error("CQC {}: Trying to send qubit of EPR but remote node is out of qubits".format(self.name))
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
            elif error_class == quantumError:
                logging.error(
                    "CQC {}: Unknown quantum error occurred when trying to send qubit of EPR.".format(self.name)
                )
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
            else:
                logging.error(
                    "CQC {}: Got the following unexpected error when trying to send EPR qubit: {}".format(
                        self.name, remote_err
                    )
                )
                self.return_messages.append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to send EPR qubit: {}".format(self.name, err)
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))

        if not succ:
            # Failed to send the qubit, destroy it instead
            logging.warning("CQC %s: Failed to send epr qubit, destroying qubits", self.name)
            try:
                yield self.cmd_release(cqc_header, cmd1, None)
            except Exception as err:
                logging.warning("CQC %s: Failed to destroy qubits", self.name)
                logging.error(err)
            try:
                yield self.cmd_release(cqc_header, cmd2, None)
            except Exception as err:
                logging.warning("CQC %s: Failed to destroy qubits", self.name)
                logging.error(err)
            return False

        # Send message we created EPR pair
        if cqc_header.version < 2:
            length = CQC_NOTIFY_LENGTH + ENT_INFO_LENGTH
        else:
            length = CQC_XTRA_QUBIT_HDR_LENGTH + ENT_INFO_LENGTH
        msg_ok = self.create_return_message(
            cqc_header.app_id, CQC_TP_EPR_OK, length=length, cqc_version=cqc_header.version
        )

        self.return_messages.append(msg_ok)

        # Send notify header with qubit ID
        if cqc_header.version < 2:
            hdr = CQCNotifyHeader()
            hdr.setVals(q_id1, 0, 0, 0, 0, 0)
        else:
            hdr = CQCXtraQubitHeader()
            hdr.setVals(qubit_id=q_id1)
        msg = hdr.pack()
        self.return_messages.append(msg)

        logging.debug("CQC %s: Notify %s", self.name, hdr.printable())

        # Send entanglement info
        msg_ent_info = ent_info.pack()
        self.return_messages.append(msg_ent_info)
        logging.debug("CQC %s: Entanglement information %s", self.name, ent_info.printable())

        logging.debug("CQC %s: EPR Pair ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
        return True

    @inlineCallbacks
    def send_epr_half(self, cqc_header, cmd, xtra, ent_info):
        """
        Send qubit to another node.
        """
        # Lookup the virtual qubit from identifier
        try:
            virt_num = yield self.get_virt_qubit_indep(cqc_header, cmd.qubit_id)
        except UnknownQubitError as e:
            logging.debug(e)
            return False
        except Exception as e:
            raise e

        # Lookup the name of the remote node used within SimulaQron
        target_name = self.factory.lookup(xtra.remote_node, xtra.remote_port)
        if target_name is None:
            logging.debug("CQC %s: Remote node not found %s", self.name, xtra.printable())
            return False

        # Prepare update raw entanglement information header
        updated_ent_info = EntInfoHeader(ent_info.pack())
        updated_ent_info.switch_nodes()
        raw_updated_ent_info = updated_ent_info.pack()
        # Send instruction to transfer the qubit
        try:
            yield self.factory.virtRoot.callRemote(
                "cqc_send_epr_half", virt_num, target_name, cqc_header.app_id, xtra.remote_app_id, raw_updated_ent_info
            )
        except Exception as e:
            raise e

        logging.debug(
            "CQC %s: Sent App ID %d half a EPR pair as qubit id %d to %s",
            self.name,
            cqc_header.app_id,
            cmd.qubit_id,
            target_name,
        )
        # Remove from active mapped qubits
        self.remove_qubit_id(cqc_header.app_id, cmd.qubit_id)

        return True

    @inlineCallbacks
    def cmd_epr_recv(self, cqc_header, cmd, xtra):
        """
        Receive half of epr from another node. Block until qubit is received.
        """
        logging.debug("CQC %s: Asking to receive for App ID %d", self.name, cqc_header.app_id)

        # First get the app_id and q_id
        app_id = cqc_header.app_id
        q_id = self.new_qubit_id(app_id)

        # This will block until a qubit is received.
        no_qubit = True
        virt_qubit = None
        ent_info = None
        # CQC_CONF_RECV_EPR_TIMEOUT is in 100ms (for legacy reasons there are no plans to change it to seconds)
        sleep_time = CQC_CONF_WAIT_TIME_RECV
        for _ in range(int(CQC_CONF_RECV_EPR_TIMEOUT * 0.1 / sleep_time)):
            try:
                data = yield self.factory.virtRoot.callRemote("cqc_get_epr_recv", cqc_header.app_id)
            except RemoteError as remote_err:
                error_class = self.get_error_class(remote_err)
                if error_class == quantumError:
                    logging.error(
                        "CQC {}: Unknown quantum error occurred when trying to recv qubit of EPR.".format(self.name)
                    )
                    err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL,
                                                         cqc_version=cqc_header.version)
                    self.return_messages.append(err_msg)
                    return False
                else:
                    logging.error(
                        "CQC {}: Got the following unexpected error when trying to recv EPR qubit: {}".format(
                            self.name, remote_err
                        )
                    )
                    self.return_messages.append(
                        self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
                    return False
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when trying to send EPR qubit: {}".format(
                        self.name, err
                    )
                )
                self.return_messages.append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
                return False

            if data:
                no_qubit = False
                (virt_qubit, rawEntInfo) = data
                ent_info = EntInfoHeader(rawEntInfo)
                break
            else:
                time.sleep(sleep_time)
        if no_qubit:
            logging.debug("CQC %s: TIMEOUT, no qubit received.", self.name)
            # self.protocol._send_back_cqc(cqc_header, CQC_ERR_TIMEOUT)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_TIMEOUT, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        logging.debug("CQC %s: Qubit received for app_id %d", self.name, cqc_header.app_id)

        # Once we have the qubit, add it to the local list and send a reply we received it. Note that we will
        # recheck whether it exists: it could have been added by another connection in the mean time
        try:
            self.factory._lock.acquire()

            if (app_id, q_id) in self.factory.qubitList:
                logging.debug("CQC %s: Qubit already in use (%d,%d)", self.name, app_id, q_id)
                # self.protocol._send_back_cqc(cqc_header, CQC_ERR_INUSE)
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_INUSE, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
                return False

            q = CQCQubit(q_id, int(time.time()), virt_qubit)
            self.factory.qubitList[(app_id, q_id)] = q
        finally:
            self.factory._lock.release()

        # Send message we received a qubit back
        if cqc_header.version < 2:
            length = CQC_NOTIFY_LENGTH + ENT_INFO_LENGTH
        else:
            length = CQC_XTRA_QUBIT_HDR_LENGTH + ENT_INFO_LENGTH
        cqc_msg = self.create_return_message(
            cqc_header.app_id, CQC_TP_EPR_OK, length=length, cqc_version=cqc_header.version
        )
        self.return_messages.append(cqc_msg)

        # Send notify header with qubit ID
        if cqc_header.version < 2:
            hdr = CQCNotifyHeader()
            hdr.setVals(q_id, 0, 0, 0, 0, 0)
            logging.debug("CQC %s: Notify %s", self.name, hdr.printable())
        else:
            hdr = CQCXtraQubitHeader()
            hdr.setVals(qubit_id=q_id)
            logging.debug("CQC %s: %s", self.name, hdr.printable())
        msg = hdr.pack()
        self.return_messages.append(msg)

        # Send entanglement info
        ent_info_msg = ent_info.pack()
        self.return_messages.append(ent_info_msg)
        logging.debug("CQC %s: Entanglement information %s", self.name, ent_info.printable())

        logging.debug("CQC %s: EPR Pair ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
        return True

    @inlineCallbacks
    def cmd_new(self, cqc_header, cmd, xtra, return_q_id=False, ignore_max_qubits=False):
        """
        Request a new qubit. Since we don't need it, this python CQC just provides very crude timing information.
        (return_q_id is used internally)
        (ignore_max_qubits is used internally to ignore the check of number of virtual qubits at the node
        such that the node can temporarily create a qubit for EPR creation.)
        """

        app_id = cqc_header.app_id
        try:
            self.factory._lock.acquire()
            try:
                virt = yield self.factory.virtRoot.callRemote("new_qubit", ignore_max_qubits=ignore_max_qubits)
                succ = True
            except RemoteError as remote_err:
                error_class = self.get_error_class(remote_err)
                succ = False
                if error_class == noQubitError:
                    logging.error(
                        "CQC {}: Out of simulated qubits in register or virtual qubits in node".format(self.name)
                    )
                    err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT,
                                                         cqc_version=cqc_header.version)
                    self.return_messages.append(err_msg)
                elif error_class == quantumError:
                    logging.error(
                        "CQC {}: Unknown quantum error occurred when trying to create new qubit.".format(self.name)
                    )
                    err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL,
                                                         cqc_version=cqc_header.version)
                    self.return_messages.append(err_msg)
                else:
                    logging.error(
                        "CQC {}: Got the following unexpected error when trying to create new qubit: {}".format(
                            self.name, remote_err
                        )
                    )
                    self.return_messages.append(
                        self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            except Exception as err:
                succ = False
                logging.error(
                    "CQC {}: Got the following unexpected error when trying to create new qubit: {}".format(
                        self.name, err
                    )
                )
                self.return_messages.append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))

            if succ:
                q_id = self.new_qubit_id(app_id)
                q = CQCQubit(q_id, int(time.time()), virt)
                self.factory.qubitList[(app_id, q_id)] = q
                logging.debug("CQC %s: Requested new qubit (%d,%d)", self.name, app_id, q_id)

                if not return_q_id:
                    # Send message we created a qubit back
                    if cqc_header.version < 2:
                        length = CQC_NOTIFY_LENGTH
                    else:
                        length = CQC_XTRA_QUBIT_HDR_LENGTH
                    cqc_msg = self.create_return_message(cqc_header.app_id, CQC_TP_NEW_OK, length=length,
                                                         cqc_version=cqc_header.version)
                    self.return_messages.append(cqc_msg)

                    # Send notify header with qubit ID
                    if cqc_header.version < 2:
                        hdr = CQCNotifyHeader()
                        hdr.setVals(q_id, 0, 0, 0, 0, 0)
                        logging.debug("CQC %s: Notify %s", self.name, hdr.printable())
                    else:
                        hdr = CQCXtraQubitHeader()
                        hdr.setVals(qubit_id=q_id)
                        logging.debug("CQC %s: %s", self.name, hdr.printable())
                    msg = hdr.pack()
                    self.return_messages.append(msg)
        finally:
            self.factory._lock.release()
        if return_q_id:
            if succ:
                return succ, q_id
            else:
                return succ, None
        else:
            return succ

    @inlineCallbacks
    def cmd_allocate(self, cqc_header, cmd, xtra):
        """
        Allocate multiple qubits.
        """
        num_qubits = cmd.qubit_id
        cmd.qubit_id = 0
        logging.debug("CQC %s: Allocating %d qubits", self.name, num_qubits)
        succ = True
        try:
            for _ in range(num_qubits):
                succ_tmp = yield self.cmd_new(cqc_header, cmd, xtra)
                succ = succ and succ_tmp
        except Exception as err:
            logging.error(
                "CQC {}: Got the following unexpected error when trying to create allocate qubits: {}".format(
                    self.name, err
                )
            )
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False
        return succ

    @inlineCallbacks
    def cmd_release(self, cqc_header, cmd, xtra):
        """
        Release
        """
        logging.debug("CQC %s: Releasing App ID %d qubit id %d", self.name, cqc_header.app_id, cmd.qubit_id)
        try:
            virt_qubit = self.get_virt_qubit(cqc_header, cmd.qubit_id)
        except UnknownQubitError as err:
            logging.debug(err)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False
        except Exception as err:
            logging.debug(err)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        try:
            outcome = yield virt_qubit.callRemote("measure", False)
        except Exception as err:
            logging.error("Following unknown error occurred when trying to release qubit by measuring: {}".format(err))
            self.return_messages.append(
                self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version))
            return False

        if outcome is None:
            logging.debug("CQC %s: Release failed", self.name)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        self.remove_qubit_id(cqc_header.app_id, cmd.qubit_id)
        return True

    @inlineCallbacks
    def apply_single_qubit_gate(self, cqc_header, qubit_id, gate):
        logging.debug("CQC %s: %s on App ID %d to qubit id %d", self.name, gate, cqc_header.app_id, qubit_id)
        try:
            virt_qubit = self.get_virt_qubit(cqc_header, qubit_id)
        except UnknownQubitError as error:
            logging.debug(error)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False
        try:
            success = yield virt_qubit.callRemote(gate)
            if success is False:
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
                return False
        except Exception as e:
            raise e

        return True

    @inlineCallbacks
    def apply_two_qubit_gate(self, cqc_header, cmd, xtra, gate):
        if not xtra:
            logging.debug("CQC %s: Missing XTRA Header", self.name)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False
        #
        logging.debug(
            "CQC %s: Applying %s to App ID %d qubit id %d target %d",
            self.name,
            gate,
            cqc_header.app_id,
            cmd.qubit_id,
            xtra.qubit_id,
        )
        try:
            control = self.get_virt_qubit(cqc_header, cmd.qubit_id)
            target = self.get_virt_qubit(cqc_header, xtra.qubit_id)
        except UnknownQubitError as e:
            logging.debug(e)
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_NOQUBIT, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False
        # Return an error if the control and target are equal, can not do this
        if control == target:
            err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
            self.return_messages.append(err_msg)
            return False

        try:
            success = yield control.callRemote(gate, target)
            if success is False:
                err_msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
                self.return_messages.append(err_msg)
                return False
        except Exception as e:
            raise e

        return True

    def get_virt_qubit(self, header, qubit_id):
        """
        Get reference to the virtual qubit reference in SimulaQron given app and qubit id, if it exists.
        If not found, send back no qubit error.

        Caution: Twisted PB does not allow references to objects to be passed back between connections.
        If you need to pass a qubit reference back to the Twisted PB on a _different_ connection,
        then use get_virt_qubit_indep below.
        """
        if not (header.app_id, qubit_id) in self.factory.qubitList:
            raise UnknownQubitError("CQC {}: Qubit not found".format(self.name))
        qubit = self.factory.qubitList[(header.app_id, qubit_id)]
        return qubit.virt

    @inlineCallbacks
    def get_virt_qubit_indep(self, header, qubit_id):
        """
        Get NUMBER (not reference!) to virtual qubit in SimulaQron specific to this connection.
        If not found, send back no qubit error.
        """
        # First let's get the general virtual qubit reference, if any
        general_ref = self.get_virt_qubit(header, qubit_id)

        try:
            num = yield general_ref.callRemote("get_virt_num")
        except Exception as e:
            raise e

        return num

    @staticmethod
    def new_qubit_id(app_id):
        """
        Returns a new unique qubit id for the specified app_id. Used by cmd_new and cmd_recv
        """
        if app_id in SimulaqronCQCHandler._available_q_ids:
            q_ids = SimulaqronCQCHandler._available_q_ids[app_id]
            q_id = heappop(q_ids)
            if not q_ids:
                heappush(q_ids, q_id + 1)
            return q_id
        else:
            SimulaqronCQCHandler._available_q_ids[app_id] = []
            heappush(SimulaqronCQCHandler._available_q_ids[app_id], 2)

            return 1

    def remove_qubit_id(self, app_id, qubit_id):
        """
        Remove qubit id from current used qubit_id so it can be reused
        :param app_id: The app id of the current qubit_id
        :param qubit_id: The qubit id to be removed
        """
        if app_id in SimulaqronCQCHandler._available_q_ids:
            q_ids = SimulaqronCQCHandler._available_q_ids[app_id]
            heappush(q_ids, qubit_id)
        del self.factory.qubitList[(app_id, qubit_id)]

    @staticmethod
    def new_ent_id(host_app_id, remote_node, remote_app_id):
        """
        Returns a new unique entanglement id for the specified host_app_id, remote_node and remote_app_id.
        Used by cmd_epr.
        """
        pair_id = (host_app_id, remote_node, remote_app_id)
        if pair_id in SimulaqronCQCHandler._next_ent_id:
            ent_id = SimulaqronCQCHandler._next_ent_id[pair_id]
            SimulaqronCQCHandler._next_ent_id[pair_id] += 1
            return ent_id
        else:
            SimulaqronCQCHandler._next_ent_id[pair_id] = 1
            return 0


class UnknownQubitError(Exception):
    def __init__(self, message):
        super().__init__(message)


#######################################################################################################
#
# CQC Internal qubit object to translate to the native mode of SimulaQron
#


class CQCQubit:
    def __init__(self, qubit_id=0, timestamp=0, virt=0):
        self.qubit_id = qubit_id
        self.timestamp = timestamp
        self.virt = virt

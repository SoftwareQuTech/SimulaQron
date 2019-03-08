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

import math
import os
import sys
import time
import logging
import socket
import warnings

from cqc.backend.cqcConfig import CQC_CONF_LINK_WAIT_TIME, CQC_CONF_COM_WAIT_TIME
from cqc.backend.cqcHeader import (
    Header,
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
    CQCRotationHeader,
    CQC_VERSION,
    CQC_HDR_LENGTH,
    CQCHeader,
    CQC_TP_DONE,
    CQC_ERR_UNSUPP,
    CQC_ERR_UNKNOWN,
    CQC_ERR_GENERAL,
    CQCSequenceHeader,
    CQCFactoryHeader,
    CQC_CMD_HDR_LENGTH,
    CQC_TP_INF_TIME,
    CQC_ERR_NOQUBIT,
    CQCMeasOutHeader,
    CQCTimeinfoHeader,
    CQC_TP_MEASOUT,
    CQC_ERR_TIMEOUT,
    CQC_TP_RECV,
    CQC_TP_EPR_OK,
    CQC_TP_NEW_OK,
    CQC_TP_EXPIRE,
)
from cqc.backend.entInfoHeader import EntInfoHeader
from simulaqron.general.hostConfig import cqc_node_id_from_addrinfo, networkConfig
from simulaqron.settings import Settings
from simulaqron.toolbox import get_simulaqron_path

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s", level=Settings.CONF_LOGGING_LEVEL_FRONTEND)


def shouldReturn(command):
    return command in {
        CQC_CMD_NEW,
        CQC_CMD_MEASURE,
        CQC_CMD_MEASURE_INPLACE,
        CQC_CMD_RECV,
        CQC_CMD_EPR_RECV,
        CQC_CMD_EPR,
    }


def hasXtraHeader(command):
    return command in {
        CQC_CMD_CNOT,
        CQC_CMD_SEND,
        CQC_CMD_EPR,
        CQC_CMD_ROT_X,
        CQC_CMD_ROT_Y,
        CQC_CMD_ROT_Z,
        CQC_CMD_CPHASE,
    }


def get_remote_from_directory_or_address(cqcNet, name, remote_socket):
    if remote_socket is None:
        try:
            # Get receiving host
            hostDict = cqcNet.hostDict
        except AttributeError:
            raise ValueError(
                "If a CQCConnections is initialized without specifying a cqcFile you need to also provide a"
                "socket address for the remote node here."
            )
        if name in hostDict:
            recvHost = hostDict[name]
            remote_ip = recvHost.ip
            remote_port = recvHost.port
        else:
            raise ValueError("Host name '{}' is not in the cqc network".format(name))
    else:
        try:
            remote_host, remote_port = remote_socket
            if not isinstance(remote_host, str):
                raise TypeError()
            if not isinstance(remote_port, int):
                raise TypeError()
        except Exception:
            raise TypeError("When specifying the remote socket address, this should be a tuple (str,int).")

            # Pack the IP
        addrs = socket.getaddrinfo(remote_host, remote_port, proto=socket.IPPROTO_TCP, family=socket.AF_INET)
        addr = addrs[0]
        remote_ip = cqc_node_id_from_addrinfo(addr)
        remote_port = addr[4][1]
    return remote_ip, remote_port


def createXtraHeader(command, values):
    if command == CQC_CMD_SEND or command == CQC_CMD_EPR:
        header = CQCCommunicationHeader()
        header.setVals(remote_app_id=values[0], remote_node=values[1], remote_port=values[2])
    elif command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
        header = CQCXtraQubitHeader()
        xtra_qubit_id = values._qID
        if xtra_qubit_id is None:
            raise QubitNotActiveError("Qubit in extra header is not active")
        header.setVals(xtra_qubit_id)
    elif command == CQC_CMD_ROT_Z or command == CQC_CMD_ROT_Y or command == CQC_CMD_ROT_X:
        header = CQCRotationHeader()
        header.setVals(values)
    else:
        header = None
    return header


class CQCConnection:
    _appIDs = {}

    def __init__(self, name, socket_address=None, cqcFile=None, appFile=None, appID=None, pend_messages=False,
                 retry_connection=True):
        """
        Initialize a connection to the cqc server.

        - **Arguments**
            :param name:        Name of the host.
            :param socket_address: tuple (str, int) of ip and port number.
            :param cqcFile:    Path to cqcFile. If None, 'Setting.CONF_CQC_FILE' is used, unless socket_address
            :param appFile:    Path to appFile. If None, 'Setting.CONF_APP_FILE' is used.
            :param appID:        Application ID. If set to None, defaults to a nonused ID.
            :param pend_messages: True if you want to wait with sending messages to the back end.
                    Use flush() to send all pending messages in one go as a sequence to the server
        """

        # This flag is used to check if CQCConnection is opened using a 'with' statement.
        # Otherwise an deprecation warning is printed when instantiating qubits.
        self._opened_with_with = False

        # Host name
        self.name = name

        if name not in self._appIDs:
            self._appIDs[name] = []

            # Which appID
        if appID is None:
            if len(self._appIDs[name]) == 0:
                self._appID = 0
            else:
                for i in range(min(self._appIDs[name]) + 1, max(self._appIDs[name])):
                    if i not in self._appIDs[name]:
                        self._appID = i
                        break
                else:
                    self._appID = max(self._appIDs[name]) + 1
            self._appIDs[name].append(self._appID)
        else:
            if appID in self._appIDs:
                raise ValueError("appID={} is already in use".format(appID))
            self._appID = appID
            self._appIDs[name].append(self._appID)

            # Buffer received data
        self.buf = None

        # ClassicalServer
        self._classicalServer = None

        # Classical connections in the application network
        self._classicalConn = {}

        # Get path to SimulaQron folder
        simulaqron_path = get_simulaqron_path.main()

        if socket_address is None:
            # This file defines the network of CQC servers interfacing to virtual quantum nodes
            if cqcFile is None:
                self.cqcFile = Settings.CONF_CQC_FILE
            else:
                self.cqcFile = cqcFile

                # Read configuration files for the cqc network
            self._cqcNet = networkConfig(self.cqcFile)

            # Host data
            if self.name in self._cqcNet.hostDict:
                myHost = self._cqcNet.hostDict[self.name]
            else:
                raise ValueError("Host name '{}' is not in the cqc network".format(name))

                # Get IP and port number
            addr = myHost.addr
        else:
            try:
                hostname, port = socket_address
                if not isinstance(hostname, str):
                    raise TypeError()
                if not isinstance(port, int):
                    raise TypeError()
                addrs = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP, family=socket.AF_INET)
                addr = addrs[0]

            except Exception:
                raise TypeError("When specifying the socket address, this should be a tuple (str,int).")

        self._s = None
        while True:
            try:
                logging.debug("App {} : Trying to connect to CQC server".format(self.name))

                self._s = socket.socket(addr[0], addr[1], addr[2])
                self._s.connect(addr[4])
                break
            except ConnectionRefusedError as err:
                logging.debug("App {} : Could not connect to  CQC server, trying again...".format(self.name))
                time.sleep(CQC_CONF_LINK_WAIT_TIME)
                self._s.close()
                if not retry_connection:
                    raise err
            except Exception as err:
                logging.warning("App {} : Critical error when connection to CQC server: {}".format(self.name, e))
                self._s.close()
                raise err

                # This file defines the application network
        if appFile is None:
            self.appFile = Settings.CONF_APP_FILE

            # Read configuration files for the application network
        if os.path.exists(self.appFile):
            self._appNet = networkConfig(self.appFile)
        else:
            logging.warning("Since there is no appFile was found the built-in classical commmunication cannot be used.")
            self._appNet = None

            # List of pending messages waiting to be send to the back-end
        self.pend_messages = pend_messages
        self.pending_messages = []

        # All qubits active for this connection
        self.active_qubits = []

    def __enter__(self):
        # This flag is used to check if CQCConnection is opened using a 'with' statement.
        # Otherwise an deprecation warning is printed when instantiating qubits.
        self._opened_with_with = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # All qubits should now be released
        self.close(release_qubits=True)

    def __str__(self):
        return "Socket to cqc server '{}'".format(self.name)

    def get_appID(self):
        """
        Returns the application ID.
        """
        return self._appID

    def close(self, release_qubits=True):
        """
        Closes the connection. Releases all qubits
        """
        if release_qubits:
            self.release_all_qubits()
        self._s.close()
        try:
            self._appIDs[self.name].remove(self._appID)
        except ValueError:
            pass  # Already closed

        self.closeClassicalServer()

        for name in list(self._classicalConn):
            self.closeClassicalChannel(name)

    def startClassicalServer(self):
        """
        Sets up a server for the application communication, if not already set up.
        """
        if self._appNet is None:
            raise ValueError(
                "Since there is no appFile was found the built-in classical commmunication cannot be used."
            )

        if not self._classicalServer:
            logging.debug("App {}: Starting classical server".format(self.name))
            # Get host data
            myHost = self._appNet.hostDict[self.name]
            hostaddr = myHost.addr

            # Setup server
            s = socket.socket(hostaddr[0], hostaddr[1], hostaddr[2])
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(hostaddr[4])
            s.listen(1)
            (conn, addr) = s.accept()
            logging.debug("App {}: Classical server started".format(self.name))
            self._classicalServer = conn

    def closeClassicalServer(self):
        if self._classicalServer:
            logging.debug("App {}: Closing classical server".format(self.name))
            self._classicalServer.close()
            logging.debug("App {}: Classical server closed".format(self.name))
            self._classicalServer = None

    def recvClassical(self, timout=1, msg_size=1024, close_after=True):
        if not self._classicalServer:
            self.startClassicalServer()
        for _ in range(10 * timout):
            logging.debug("App {}: Trying to receive classical message".format(self.name))
            msg = self._classicalServer.recv(msg_size)
            if len(msg) > 0:
                logging.debug("App {}: Received classical message".format(self.name))
                if close_after:
                    self.closeClassicalServer()
                return msg
            time.sleep(0.1)
        raise RuntimeError("Timeout: No message received")

    def openClassicalChannel(self, name):
        """
        Opens a classical connection to another host in the application network.

        - **Arguments**

            :name:        The name of the host in the application network.
            :timout:    The time to try to connect to the server. When timout is reached an RuntimeError is raised.
        """
        if self._appNet is None:
            raise ValueError(
                "Since there is no appFile was found the built-in classical commmunication cannot be used."
            )
        if name not in self._classicalConn:
            logging.debug("App {}: Opening classical channel to {}".format(self.name, name))
            if name in self._appNet.hostDict:
                remoteHost = self._appNet.hostDict[name]
            else:
                raise ValueError("Host name '{}' is not in the cqc network".format(name))

            addr = remoteHost.addr
            while True:
                try:
                    s = socket.socket(addr[0], addr[1], addr[2])
                    s.connect(addr[4])
                    logging.debug("App {}: Classical channel to {} opened".format(self.name, name))
                    break
                except ConnectionRefusedError:
                    logging.debug(
                        "App {}: Could not open classical channel to {}, trying again..".format(self.name, name)
                    )
                    time.sleep(CQC_CONF_COM_WAIT_TIME)
                except Exception as e:
                    logging.warning(
                        "App {} : Critical error when connection to app node {}: {}".format(self.name, name, e)
                    )
                    break
            self._classicalConn[name] = s

    def closeClassicalChannel(self, name):
        """
        Closes a classical connection to another host in the application network.

        - **Arguments**

            :name:        The name of the host in the application network.
        """
        if name in self._classicalConn:
            logging.debug("App {}: Closing classical channel to {}".format(self.name, name))
            s = self._classicalConn.pop(name)
            s.close()
            logging.debug("App {}: Classical channel to {} closed".format(self.name, name))

    def sendClassical(self, name, msg, close_after=True):
        """
        Sends a classical message to another host in the application network.

        - **Arguments**

            :name:        The name of the host in the application network.
            :msg:        The message to send. Should be either a int in range(0,256) or a list of such ints.
            :timout:    The time to try to connect to the server. When timout is reached an RuntimeError is raised.
        """
        if name not in self._classicalConn:
            self.openClassicalChannel(name)
        try:
            to_send = bytes([int(msg)])
        except (TypeError, ValueError):
            to_send = bytes(msg)
        logging.debug("App {}: Sending classical message {} to {}".format(self.name, to_send, name))
        self._classicalConn[name].send(to_send)
        logging.debug("App {}: Classical message {} to {} sent".format(self.name, to_send, name))
        if close_after:
            self.closeClassicalChannel(name)

    def sendSimple(self, tp):
        """
        Sends a simple message to the cqc server, for example a HELLO message if tp=CQC_TP_HELLO.
        """
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, tp, self._appID, 0)
        msg = hdr.pack()
        self._s.send(msg)

    def sendCommand(self, qID, command, notify=1, block=1, action=0):
        """
        Sends a simple message and command message to the cqc server.

        - **Arguments**

            :qID:        qubit ID
            :command:    Command to be executed, eg CQC_CMD_H
            :nofify:    Do we wish to be notified when done.
            :block:        Do we want the qubit to be blocked
            :action:    Are there more commands to be executed
        """
        # Send Header
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, CQC_TP_COMMAND, self._appID, CQC_CMD_HDR_LENGTH)
        msg = hdr.pack()
        self._s.send(msg)

        # Send Command
        cmd_hdr = CQCCmdHeader()
        cmd_hdr.setVals(qID, command, notify, block, action)
        cmd_msg = cmd_hdr.pack()
        self._s.send(cmd_msg)

    def sendCmdXtra(
        self,
        qID,
        command,
        notify=1,
        block=1,
        action=0,
        xtra_qID=0,
        step=0,
        remote_appID=0,
        remote_node=0,
        remote_port=0,
    ):
        """
        Sends a simple message, command message and xtra message to the cqc server.

        - **Arguments**

            :qID:         qubit ID
            :command:     Command to be executed, eg CQC_CMD_H
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
            :action:     Are there more commands to be executed
            :xtra_qID:     Extra qubit ID for for example CNOT
            :step:         Defines the angle of rotation.
            :remote_appID:     Application ID of remote host
            :remote_node:     ip of remote host in cqc network
            :remote_port:     port of remote host in cqc network
        """

        # Check what extra header we require
        xtra_hdr = None
        if command == CQC_CMD_SEND or command == CQC_CMD_EPR:
            xtra_hdr = CQCCommunicationHeader()
            xtra_hdr.setVals(remote_appID, remote_node, remote_port)
        elif command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
            xtra_hdr = CQCXtraQubitHeader()
            xtra_hdr.setVals(xtra_qID)
        elif command == CQC_CMD_ROT_X or command == CQC_CMD_ROT_Y or command == CQC_CMD_ROT_Z:
            xtra_hdr = CQCRotationHeader()
            xtra_hdr.setVals(step)

        if xtra_hdr is None:
            header_length = CQC_CMD_HDR_LENGTH
            xtra_msg = b""
        else:
            xtra_msg = xtra_hdr.pack()
            header_length = CQC_CMD_HDR_LENGTH + xtra_hdr.HDR_LENGTH

            # Send Header
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, CQC_TP_COMMAND, self._appID, header_length)
        msg = hdr.pack()

        # Send Command
        cmd_hdr = CQCCmdHeader()
        cmd_hdr.setVals(qID, command, notify, block, action)
        cmd_msg = cmd_hdr.pack()

        # Send headers
        self._s.send(msg + cmd_msg + xtra_msg)

    def sendGetTime(self, qID, notify=1, block=1, action=0):
        """
        Sends get-time message

        - **Arguments**

            :qID:         qubit ID
            :command:     Command to be executed, eg CQC_CMD_H
            :notify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
            :action:     Are there more commands to be executed
        """
        # Send Header
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, CQC_TP_GET_TIME, self._appID, CQC_CMD_HDR_LENGTH)
        msg = hdr.pack()
        self._s.send(msg)

        # Send Command
        cmd_hdr = CQCCmdHeader()
        cmd_hdr.setVals(qID, 0, notify, block, action)
        cmd_msg = cmd_hdr.pack()
        self._s.send(cmd_msg)

    def allocate_qubits(self, num_qubits, notify=True, block=True):
        """
        Requests the backend to reserve some qubits
        :param num_qubits: The amount of qubits to reserve
        :return: A list of qubits
        :param notify:     Do we wish to be notified when done.
        :param block:         Do we want the qubit to be blocked
        """

        # CQC header
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, CQC_TP_COMMAND, self._appID, CQC_CMD_HDR_LENGTH)
        cqc_msg = hdr.pack()

        # Command header
        cmd_hdr = CQCCmdHeader()
        cmd_hdr.setVals(num_qubits, CQC_CMD_ALLOCATE, int(notify), int(block), 0)
        cmd_msg = cmd_hdr.pack()

        self._s.send(cqc_msg + cmd_msg)
        qubits = []
        for _ in range(num_qubits):
            msg = self.readMessage()
            self.check_error(msg[0])
            if msg[0].tp != CQC_TP_NEW_OK:
                print(len(msg))
                raise CQCUnsuppError("Unexpected message of type {} send back from backend".format(msg[0].tp))
            qubits.append(self.parse_CQC_msg(msg))
            self.print_CQC_msg(msg)
        if notify:
            message = self.readMessage()
            if message[0].tp != CQC_TP_DONE:
                raise CQCUnsuppError(
                    "Unexpected message send back from the server. Message: {}".format(message[0].printable())
                )

        return qubits

    def release_qubits(self, qubits, notify=True, block=False, action=False):
        """
        Release qubits so backend can free them up for other uses
        :param qubits: a list of qubits to be released
        :param notify:     Do we wish to be notified when done.
        :param block:         Do we want the qubit to be blocked
        :param action:     Execute the releases recursively or sequencely
        """

        if isinstance(qubits, qubit):
            qubits = [qubits]
        assert isinstance(qubits, list)
        n = len(qubits)

        if n == 0:  # then we don't need to do anything
            return

        logging.debug("App {} tells CQC: Release {} qubits".format(self.name, n))
        if action:
            hdr_length = CQCCmdHeader.HDR_LENGTH + CQCSequenceHeader.HDR_LENGTH
        else:
            hdr_length = CQCCmdHeader.HDR_LENGTH
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, CQC_TP_COMMAND, self._appID, hdr_length * n)
        cqc_msg = hdr.pack()

        release_messages = b""

        for i in range(n):
            q = qubits[i]
            try:
                q.check_active()
            except QubitNotActiveError as e:
                raise QubitNotActiveError(
                    str(e) + ". Qubit {} is not active. None of the qubits are released".format(q._qID)
                )
            q._set_active(False)
            cmd_hdr = CQCCmdHeader()
            cmd_hdr.setVals(q._qID, CQC_CMD_RELEASE, int(notify), int(block), int(action))
            release_messages += cmd_hdr.pack()
            if action:
                seq_hdr = CQCSequenceHeader()
                # After this one we are sending n-i-1 more releases
                seq_hdr.setVals(hdr_length * (n - i - 1))
                release_messages += seq_hdr.pack()

        self._s.send(cqc_msg + release_messages)

        if notify:
            msg = self.readMessage()
            self.check_error(msg[0])
            if msg[0].tp != CQC_TP_DONE:
                raise CQCUnsuppError(
                    "Unexpected message send back from the server. Message: {}".format(msg[0].printable())
                )
            self.print_CQC_msg(msg)

    def release_all_qubits(self):
        """
        Releases all qubits off this connection
        """
        return self.release_qubits(self.active_qubits[:])

    def sendFactory(
        self,
        qID,
        command,
        num_iter,
        notify=1,
        block=1,
        action=0,
        xtra_qID=-1,
        remote_appID=0,
        remote_node=0,
        remote_port=0,
        step_size=0,
    ):
        """
        Sends a factory message

        - **Arguments**

            :qID:         qubit ID
            :command:     Command to be executed, eg CQC_CMD_H
            :num_iter:     Number of times to execute command
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the factory to be blocked
            :action:     Are there more commands to be executed
            :xtra_qID:     Extra qubit ID for for example CNOT
            :remote_appID:     Application ID of remote host
            :remote_node:     ip of remote host in cqc network
            :remote_port:     port of remote host in cqc network
            :cmd_length:     length of extra commands
        """
        warnings.warn("Send factory is deprecated. Use flush_factory() instead", DeprecationWarning)

        if xtra_qID == -1:
            if command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
                raise CQCUnsuppError("Please provide a target qubit")
            xtra_qID = 0

            # Check what extra header we require
        xtra_hdr = None
        if hasXtraHeader(command):
            if command == CQC_CMD_SEND or command == CQC_CMD_EPR:
                xtra_hdr = CQCCommunicationHeader()
                xtra_hdr.setVals(remote_appID, remote_node, remote_port)
            elif command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
                xtra_hdr = CQCXtraQubitHeader()
                xtra_hdr.setVals(xtra_qID)
            else:
                xtra_hdr = CQCRotationHeader()
                xtra_hdr.setVals(step_size)
            xtra_msg = xtra_hdr.pack()
            hdr_length = CQC_CMD_HDR_LENGTH + CQCFactoryHeader.HDR_LENGTH + xtra_hdr.HDR_LENGTH
        else:
            xtra_msg = b""
            hdr_length = CQC_CMD_HDR_LENGTH + CQCFactoryHeader.HDR_LENGTH

            # Send Header
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, CQC_TP_FACTORY, self._appID, hdr_length)
        msg = hdr.pack()

        # Factory header
        factory_hdr = CQCFactoryHeader()
        factory_hdr.setVals(num_iter, notify, block)
        factory_msg = factory_hdr.pack()

        # Send Command
        cmd_hdr = CQCCmdHeader()
        cmd_hdr.setVals(qID, command, 0, block, action)
        cmd_msg = cmd_hdr.pack()
        logging.debug("App {} sends CQC message {}".format(self.name, hdr.printable()))
        logging.debug("App {} sends CQC message {}".format(self.name, factory_hdr.printable()))

        logging.debug("App {} sends CQC message {}".format(self.name, cmd_hdr.printable()))
        if xtra_hdr:
            logging.debug("App {} sends CQC message {}".format(self.name, xtra_hdr.printable()))
        self._s.send(msg + factory_msg + cmd_msg + xtra_msg)

        # Get RECV messages
        # Some commands expect to get a list of messages back, check those
        res = []
        if shouldReturn(command):
            for _ in range(num_iter):
                message = self.readMessage()
                if message[0].tp in {CQC_TP_NEW_OK, CQC_TP_RECV, CQC_TP_EPR_OK}:
                    qID = message[1].qubit_id
                    q = qubit(self, createNew=False, q_id=qID, notify=notify, block=block)
                    q._set_active(True)
                    res.append(q)
                elif message[0].tp == CQC_TP_MEASOUT:
                    outcome = message[1].outcome
                    res.append(outcome)
        if notify:
            message = self.readMessage()
            if message[0].tp != CQC_TP_DONE:
                raise CQCUnsuppError(
                    "Unexpected message send back from the server. Message: {}".format(message[0].printable())
                )
        return res

    def readMessage(self, maxsize=192):  # WHAT IS GOOD SIZE?
        """
        Receive the whole message from cqc server.
        Returns (CQCHeader,None,None), (CQCHeader,CQCNotifyHeader,None) or (CQCHeader,CQCNotifyHeader,EntInfoHeader)
        depending on the type of message.
        Maxsize is the max size of message.
        """

        # Initilize checks
        gotCQCHeader = False
        if self.buf:
            checkedBuf = False
        else:
            checkedBuf = True

        while True:
            # If buf does not contain enough data, read in more
            if checkedBuf:
                # Receive data
                data = self._s.recv(maxsize)

                # Read whatever we received into a buffer
                if self.buf:
                    self.buf += data
                else:
                    self.buf = data

                    # If we don't have the CQC header yet, try and read it in full.
            if not gotCQCHeader:
                if len(self.buf) < CQC_HDR_LENGTH:
                    # Not enough data for CQC header, return and wait for the rest
                    checkedBuf = True
                    continue

                    # Got enough data for the CQC Header so read it in
                gotCQCHeader = True
                rawHeader = self.buf[0:CQC_HDR_LENGTH]
                currHeader = CQCHeader(rawHeader)

                # Remove the header from the buffer
                self.buf = self.buf[CQC_HDR_LENGTH : len(self.buf)]

                # Check for error
                self.check_error(currHeader)

                # Check whether we already received all the data
            if len(self.buf) < currHeader.length:
                # Still waiting for data
                checkedBuf = True
                continue
            else:
                break
                # We got all the data, read other headers if there is any
        if currHeader.length == 0:
            return currHeader, None, None
        else:
            if currHeader.tp == CQC_TP_INF_TIME:
                timeinfo_header = self._extract_header(CQCTimeinfoHeader)
                return currHeader, timeinfo_header, None
            elif currHeader.tp == CQC_TP_MEASOUT:
                measout_header = self._extract_header(CQCMeasOutHeader)
                return currHeader, measout_header, None
            elif currHeader.tp in [CQC_TP_RECV, CQC_TP_NEW_OK, CQC_TP_EXPIRE]:
                xtra_qubit_header = self._extract_header(CQCXtraQubitHeader)
                return currHeader, xtra_qubit_header, None
            elif currHeader.tp == CQC_TP_EPR_OK:
                xtra_qubit_header = self._extract_header(CQCXtraQubitHeader)
                ent_info_hdr = self._extract_header(EntInfoHeader)
                return currHeader, xtra_qubit_header, ent_info_hdr

    def _extract_header(self, header_class):
        """
        Extracts the given header class from the first part of the current buffer.
        :param header_class: Subclassed from `SimulaQron.cqc.backend.cqcHeader.Header`
        :return: An instance of the class
        """
        if not issubclass(header_class, Header):
            raise ValueError("header_class {} is not a subclass of Header".format(header_class))

        try:
            rawHeader = self.buf[:header_class.HDR_LENGTH]
        except IndexError:
            raise ValueError("Got a header message of unexpected size")
        self.buf = self.buf[header_class.HDR_LENGTH: len(self.buf)]
        header = header_class(rawHeader)

        return header

    def print_CQC_msg(self, message):
        """
        Prints messsage returned by the readMessage method of CQCConnection.
        """
        hdr = message[0]
        otherHdr = message[1]
        entInfoHdr = message[2]

        if hdr.tp == CQC_TP_HELLO:
            logging.debug("CQC tells App {}: 'HELLO'".format(self.name))
        elif hdr.tp == CQC_TP_EXPIRE:
            logging.debug("CQC tells App {}: 'Qubit with ID {} has expired'".format(self.name, otherHdr.qubit_id))
        elif hdr.tp == CQC_TP_DONE:
            logging.debug("CQC tells App {}: 'Done with command'".format(self.name))
        elif hdr.tp == CQC_TP_RECV:
            logging.debug("CQC tells App {}: 'Received qubit with ID {}'".format(self.name, otherHdr.qubit_id))
        elif hdr.tp == CQC_TP_EPR_OK:

            # Lookup host name
            remote_node = entInfoHdr.node_B
            remote_port = entInfoHdr.port_B
            remote_name = None
            try:
                for node in self._cqcNet.hostDict.values():
                    if (node.ip == remote_node) and (node.port == remote_port):
                        remote_name = node.name
                        break
                if remote_name is None:
                    raise RuntimeError("Remote node ({},{}) is not in config-file.".format(remote_node, remote_port))
            except AttributeError:
                remote_name = "({}, {})".format(remote_node, remote_port)

            logging.debug(
                "CQC tells App {}: 'EPR created with node {}, using qubit with ID {}'".format(
                    self.name, remote_name, otherHdr.qubit_id
                )
            )
        elif hdr.tp == CQC_TP_MEASOUT:
            logging.debug("CQC tells App {}: 'Measurement outcome is {}'".format(self.name, otherHdr.outcome))
        elif hdr.tp == CQC_TP_INF_TIME:
            logging.debug("CQC tells App {}: 'Timestamp is {}'".format(self.name, otherHdr.datetime))

    def parse_CQC_msg(self, message, q=None, is_factory=False):
        """
        parses the cqc message and returns the relevant value of that measure
        (qubit, measurement outcome)

        :param message: str
            the cqc message to be parsed
        :param q: :obj:`SimulaQron.cqc.pythonLib.cqc.qubit`
            the qubit object we should save the qubit to
        :param is_factory: bool
            whether the returned message came from a factory. If so, do not change the qubit, but create a new one
        :return: the result of the message (either a qubit, or a measurement outcome. Otherwise None
        """
        hdr = message[0]
        otherHdr = message[1]
        entInfoHdr = message[2]

        if hdr.tp in {CQC_TP_RECV, CQC_TP_NEW_OK, CQC_TP_EPR_OK}:
            if is_factory:
                q._set_active(False)  # Set qubit to inactive so it can't be used anymore
                q = qubit(self, createNew=False)
            if q is None:
                q = qubit(self, createNew=False)
            q._qID = otherHdr.qubit_id
            q.set_entInfo(entInfoHdr)
            q._set_active(True)
            return q
        if hdr.tp == CQC_TP_MEASOUT:
            return otherHdr.outcome
        if hdr.tp == CQC_TP_INF_TIME:
            return otherHdr.datetime

    def check_error(self, hdr):
        """
        Checks if there is an error returned.
        """
        self._errorHandler(hdr.tp)

    def _errorHandler(self, cqc_err):
        """
        Raises an error if there is an error-message
        """
        if cqc_err == CQC_ERR_GENERAL:
            raise CQCGeneralError("General error")
        if cqc_err == CQC_ERR_NOQUBIT:
            raise CQCNoQubitError("No more qubits available")
        if cqc_err == CQC_ERR_UNSUPP:
            raise CQCUnsuppError("Sequence not supported")
        if cqc_err == CQC_ERR_TIMEOUT:
            raise CQCTimeoutError("Timeout")
        if cqc_err == CQC_ERR_UNKNOWN:
            raise CQCUnknownError("Unknown qubit ID")

    def sendQubit(self, q, name, remote_appID=0, remote_socket=None, notify=True, block=True):
        """
        Sends qubit to another node in the cqc network. If this node is not in the network an error is raised.

        - **Arguments**

            :q:         The qubit to send.
            :Name:         Name of the node as specified in the cqc network config file.
            :remote_appID:     The app ID of the application running on the receiving node.
            :remote_socket: tuple (str, int) of ip and port number. Needed if no cqcFile was specified
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        remote_ip, remote_port = get_remote_from_directory_or_address(self._cqcNet, name, remote_socket)

        if self.pend_messages:
            # print info
            logging.debug(
                "App {} pends message: 'Send qubit with ID {} to {} and appID {}'".format(
                    self.name, q._qID, name, remote_appID
                )
            )
            self.pending_messages.append(
                [q, CQC_CMD_SEND, int(notify), int(block), [remote_appID, remote_ip, remote_port]]
            )
        else:
            # print info
            logging.debug(
                "App {} tells CQC: 'Send qubit with ID {} to {} and appID {}'".format(
                    self.name, q._qID, name, remote_appID
                )
            )
            self.sendCmdXtra(
                q._qID,
                CQC_CMD_SEND,
                notify=int(notify),
                block=int(block),
                remote_appID=remote_appID,
                remote_node=remote_ip,
                remote_port=remote_port,
            )
            if notify:
                message = self.readMessage()
                self.print_CQC_msg(message)

                # Deactivate qubit
            q._set_active(False)

    def recvQubit(self, notify=True, block=True):
        """
        Receives a qubit.

        - **Arguments**

            :q:         The qubit to send.
            :Name:         Name of the node as specified in the cqc network config file.
            :remote_appID:     The app ID of the application running on the receiving node.
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """

        # initialize the qubit
        q = qubit(self, createNew=False)

        if self.pend_messages:
            # print info
            logging.debug("App {} pends message: 'Receive qubit'".format(self.name))
            self.pending_messages.append([q, CQC_CMD_RECV, int(notify), int(block)])
            return q
        else:
            # print info
            logging.debug("App {} tells CQC: 'Receive qubit'".format(self.name))
            self.sendCommand(0, CQC_CMD_RECV, notify=int(notify), block=int(block))

            # Get RECV message
            message = self.readMessage()
            otherHdr = message[1]
            q_id = otherHdr.qubit_id

            self.print_CQC_msg(message)

            if notify:
                message = self.readMessage()
                self.print_CQC_msg(message)

                # initialize the qubit
            q._qID = q_id

            # Activate and return qubit
            q._set_active(True)
            return q

    def createEPR(self, name, remote_appID=0, remote_socket=None, notify=True, block=True):
        """
        Creates epr with other host in cqc network.

        - **Arguments**

            :name:         Name of the node as specified in the cqc network config file.
            :remote_appID:     The app ID of the application running on the receiving node.
            :remote_socket: tuple (str, int) of ip and port number. Needed if no cqcFile was specified
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """

        remote_ip, remote_port = get_remote_from_directory_or_address(self._cqcNet, name, remote_socket)

        # initialize the qubit
        q = qubit(self, createNew=False)

        if self.pend_messages:
            # print info
            logging.debug(
                "App {} pends message: 'Create EPR-pair with {} and appID {}'".format(self.name, name, remote_appID)
            )

            self.pending_messages.append(
                [q, CQC_CMD_EPR, int(notify), int(block), [remote_appID, remote_ip, remote_port]]
            )
            return q
        else:
            # print info
            logging.debug(
                "App {} tells CQC: 'Create EPR-pair with {} and appID {}'".format(self.name, name, remote_appID)
            )

            self.sendCmdXtra(
                0,
                CQC_CMD_EPR,
                notify=int(notify),
                block=int(block),
                remote_appID=remote_appID,
                remote_node=remote_ip,
                remote_port=remote_port,
            )
            # Get RECV message
            message = self.readMessage()
            otherHdr = message[1]
            entInfoHdr = message[2]
            q_id = otherHdr.qubit_id

            self.print_CQC_msg(message)

            if notify:
                message = self.readMessage()
                self.print_CQC_msg(message)

            q.set_entInfo(entInfoHdr)
            q._qID = q_id
            # Activate and return qubit
            q._set_active(True)
            return q

    def recvEPR(self, notify=True, block=True):
        """
        Receives a qubit from an EPR-pair generated with another node.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """

        # initialize the qubit
        q = qubit(self, createNew=False)
        if self.pend_messages:
            # print info
            logging.debug("App {} pends message: 'Receive half of EPR'".format(self.name))
            self.pending_messages.append([q, CQC_CMD_EPR_RECV, int(notify), int(block)])
            return q
        else:
            # print info
            logging.debug("App {} tells CQC: 'Receive half of EPR'".format(self.name))
            self.sendCommand(0, CQC_CMD_EPR_RECV, notify=int(notify), block=int(block))

            # Get RECV message
            message = self.readMessage()
            otherHdr = message[1]
            entInfoHdr = message[2]
            q_id = otherHdr.qubit_id

            self.print_CQC_msg(message)

            if notify:
                message = self.readMessage()
                self.print_CQC_msg(message)

                # initialize the qubit
            q.set_entInfo(entInfoHdr)
            q._qID = q_id

            # Activate and return qubit
            q._set_active(True)
            return q

    def set_pending(self, pend_messages):
        """
        Set the pend_messages flag.
        If true, flush() has to be called to send all pending_messages in sequence to the backend
        If false, all commands are directly send to the back_end
        :param pend_messages: Boolean to indicate if messages should pend or not
        """
        # Check if the list is not empty, give a warning if it isn't
        if self.pending_messages:
            logging.warning("List of pending messages is not empty, flushing them")
            self.flush()
        self.pend_messages = pend_messages

    def flush(self, do_sequence=True):
        """
        Flush all pending messages to the backend.
        :param do_sequence: boolean to indicate if you want to send the pending messages as a sequence
        :return: A list of things that are send back from the server. Can be qubits, or outcomes
        """
        return self.flush_factory(1, do_sequence)

    def flush_factory(self, num_iter, do_sequence=True, block_factory=False):
        """
        Flushes the current pending sequence in a factory. It is performed multiple times
        :param num_iter: The amount of times the current pending sequence is performed
        :return: A list of outcomes/qubits that are produced by the commands
        """
        # Because of new/recv we might have to send headers multiple times
        # Loop over the pending_messages until there are no more
        # It should only enter the while loop once if num_iter == 1
        # Otherwise it loops for every non active qubit it encounters
        res = []
        while self.pending_messages:
            logging.debug("App {} starts flushing pending messages".format(self.name))
            pending_headers = []
            should_notify = False
            header_length = 0
            ready_messages = []
            # Loop over the messages until we encounter an inactive qubit (or end of list)
            for message in self.pending_messages[:]:
                q = message[0]
                cqc_command = message[1]

                qubits_not_active = not q._active and cqc_command not in {
                    CQC_CMD_EPR_RECV,
                    CQC_CMD_RECV,
                    CQC_CMD_NEW,
                    CQC_CMD_EPR,
                }

                if len(message) > 4:
                    values = message[4]
                else:
                    values = []
                try:
                    xtra_header = createXtraHeader(cqc_command, values)
                except QubitNotActiveError:
                    qubits_not_active = True

                    # Check if the q is active, if it is not, send the current pending_headers
                    # Then check again, if it still not active, throw an error
                if qubits_not_active:
                    if num_iter != 1:
                        raise CQCUnsuppError("Some qubits are non active in the factory, this is not supported (yet?)")
                    if not pending_headers:  # If all messages already have been send, the qubit is inactive
                        raise CQCNoQubitError("Qubit is not active")
                    logging.debug(
                        "App {} encountered a non active qubit, sending current pending messages".format(self.name)
                    )
                    break  # break out the for loop

                    # set qubit to inactive, since we send it away or measured it
                if cqc_command == CQC_CMD_SEND or cqc_command == CQC_CMD_MEASURE:
                    q._set_active(False)

                q_id = q._qID if q._qID is not None else 0

                self.pending_messages.remove(message)
                ready_messages.append(message)

                notify = message[2]
                should_notify = should_notify or notify
                block = message[3]

                cmd_header = CQCCmdHeader()
                cmd_header.setVals(q_id, cqc_command, notify, block, int(do_sequence))
                header_length += cmd_header.HDR_LENGTH
                pending_headers.append(cmd_header)

                if xtra_header is not None:
                    header_length += xtra_header.HDR_LENGTH
                    pending_headers.append(xtra_header)

                if do_sequence:
                    sequence_header = CQCSequenceHeader()
                    header_length += sequence_header.HDR_LENGTH
                    pending_headers.append(sequence_header)

                    # create the header and sequence headers if needed
                    # We need to find the header length for sequence,
                    # so loop over the pending_headers in reverse
            if do_sequence:
                sequence_length = 0
                for header in reversed(pending_headers):
                    if isinstance(header, CQCSequenceHeader):
                        header.setVals(sequence_length)
                    sequence_length += header.HDR_LENGTH

            if num_iter != 1:
                factory_header = CQCFactoryHeader()
                factory_header.setVals(num_iter, should_notify, block_factory)
                header_length += factory_header.HDR_LENGTH
                pending_headers.insert(0, factory_header)
                cqc_type = CQC_TP_FACTORY
            else:
                cqc_type = CQC_TP_COMMAND

            cqc_header = CQCHeader()
            cqc_header.setVals(CQC_VERSION, cqc_type, self._appID, header_length)
            pending_headers.insert(0, cqc_header)

            # send the headers
            for header in pending_headers:
                logging.debug("App {} sends CQC: {}".format(self.name, header.printable()))
                self._s.send(header.pack())

                # Read out any returned messages from the backend
            for i in range(num_iter):
                for data in ready_messages:
                    q = data[0]  # qubit object that might be adjusted
                    cmd = data[1]
                    if shouldReturn(cmd):
                        message = self.readMessage()
                        self.check_error(message[0])
                        res.append(self.parse_CQC_msg(message, q, num_iter != 1))
                        self.print_CQC_msg(message)

            if should_notify:
                message = self.readMessage()
                self.check_error(message[0])
        return res

    def tomography(self, preparation, iterations, progress=True):
        """
        Does a tomography on the output from the preparation specified.
        The frequencies from X, Y and Z measurements are returned as a tuple (f_X,f_Y,f_Z).

        - **Arguments**

            :preparation:     A function that takes a CQCConnection as input and prepares a qubit and returns this
            :iterations:     Number of measurements in each basis.
            :progress_bar:     Displays a progress bar
        """
        accum_outcomes = [0, 0, 0]
        if progress:
            bar = ProgressBar(3 * iterations)

            # Measure in X
        for _ in range(iterations):
            # Progress bar
            if progress:
                bar.increase()

                # prepare and measure
            q = preparation(self)
            q.H()
            m = q.measure()
            accum_outcomes[0] += m

            # Measure in Y
        for _ in range(iterations):
            # Progress bar
            if progress:
                bar.increase()

                # prepare and measure
            q = preparation(self)
            q.K()
            m = q.measure()
            accum_outcomes[1] += m

            # Measure in Z
        for _ in range(iterations):
            # Progress bar
            if progress:
                bar.increase()

                # prepare and measure
            q = preparation(self)
            m = q.measure()
            accum_outcomes[2] += m

        if progress:
            bar.close()
            del bar

        freqs = map(lambda x: x / iterations, accum_outcomes)
        return list(freqs)

    def test_preparation(self, preparation, exp_values, conf=2, iterations=100, progress=True):
        """
        Test the preparation of a qubit.
        Returns True if the expected values are inside the confidence interval produced from the data received from
        the tomography function

        - **Arguments**

            :preparation:     A function that takes a CQCConnection as input and prepares a qubit and returns this
            :exp_values:     The expected values for measurements in the X, Y and Z basis.
            :conf:         Determines the confidence region (+/- conf/sqrt(iterations) )
            :iterations:     Number of measurements in each basis.
            :progress_bar:     Displays a progress bar
        """
        epsilon = conf / math.sqrt(iterations)

        freqs = self.tomography(preparation, iterations, progress=progress)
        for i in range(3):
            if abs(freqs[i] - exp_values[i]) > epsilon:
                print(freqs, exp_values, epsilon)
                return False
        return True


class ProgressBar:
    def __init__(self, maxitr):
        self.maxitr = maxitr
        self.itr = 0
        try:
            self.cols = os.get_terminal_size().columns
        except (OSError, AttributeError):
            self.cols = 60
        print("")
        self.update()

    def increase(self):
        self.itr += 1
        self.update()

    def update(self):
        cols = self.cols - 8
        assert self.itr <= self.maxitr
        ratio = float(self.itr) / self.maxitr
        procent = int(ratio * 100)
        progress = "=" * int(cols * ratio)
        sys.stdout.write("\r")
        sys.stdout.write("[%*s] %d%%" % (-cols, progress, procent))
        sys.stdout.flush()
        pass

    def close(self):
        print("")


class CQCGeneralError(Exception):
    pass


class CQCNoQubitError(CQCGeneralError):
    pass


class CQCUnsuppError(CQCGeneralError):
    pass


class CQCTimeoutError(CQCGeneralError):
    pass


class CQCInuseError(CQCGeneralError):
    pass


class CQCUnknownError(CQCGeneralError):
    pass


class QubitNotActiveError(CQCGeneralError):
    pass


class qubit:
    """
    A qubit.
    """

    def __init__(self, cqc, notify=True, block=True, createNew=True, q_id=None, entInfo=None):
        """
        Initializes the qubit. The cqc connection must be given.
        If notify, the return message is received before the method finishes.
        createNew is set to False when we receive a qubit.

        - **Arguments**

            :cqc:         The CQCconnection used
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
            :createNew:     If NEW-message should be sent, used internally
            :q_id:         Qubit id, used internally if createNew
            :entInfo:     Entanglement information, if qubit is part of EPR-pair
        """

        # Cqc connection
        self._cqc = cqc

        # Check if the cqc connection was openened using a 'with' statement
        # If not, raise a deprecation warning
        if not self._cqc._opened_with_with:
            logging.warning(
                "You should open CQCConnection in a context, i.e. using 'with CQCConnection(...) as cqc:'. "
                "Then qubits will be automatically released by the end of the program, independently of what happens. "
                "For more information, see https://softwarequtech.github.io/SimulaQron/html/PythonLib.html"
            )

            # Whether the qubit is active. Will be set in the first run
        self._active = None

        if createNew:
            if cqc.pend_messages:
                # print info
                logging.debug("App {} pends message:'Create qubit'".format(self._cqc.name))

                cqc.pending_messages.append([self, CQC_CMD_NEW, int(notify), int(block)])
                # Set q id, None by default
                self._qID = q_id
                self._set_active(False)
            else:
                # print info
                logging.debug("App {} tells CQC: 'Create qubit'".format(self._cqc.name))

                # Create new qubit at the cqc server
                self._cqc.sendCommand(0, CQC_CMD_NEW, notify=int(notify), block=int(block))

                # Get qubit id
                message = self._cqc.readMessage()
                try:
                    otherHdr = message[1]
                    self._qID = otherHdr.qubit_id
                except AttributeError:
                    raise CQCGeneralError("Didn't receive the qubit id")
                    # Activate qubit
                self._set_active(True)

                if notify:
                    message = self._cqc.readMessage()
                    self._cqc.print_CQC_msg(message)
        else:
            self._qID = q_id
            self._set_active(False)  # Why?

            # Entanglement information
        self._entInfo = entInfo

        # Lookup remote entangled node
        self._remote_entNode = None
        if self._entInfo:
            ip = self._entInfo.node_B
            port = self._entInfo.port_B
            try:
                for node in self._cqc._cqcNet.hostDict.values():
                    if (node.ip == ip) and (node.port == port):
                        self._remote_entNode = node.name
                        break
            except AttributeError:
                self._remote_entNode = None

    def __str__(self):
        if self._active:
            return "Qubit at the node {}".format(self._cqc.name)
        else:
            return "Not active qubit"

    def get_entInfo(self):
        return self._entInfo

    def print_entInfo(self):
        if self._entInfo:
            print(self._entInfo.printable())
        else:
            print("No entanglement information")

    def set_entInfo(self, entInfo):
        self._entInfo = entInfo

        # Lookup remote entangled node
        self._remote_entNode = None
        if self._entInfo:
            ip = self._entInfo.node_B
            port = self._entInfo.port_B
            try:
                for node in self._cqc._cqcNet.hostDict.values():
                    if (node.ip == ip) and (node.port == port):
                        self._remote_entNode = node.name
                        break
            except AttributeError:
                self._remote_entNode = None

    def is_entangled(self):
        if self._entInfo:
            return True
        return False

    def get_remote_entNode(self):
        return self._remote_entNode

    def check_active(self):
        """
        Checks if the qubit is active
        """
        if self._cqc.pend_messages:
            return  # will be handled in the flush, not here
        if not self._active:
            raise QubitNotActiveError("Qubit is not active, has either been sent, measured, released or not received")

    def _set_active(self, be_active):
        # Check if not already new state
        if self._active == be_active:
            return
        if be_active:
            self._cqc.active_qubits.append(self)
        else:
            if self in self._cqc.active_qubits:
                self._cqc.active_qubits.remove(self)

        self._active = be_active

    def _single_qubit_gate(self, command, notify, block):
        """
        Performs a single qubit gate specified by the command, called in I(), X(), Y() etc
        :param command: the identifier of the command, as specified in cqcHeader.py
        :param notify: Do we wish to be notified when done
        :param block: Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()

        if self._cqc.pend_messages:
            # print info
            logging.debug(
                "App {} pends message: 'Send command {} for qubit with ID {}'".format(
                    self._cqc.name, command, self._qID
                )
            )

            self._cqc.pending_messages.append([self, command, int(notify), int(block)])
        else:
            # print info
            logging.debug(
                "App {} tells CQC: 'Send command {} for qubit with ID {}'".format(self._cqc.name, command, self._qID)
            )

            self._cqc.sendCommand(self._qID, command, notify=int(notify), block=int(block))
            if notify:
                message = self._cqc.readMessage()
                self._cqc.print_CQC_msg(message)

    def I(self, notify=True, block=True):
        """
        Performs an identity gate on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_I, notify, block)

    def X(self, notify=True, block=True):
        """
        Performs a X on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_X, notify, block)

    def Y(self, notify=True, block=True):
        """
        Performs a Y on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_Y, notify, block)

    def Z(self, notify=True, block=True):
        """
        Performs a Z on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_Z, notify, block)

    def T(self, notify=True, block=True):
        """
        Performs a T gate on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_T, notify, block)

    def H(self, notify=True, block=True):
        """
        Performs a Hadamard on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_H, notify, block)

    def K(self, notify=True, block=True):
        """
        Performs a K gate on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_K, notify, block)

    def _single_gate_rotation(self, command, step, notify, block):
        """
        Perform a rotation on a qubit
        :param command: the rotation qubit command as specified in cqcHeader.py
        :param step: Determines the rotation angle in steps of 2*pi/256
        :param notify: Do we wish to be notified when done
        :param block: Do we want the qubit to be blocked
        :return:
        """
        # check if qubit is active
        self.check_active()

        if self._cqc.pend_messages:
            # print info
            logging.debug(
                "App {} pends message: 'Perform rotation command {} (angle {}*2pi/256) to qubit with ID {}'".format(
                    self._cqc.name, command, step, self._qID
                )
            )
            self._cqc.pending_messages.append([self, command, int(notify), int(block), step])
        else:
            # print info
            logging.debug(
                "App {} tells CQC: 'Perform rotation command {} (angle {}*2pi/256) to qubit with ID {}'".format(
                    self._cqc.name, command, step, self._qID
                )
            )
            self._cqc.sendCmdXtra(self._qID, command, step=step, notify=int(notify), block=int(block))
            if notify:
                message = self._cqc.readMessage()
                self._cqc.print_CQC_msg(message)

    def rot_X(self, step, notify=True, block=True):
        """
        Applies rotation around the x-axis with the angle of step*2*pi/256 radians.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :step:         Determines the rotation angle in steps of 2*pi/256
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_gate_rotation(CQC_CMD_ROT_X, step, notify, block)

    def rot_Y(self, step, notify=True, block=True):
        """
        Applies rotation around the y-axis with the angle of step*2*pi/256 radians.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :step:         Determines the rotation angle in steps of 2*pi/256
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_gate_rotation(CQC_CMD_ROT_Y, step, notify, block)

    def rot_Z(self, step, notify=True, block=True):
        """
        Applies rotation around the z-axis with the angle of step*2*pi/256 radians.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :step:         Determines the rotation angle in steps of 2*pi/256
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_gate_rotation(CQC_CMD_ROT_Z, step, notify, block)

    def _two_qubit_gate(self, command, target, notify, block):
        """
        Perform a two qubit gate on the qubit
        :param command: the two qubit gate command as specified in cqcHeader.py
        :param target: The target qubit
        :param notify: Do we wish to be notified when done
        :param block: Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()
        target.check_active()

        if self._cqc != target._cqc:
            raise CQCUnsuppError("Multi qubit operations can only operate on qubits in the same process")

        if self == target:
            raise CQCUnsuppError("Cannot perform multi qubit operation where control and target are the same")

        if self._cqc.pend_messages:
            # print info
            logging.debug(
                "App {} pends message: 'Perform CNOT to qubits with IDs {}(control) {}(target)'".format(
                    self._cqc.name, self._qID, target._qID
                )
            )
            self._cqc.pending_messages.append([self, command, int(notify), int(block), target])
        else:
            # print info
            logging.debug(
                "App {} tells CQC: 'Perform CNOT to qubits with IDs {}(control) {}(target)'".format(
                    self._cqc.name, self._qID, target._qID
                )
            )
            self._cqc.sendCmdXtra(self._qID, command, notify=int(notify), block=int(block), xtra_qID=target._qID)
            if notify:
                message = self._cqc.readMessage()
                self._cqc.print_CQC_msg(message)

    def cnot(self, target, notify=True, block=True):
        """
        Applies a cnot onto target.
        Target should be a qubit-object with the same cqc connection.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :target:     The target qubit
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._two_qubit_gate(CQC_CMD_CNOT, target, notify, block)

    def cphase(self, target, notify=True, block=True):
        """
        Applies a cphase onto target.
        Target should be a qubit-object with the same cqc connection.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :target:     The target qubit
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._two_qubit_gate(CQC_CMD_CPHASE, target, notify, block)

    def measure(self, inplace=False, block=True):
        """
        Measures the qubit in the standard basis and returns the measurement outcome.
        If now MEASOUT message is received, None is returned.
        If inplace=False, the measurement is destructive and the qubit is removed from memory.
        If inplace=True, the qubit is left in the post-measurement state.

        - **Arguments**

            :inplace:     If false, measure destructively.
            :block:         Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()

        if inplace:
            command = CQC_CMD_MEASURE_INPLACE
        else:
            command = CQC_CMD_MEASURE

        if self._cqc.pend_messages:
            self._cqc.pending_messages.append([self, command, 0, int(block)])
            # print info
            logging.debug("App {} pends message: 'Measure qubit with ID {}'".format(self._cqc.name, self._qID))

        else:
            # print info
            logging.debug("App {} tells CQC: 'Measure qubit with ID {}'".format(self._cqc.name, self._qID))

            self._cqc.sendCommand(self._qID, command, notify=0, block=int(block))

            # Return measurement outcome
            message = self._cqc.readMessage()
            if not inplace:
                self._set_active(False)
            try:
                otherHdr = message[1]
                return otherHdr.outcome
            except AttributeError:
                return None

    def reset(self, notify=True, block=True):
        """
        Resets the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()

        if self._cqc.pend_messages:
            # print info
            logging.debug("App {} pends message: 'Reset qubit with ID {}'".format(self._cqc.name, self._qID))

            self._cqc.pending_messages.append([self, CQC_CMD_RESET, int(notify), int(block)])
        else:
            # print info
            logging.debug("App {} tells CQC: 'Reset qubit with ID {}'".format(self._cqc.name, self._qID))

            self._cqc.sendCommand(self._qID, CQC_CMD_RESET, notify=int(notify), block=int(block))
            if notify:
                message = self._cqc.readMessage()
                self._cqc.print_CQC_msg(message)

    def release(self, notify=True, block=False):
        """
        Release the current qubit
        :param notify: Do we wish to be notified when done
        :param block: Do we want the qubit to be blocked
        :return:
        """
        return self._cqc.release_qubits([self], notify=notify, block=block)

    def getTime(self, block=True):
        """
        Returns the time information of the qubit.
        If now INF_TIME message is received, None is returned.

        - **Arguments**

            :block:         Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()

        # print info
        logging.debug("App {} tells CQC: 'Return time-info of qubit with ID {}'".format(self._cqc.name, self._qID))

        self._cqc.sendGetTime(self._qID, notify=0, block=int(block))

        # Return time-stamp
        message = self._cqc.readMessage()
        try:
            otherHdr = message[1]
            return otherHdr.datetime
        except AttributeError:
            return None

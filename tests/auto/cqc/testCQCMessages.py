#
# Copyright (c) 2018, Stephanie Wehner and Axel Dahlberg
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

import json
import unittest
import struct
import os

from SimulaQron.cqc.backend.cqcLogMessageHandler import CQCLogMessageHandler
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit, CQCUnsuppError, QubitNotActiveError
from SimulaQron.cqc.backend.cqcHeader import (
    CQCCmdHeader,
    CQC_CMD_SEND,
    CQC_CMD_EPR,
    CQC_CMD_CNOT,
    CQC_CMD_CPHASE,
    CQC_CMD_ROT_X,
    CQC_CMD_ROT_Y,
    CQC_CMD_ROT_Z,
    CQC_TP_COMMAND,
    CQC_TP_FACTORY,
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
    CQCFactoryHeader,
    CQC_CMD_HDR_LENGTH,
)


def get_last_entries(amount):
    file = "{}/logFile.json".format(CQCLogMessageHandler.dir_path)
    with open(file, "r") as outfile:
        logData = json.load(outfile)
    return logData[-amount:]


class CQCMessageTest(unittest.TestCase):
    # Only tests cqc_commands at the moment.
    # So no messages that are send back (notifications)

    @classmethod
    def setUpClass(cls):
        try:
            os.remove("{}/logFile.json".format(CQCLogMessageHandler.dir_path))
        except OSError:
            pass

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove("{}/logFile.json".format(CQCLogMessageHandler.dir_path))
        except OSError:
            pass

    def testNewQubit(self):
        with CQCConnection("Alice", appID=1) as alice:
            qubit(alice, block=False, notify=False)
            lastEntry = get_last_entries(1)[0]
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(lastEntry["node_name"], "Alice")
            self.assertEqual(cmd_header["instruction"], CQC_CMD_NEW)
            self.assertEqual(cmd_header["block"], False)
            self.assertEqual(cmd_header["notify"], False)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testI(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.I()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_I)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testX(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.X()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_X)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testY(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.Y()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_Y)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testZ(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.Z()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_Z)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testH(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.H()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_H)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testT(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.T()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_T)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testK(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.K()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_K)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testRotX(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.rot_X(200)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_ROT_X)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH + CQCRotationHeader.HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            xtra_header = lastEntry["xtra_header"]
            self.assertEqual(xtra_header["step"], 200)

    def testRotY(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.rot_Y(200)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_ROT_Y)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH + CQCRotationHeader.HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            xtra_header = lastEntry["xtra_header"]
            self.assertEqual(xtra_header["step"], 200)

    def testRotZ(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q1.rot_Z(200)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_ROT_Z)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH + CQCRotationHeader.HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            xtra_header = lastEntry["xtra_header"]
            self.assertEqual(xtra_header["step"], 200)

    def testRotXFail(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            with self.assertRaises(ValueError):
                q1.rot_X(256)

    def testRotXFailNone(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            with self.assertRaises(ValueError):
                q1.rot_X(None)

    def testRotXFailNaN(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            with self.assertRaises(ValueError):
                q1.rot_X("four")

    def testRotXFailNegative(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            with self.assertRaises(ValueError):
                q1.rot_X(-1)

    def testRotXFailFloat(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            with self.assertRaises(ValueError):
                q1.rot_X(1.1)

    def testCNot(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q2 = qubit(alice)
            q1.cnot(q2)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_CNOT)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH + CQCXtraQubitHeader.HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            xtra_header = lastEntry["xtra_header"]
            self.assertEqual(xtra_header["qubit_id"], cmd_header["qubit_id"] + 1)

    def testCNotRemote(self):
        with CQCConnection("Alice", appID=1) as alice:
            # The appId in xtra_header['app_id'] is not 2 when testing.
            # In fact, doing this code in a real application result in an error as of 2018-03-12
            with CQCConnection("Bob", appID=2) as bob:
                q1 = qubit(alice)
                q2 = qubit(bob)
                with self.assertRaises(CQCUnsuppError):
                    q1.cnot(q2)

    def testCPhase(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q2 = qubit(alice)
            q1.cphase(q2)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_CPHASE)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH + CQCXtraQubitHeader.HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            xtra_header = lastEntry["xtra_header"]
            self.assertEqual(xtra_header["qubit_id"], cmd_header["qubit_id"] + 1)

    def testSend(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            alice.sendQubit(q1, "Bob", remote_appID=2)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_SEND)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH + CQCCommunicationHeader.HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            xtra_header = lastEntry["xtra_header"]
            self.assertEqual(xtra_header["remote_app_id"], 2)
            self.assertNotEqual(xtra_header["remote_node"], 0)
            self.assertNotEqual(xtra_header["remote_port"], 0)

    def testSendSelf(self):
        with CQCConnection("Alice", appID=1) as alice:
            # Should not work in a real application
            q1 = qubit(alice)
            alice.sendQubit(q1, "Alice", remote_appID=1)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_SEND)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH + CQCCommunicationHeader.HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            xtra_header = lastEntry["xtra_header"]
            self.assertEqual(xtra_header["remote_app_id"], 1)
            self.assertNotEqual(xtra_header["remote_node"], 0)
            self.assertNotEqual(xtra_header["remote_port"], 0)

    def testRecv(self):
        with CQCConnection("Alice", appID=1) as alice:
            alice.recvQubit()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_RECV)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testEPRSend(self):
        with CQCConnection("Alice", appID=1) as alice:
            alice.createEPR("Bob", remote_appID=2)

            entries = get_last_entries(5)

            cmd_header_epr = entries[0]["cmd_header"]
            self.assertEqual(entries[0]["node_name"], "Alice")
            self.assertEqual(cmd_header_epr["instruction"], CQC_CMD_EPR)
            self.assertEqual(cmd_header_epr["block"], True)
            self.assertEqual(cmd_header_epr["notify"], True)
            cqc_header_epr = entries[0]["cqc_header"]
            self.assertEqual(cqc_header_epr["type"], CQC_TP_COMMAND)
            for i in range(5):
                self.assertEqual(
                    entries[i]["cqc_header"]["header_length"], CQC_CMD_HDR_LENGTH + CQCCommunicationHeader.HDR_LENGTH
                )
            self.assertEqual(cqc_header_epr["app_id"], 1)
            xtra_header_epr = entries[0]["xtra_header"]
            self.assertEqual(xtra_header_epr["remote_app_id"], 2)
            self.assertNotEqual(xtra_header_epr["remote_node"], 0)
            self.assertNotEqual(xtra_header_epr["remote_port"], 0)

            # Check if the qubits are created correctly
            # The protocol already knows what do to on EPR, so no new headers are made,
            # This means that the header of createEPR() is send into new(),
            # New headers have to be made for H() and CNOT() for the qubit ids,
            # but the instruction is not needed, defaults to 0
            self.assertEqual(entries[1]["cmd_header"]["instruction"], CQC_CMD_EPR)
            self.assertEqual(entries[3]["cmd_header"]["instruction"], 0)
            self.assertEqual(entries[4]["cmd_header"]["instruction"], 0)
            self.assertEqual(entries[4]["cmd_header"]["qubit_id"] + 1, entries[4]["xtra_header"]["qubit_id"])

    def testEPRRecv(self):
        with CQCConnection("Alice", appID=1) as alice:
            alice.recvEPR()
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_EPR_RECV)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], True)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)

    def testMeasure(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            m1 = q1.measure()
            # We've set that for this testing purposes, the measurement outcome is
            # always 2
            self.assertEqual(m1, 2)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_MEASURE)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], False)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            self.assertFalse(q1._active)

    def testMeasureInplace(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            m1 = q1.measure(inplace=True)
            # We've set that for this testing purposes, the measurement outcome is
            # always 2
            self.assertEqual(m1, 2)
            lastEntry = get_last_entries(1)[0]
            self.assertEqual(lastEntry["node_name"], "Alice")
            cmd_header = lastEntry["cmd_header"]
            self.assertEqual(cmd_header["instruction"], CQC_CMD_MEASURE_INPLACE)
            self.assertEqual(cmd_header["block"], True)
            self.assertEqual(cmd_header["notify"], False)
            cqc_header = lastEntry["cqc_header"]
            self.assertEqual(cqc_header["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_header["header_length"], CQC_CMD_HDR_LENGTH)
            self.assertEqual(cqc_header["app_id"], 1)
            self.assertTrue(q1._active)

    def testFactoryZero(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            alice.set_pending(True)
            q1.X()
            alice.flush_factory(0, do_sequence=False)
            alice.set_pending(False)
            q1.measure(inplace=True)

            # Checking the factory and the measure, factory should not log any commands
            lastEntries = get_last_entries(2)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 0)

            measureEntry = lastEntries[1]
            self.assertEqual(measureEntry["node_name"], "Alice")
            self.assertEqual(measureEntry["cmd_header"]["instruction"], CQC_CMD_MEASURE_INPLACE)
            self.assertEqual(measureEntry["cmd_header"]["qubit_id"], q1._qID)

            q1.measure()

    def testFactoryOnce(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            alice.set_pending(True)
            q1.X()
            alice.flush_factory(1, do_sequence=False)
            alice.set_pending(False)
            q1.measure(inplace=True)

            # Doing a factory once is equal to doing a sequence, so the factory header is not send
            lastEntries = get_last_entries(2)

            xEntry = lastEntries[0]
            self.assertEqual(xEntry["node_name"], "Alice")
            x_cmd_cmd_header = xEntry["cmd_header"]
            self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_X)
            self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)
            # cqc header is the same as the first.

            measureEntry = lastEntries[1]
            self.assertEqual(measureEntry["node_name"], "Alice")
            self.assertEqual(measureEntry["cmd_header"]["instruction"], CQC_CMD_MEASURE_INPLACE)
            self.assertEqual(measureEntry["cmd_header"]["qubit_id"], q1._qID)

    def testFactoryN(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            alice.set_pending(True)
            q1.X()
            alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)
            q1.measure(inplace=True)

            # Checking the factory and the measure, factory should not log any commands
            lastEntries = get_last_entries(12)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_X)
                self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)
                # cqc header is the same as the first.

            measureEntry = lastEntries[11]
            self.assertEqual(measureEntry["cmd_header"]["instruction"], CQC_CMD_MEASURE_INPLACE)
            self.assertEqual(measureEntry["cmd_header"]["qubit_id"], q1._qID)

    def testFactoryCNOTFalse(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            qubit(alice)
            with self.assertRaises(CQCUnsuppError):
                alice.set_pending(True)
                q1.cnot(q1)
                alice.flush_factory(10, do_sequence=False)
                alice.set_pending(False)

    def testFactoryCNOT(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q2 = qubit(alice)
            alice.set_pending(True)
            q1.cnot(q2)
            alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)

            entries = get_last_entries(11)
            factoryEntry = entries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH + CQCXtraQubitHeader.HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = entries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_CNOT)
                self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)
                x = xEntry["xtra_header"]
                self.assertEqual(x["qubit_id"], q2._qID)

    def testFactoryCPHASE(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            q2 = qubit(alice)
            alice.set_pending(True)
            q1.cphase(q2)
            alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)

            entries = get_last_entries(11)
            factoryEntry = entries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH + CQCXtraQubitHeader.HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = entries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_CPHASE)
                self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)
                x = xEntry["xtra_header"]
                self.assertEqual(x["qubit_id"], q2._qID)

    def testFactoryROTX(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            alice.set_pending(True)
            q1.rot_X(step=5)
            alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)
            q1.measure(inplace=True)

            # Checking the factory and the measure, factory should not log any commands
            lastEntries = get_last_entries(12)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH + CQCRotationHeader.HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_ROT_X)
                self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)
                xtra_header = xEntry["xtra_header"]
                self.assertEqual(xtra_header["step"], 5)
                # cqc header is the same as the first.

            measureEntry = lastEntries[11]
            self.assertEqual(measureEntry["cmd_header"]["instruction"], CQC_CMD_MEASURE_INPLACE)
            self.assertEqual(measureEntry["cmd_header"]["qubit_id"], q1._qID)

    def testFactoryNew(self):
        with CQCConnection("Alice", appID=1) as alice:
            # Should return a list of qubits with consecutive qubit ids
            alice.set_pending(True)
            qubit(alice)
            qubits = alice.flush_factory(10, do_sequence=False)
            # It is preferable to use the following however:
            # qubits = alice.allocate_qubits(10)
            alice.set_pending(False)
            # Checking the factory and the measure, factory should not log any commands
            lastEntries = get_last_entries(11)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_NEW)

            curID = qubits[0]._qID
            for q in qubits[1:]:
                self.assertEqual(q._qID, curID + 1)
                curID = q._qID

    def testFactoryMeasure(self):
        with CQCConnection("Alice", appID=1) as alice:
            # this one will go wrong in actual environment
            q1 = qubit(alice)
            alice.set_pending(True)
            q1.measure(inplace=False)
            # with self.assertRaises(QubitNotActiveError):
            measurements = alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)
            # All measurements should be equal to 2
            self.assertTrue(all(x == 2 for x in measurements))

            lastEntries = get_last_entries(11)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_MEASURE)
                self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)

    def testFactoryMeasureInplace(self):
        with CQCConnection("Alice", appID=1) as alice:
            # should give the same results as inplace = false
            q1 = qubit(alice)
            alice.set_pending(True)
            q1.measure(inplace=True)
            measurements = alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)
            # All measurements should be equal to 2
            self.assertTrue(all(x == 2 for x in measurements))

            lastEntries = get_last_entries(11)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_MEASURE_INPLACE)
                self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)

    def testFactoryReset(self):
        with CQCConnection("Alice", appID=1) as alice:

            q1 = qubit(alice)
            alice.set_pending(True)
            q1.reset()
            res = alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)

            self.assertListEqual(res, [])

            lastEntries = get_last_entries(11)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_RESET)
                self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)

    def testFactorySend(self):
        with CQCConnection("Alice", appID=1) as alice:
            q1 = qubit(alice)
            alice.set_pending(True)
            alice.sendQubit(q1, name="Bob", remote_appID=5)
            res = alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)

            self.assertListEqual(res, [])

            lastEntries = get_last_entries(11)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH + CQCCommunicationHeader.HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_SEND)
                self.assertEqual(x_cmd_cmd_header["qubit_id"], q1._qID)
                xtra_header = xEntry["xtra_header"]
                self.assertEqual(xtra_header["remote_app_id"], 5)
                self.assertGreater(xtra_header["remote_node"], 1)
                self.assertGreater(xtra_header["remote_port"], 1)

    def testFactoryRecv(self):
        with CQCConnection("Alice", appID=1) as alice:
            alice.set_pending(True)
            alice.recvQubit()
            qubits = alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)

            curID = qubits[0]._qID
            for q in qubits[1:]:
                self.assertEqual(q._qID, curID + 1)
                curID = q._qID

            lastEntries = get_last_entries(11)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_RECV)

    def testFactoryEPR(self):
        with CQCConnection("Alice", appID=1) as alice:
            alice.set_pending(True)
            alice.createEPR(name="Bob", remote_appID=5)
            qubits = alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)

            lastEntries = get_last_entries(51)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH + CQCCommunicationHeader.HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            # Check if the qubits are created correctly
            # The protocol already knows what do to on EPR, so no new headers are made,
            # This means that the header of createEPR() is send into new(),
            # New headers have to be made for H() and CNOT() for the qubit ids,
            # but the instruction is not needed, defaults to 0
            curID = [qubits[0]._qID]
            for q in qubits[1:]:
                self.assertEqual(q._qID, curID[-1] + 2)
                curID.append(q._qID)

            for i in range(10):
                xEntry = lastEntries[5 * i + 1]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_EPR)

                xtra_header = xEntry["xtra_header"]
                self.assertEqual(xtra_header["remote_app_id"], 5)
                self.assertGreater(xtra_header["remote_node"], 0)
                self.assertGreater(xtra_header["remote_port"], 0)

                xEntry = lastEntries[5 * i + 2]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_EPR)
                xEntry = lastEntries[5 * i + 3]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_EPR)
                xEntry = lastEntries[5 * i + 4]
                x_cmd_cmd_header = xEntry["cmd_header"]  # H Header
                self.assertEqual(x_cmd_cmd_header["instruction"], 0)
                id1 = x_cmd_cmd_header["qubit_id"]

                # Let's see the qubit id is in agreement with the received ones
                self.assertEqual(id1, curID[i])

                xEntry = lastEntries[5 * i + 5]
                x_cmd_cmd_header = xEntry["cmd_header"]  # CNOT Header
                self.assertEqual(x_cmd_cmd_header["instruction"], 0)
                self.assertEqual(id1, x_cmd_cmd_header["qubit_id"])
                self.assertEqual(id1 + 1, xEntry["xtra_header"]["qubit_id"])

    def testFactoryEPR_RECV(self):
        with CQCConnection("Alice", appID=1) as alice:

            alice.set_pending(True)
            alice.recvEPR()
            qubits = alice.flush_factory(10, do_sequence=False)
            alice.set_pending(False)

            curID = qubits[0]._qID
            for q in qubits[1:]:
                self.assertEqual(q._qID, curID + 1)
                curID = q._qID

            lastEntries = get_last_entries(11)
            factoryEntry = lastEntries[0]
            self.assertEqual(factoryEntry["node_name"], "Alice")
            factory_cqc_header = factoryEntry["cqc_header"]
            self.assertEqual(factory_cqc_header["type"], CQC_TP_FACTORY)
            expected_length = CQCFactoryHeader.HDR_LENGTH + CQC_CMD_HDR_LENGTH
            self.assertEqual(factory_cqc_header["header_length"], expected_length)
            self.assertEqual(factoryEntry["factory_iterations"], 10)

            for i in range(1, 11):
                xEntry = lastEntries[i]
                x_cmd_cmd_header = xEntry["cmd_header"]
                self.assertEqual(x_cmd_cmd_header["instruction"], CQC_CMD_EPR_RECV)

    def testAllocate0(self):
        with CQCConnection("Alice", appID=1) as alice:
            qubits = alice.allocate_qubits(0)

            self.assertEqual(qubits, [])

            entry = get_last_entries(1)[0]
            self.assertEqual(entry["node_name"], "Alice")
            cqc_hdr = entry["cqc_header"]
            self.assertEqual(cqc_hdr["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_hdr["header_length"], CQCCmdHeader.HDR_LENGTH)

            cmd_hdr = entry["cmd_header"]
            self.assertEqual(cmd_hdr["instruction"], CQC_CMD_ALLOCATE)
            self.assertEqual(cmd_hdr["qubit_id"], 0)

    def testAllocate10(self):
        with CQCConnection("Alice", appID=1) as alice:
            qubits = alice.allocate_qubits(10)

            self.assertEqual(len(qubits), 10)

            curID = qubits[0]._qID
            for q in qubits[1:]:
                self.assertTrue(q._active)
                self.assertEqual(q._qID, curID + 1)
                curID = q._qID

            entry = get_last_entries(1)[0]
            self.assertEqual(entry["node_name"], "Alice")
            cqc_hdr = entry["cqc_header"]
            self.assertEqual(cqc_hdr["type"], CQC_TP_COMMAND)
            self.assertEqual(cqc_hdr["header_length"], CQCCmdHeader.HDR_LENGTH)

            cmd_hdr = entry["cmd_header"]
            self.assertEqual(cmd_hdr["instruction"], CQC_CMD_ALLOCATE)
            self.assertEqual(cmd_hdr["qubit_id"], 10)

    def testRelease(self):
        with CQCConnection("Alice", appID=1) as alice:
            qubits = alice.allocate_qubits(10)
            alice.release_qubits(qubits)

            for q in qubits:
                self.assertFalse(q._active)

            entries = get_last_entries(10)
            for i in range(10):
                entry = entries[i]
                self.assertEqual(entry["node_name"], "Alice")
                cqc_hdr = entry["cqc_header"]
                self.assertEqual(cqc_hdr["type"], CQC_TP_COMMAND)
                self.assertEqual(cqc_hdr["header_length"], 10 * CQCCmdHeader.HDR_LENGTH)

                cmd_hdr = entry["cmd_header"]
                self.assertEqual(cmd_hdr["instruction"], CQC_CMD_RELEASE)
                self.assertEqual(cmd_hdr["qubit_id"], qubits[i]._qID)

    def testReleaseWhenAlreadyReleased(self):
        with CQCConnection("Alice", appID=1) as alice:
            qubits = alice.allocate_qubits(10)
            qubits[0].measure()
            with self.assertRaises(QubitNotActiveError):
                alice.release_qubits(qubits)
            self.assertTrue(qubits[1]._active)


if __name__ == "__main__":
    unittest.main()

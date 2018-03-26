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

from SimulaQron.cqc.backend.cqcLogMessageHandler import CQCLogMessageHandler
from SimulaQron.cqc.pythonLib.cqc import *


def get_last_entries(amount):
	file = "{}/logFileAlice.json".format(CQCLogMessageHandler.dir_path)
	with open(file, 'r') as outfile:
		logData = json.load(outfile)
	return logData[-amount:]


class CQCMessageTest(unittest.TestCase):
	# Only tests cqc_commands at the moment.
	# So no messages that are send back (notifications)

	_alice = None

	@classmethod
	def setUpClass(cls):
		try:
			os.remove("{}/logFileAlice.json".format(CQCLogMessageHandler.dir_path))
			os.remove("{}/logFileBob.json".format(CQCLogMessageHandler.dir_path))

		except OSError:
			pass

	@classmethod
	def tearDownClass(cls):
		try:
			os.remove("{}/logFileAlice.json".format(CQCLogMessageHandler.dir_path))
			os.remove("{}/logFileBob.json".format(CQCLogMessageHandler.dir_path))
		except OSError:
			pass


	def tearDown(self):
		self._alice.close()

	def setUp(self):
		self._alice = CQCConnection("Alice", appID=1)

	# def testNewQubit(self):
	# 	qubit(self._alice, block=False, notify=False, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_NEW)
	# 	self.assertEqual(cmd_header['block'], False)
	# 	self.assertEqual(cmd_header['notify'], False)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testI(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.I(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_I)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testX(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.X(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_X)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testY(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.Y(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_Y)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testZ(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.Z(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_Z)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testH(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.H(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_H)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testT(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.T(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_T)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testK(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.K(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_K)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testRotX(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.rot_X(200, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_ROT_X)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	xtra_header = lastEntry['xtra_header']
	# 	self.assertEqual(xtra_header['step'], 200)
	#
	# def testRotY(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.rot_Y(200, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_ROT_Y)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	xtra_header = lastEntry['xtra_header']
	# 	self.assertEqual(xtra_header['step'], 200)
	#
	# def testRotZ(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q1.rot_Z(200, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_ROT_Z)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	xtra_header = lastEntry['xtra_header']
	# 	self.assertEqual(xtra_header['step'], 200)
	#
	# def testRotXFail(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	with self.assertRaises(struct.error):
	# 		q1.rot_X(256, print_info=False)
	#
	# def testRotXFailNone(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	with self.assertRaises(struct.error):
	# 		q1.rot_X(None, print_info=False)
	#
	# def testRotXFailNaN(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	with self.assertRaises(struct.error):
	# 		q1.rot_X("four", print_info=False)
	#
	# def testRotXFailNegative(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	with self.assertRaises(struct.error):
	# 		q1.rot_X(-1, print_info=False)
	#
	# def testRotXFailFloat(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	with self.assertRaises(struct.error):
	# 		q1.rot_X(1.1, print_info=False)
	#
	# def testCNot(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q2 = qubit(self._alice, print_info=False)
	# 	q1.cnot(q2, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_CNOT)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	xtra_header = lastEntry['xtra_header']
	# 	self.assertEqual(xtra_header['step'], 0)
	# 	self.assertEqual(xtra_header['qubit_id'], cmd_header['qubit_id']+1)
	#
	# def testCNotRemote(self):
	# 	# The appId in xtra_header['app_id'] is not 2 when testing.
	# 	# In fact, doing this code in a real application result in an error as of 2018-03-12
	# 	bob = CQCConnection("Bob", appID=2)
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q2 = qubit(bob, print_info=False)
	# 	q1.cnot(q2, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_CNOT)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	xtra_header = lastEntry['xtra_header']
	# 	self.assertEqual(xtra_header['step'], 0)
	# 	bob.close()
	#
	# def testCPhase(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q2 = qubit(self._alice, print_info=False)
	# 	q1.cphase(q2, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_CPHASE)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	xtra_header = lastEntry['xtra_header']
	# 	self.assertEqual(xtra_header['step'], 0)
	# 	self.assertEqual(xtra_header['qubit_id'], cmd_header['qubit_id']+1)
	#
	# def testSend(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	bob = CQCConnection("Bob", appID=2)
	# 	self._alice.sendQubit(q1, "Bob", remote_appID=2, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_SEND)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	xtra_header = lastEntry['xtra_header']
	# 	self.assertEqual(xtra_header['step'], 0)
	# 	self.assertEqual(xtra_header['remote_app_id'], 2)
	# 	bob.close()
	#
	# def testSendSelf(self):
	# 	# Should not work in a real application
	# 	q1 = qubit(self._alice, print_info=False)
	# 	self._alice.sendQubit(q1, "Alice", remote_appID=1, print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_SEND)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	xtra_header = lastEntry['xtra_header']
	# 	self.assertEqual(xtra_header['step'], 0)
	# 	self.assertEqual(xtra_header['remote_app_id'], 1)
	#
	# def testRecv(self):
	# 	self._alice.recvQubit(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_RECV)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testEPRSend(self):
	# 	bob = CQCConnection("Bob")
	# 	self._alice.createEPR("Bob", remote_appID=2, print_info=False)
	#
	# 	entries = get_last_entries(5)
	#
	# 	cmd_header_epr = entries[0]['cmd_header']
	# 	self.assertEqual(cmd_header_epr['instruction'], CQC_CMD_EPR)
	# 	self.assertEqual(cmd_header_epr['block'], True)
	# 	self.assertEqual(cmd_header_epr['notify'], True)
	# 	cqc_header_epr = entries[0]['cqc_header']
	# 	self.assertEqual(cqc_header_epr['type'], CQC_TP_COMMAND)
	# 	for i in range(5):
	# 		self.assertEqual(entries[i]['cqc_header']['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	self.assertEqual(cqc_header_epr['app_id'], 1)
	# 	xtra_header_epr = entries[0]['xtra_header']
	# 	self.assertEqual(xtra_header_epr['step'], 0)
	# 	self.assertEqual(xtra_header_epr['remote_app_id'], 2)
	#
	# 	# Check if the qubits are created correctly
	# 	# The protocol already knows what do to on EPR, so no new headers are made,
	# 	# This means that the header of createEPR() is send into new(),
	# 	# New headers have to be made for H() and CNOT() for the qubit ids,
	# 	# but the instruction is not needed, defaults to 0
	# 	self.assertEqual(entries[1]['cmd_header']['instruction'], CQC_CMD_EPR)
	# 	self.assertEqual(entries[3]['cmd_header']['instruction'], 0)
	# 	self.assertEqual(entries[4]['cmd_header']['instruction'], 0)
	# 	self.assertEqual(entries[4]['cmd_header']['qubit_id']+1, entries[4]['xtra_header']['qubit_id'])
	#
	# 	bob.close()
	#
	# def testEPRRecv(self):
	# 	self._alice.recvEPR(print_info=False)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_EPR_RECV)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], True)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	#
	# def testMeasure(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	m1 = q1.measure(print_info=False)
	# 	# We've set that for this testing purposes, the measurement outcome is
	# 	# always 2
	# 	self.assertEqual(m1, 2)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_MEASURE)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], False)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	self.assertFalse(q1._active)
	#
	# def testMeasureInplace(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	m1 = q1.measure(inplace=True, print_info=False)
	# 	# We've set that for this testing purposes, the measurement outcome is
	# 	# always 2
	# 	self.assertEqual(m1, 2)
	# 	lastEntry = get_last_entries(1)[0]
	# 	cmd_header = lastEntry['cmd_header']
	# 	self.assertEqual(cmd_header['instruction'], CQC_CMD_MEASURE_INPLACE)
	# 	self.assertEqual(cmd_header['block'], True)
	# 	self.assertEqual(cmd_header['notify'], False)
	# 	cqc_header = lastEntry['cqc_header']
	# 	self.assertEqual(cqc_header['type'], CQC_TP_COMMAND)
	# 	self.assertEqual(cqc_header['header_length'], CQC_CMD_HDR_LENGTH)
	# 	self.assertEqual(cqc_header['app_id'], 1)
	# 	self.assertTrue(q1._active)
	#
	# def testFactoryZero(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	self._alice.sendFactory(q1._qID, CQC_CMD_X, 0)
	# 	m1 = q1.measure(inplace=True, print_info=False)
	#
	# 	# Checking the factory and the measure, factory should not log any commands
	# 	lastEntries = get_last_entries(2)
	# 	factoryEntry = lastEntries[0]
	# 	factory_cmd_header = factoryEntry['cmd_header']
	# 	self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_X)
	# 	self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
	# 	factory_cqc_header = factoryEntry['cqc_header']
	# 	self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
	# 	self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH+CQC_CMD_XTRA_LENGTH)
	# 	x = factoryEntry['xtra_header']
	# 	self.assertEqual(x['step'], 0)
	#
	# 	measureEntry = lastEntries[1]
	# 	self.assertEqual(measureEntry['cmd_header']['instruction'], CQC_CMD_MEASURE_INPLACE)
	# 	self.assertEqual(measureEntry['cmd_header']['qubit_id'], q1._qID)
	#
	# 	q1.measure(print_info=False)
	#
	#
	# def testFactoryOnce(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	self._alice.sendFactory(q1._qID, CQC_CMD_X, 1)
	# 	m1 = q1.measure(inplace=True, print_info=False)
	#
	# 	# Checking the factory and the measure, factory should not log any commands
	# 	lastEntries = get_last_entries(3)
	# 	factoryEntry = lastEntries[0]
	# 	factory_cmd_header = factoryEntry['cmd_header']
	# 	self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_X)
	# 	self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
	# 	factory_cqc_header = factoryEntry['cqc_header']
	# 	self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
	# 	self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	factory_xtra_header = factoryEntry['xtra_header']
	# 	self.assertEqual(factory_xtra_header['step'], 1)
	#
	# 	xEntry = lastEntries[1]
	# 	x_cmd_cmd_header = xEntry['cmd_header']
	# 	self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_X)
	# 	self.assertEqual(x_cmd_cmd_header['qubit_id'], q1._qID)
	# 	# cqc header is the same as the first.
	#
	# 	measureEntry = lastEntries[2]
	# 	self.assertEqual(measureEntry['cmd_header']['instruction'], CQC_CMD_MEASURE_INPLACE)
	# 	self.assertEqual(measureEntry['cmd_header']['qubit_id'], q1._qID)
	#
	#
	#
	# def testFactoryN(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	self._alice.sendFactory(q1._qID, CQC_CMD_X, 10)
	# 	m1 = q1.measure(inplace=True, print_info=False)
	#
	# 	# Checking the factory and the measure, factory should not log any commands
	# 	lastEntries = get_last_entries(12)
	# 	factoryEntry = lastEntries[0]
	# 	factory_cmd_header = factoryEntry['cmd_header']
	# 	self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_X)
	# 	self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
	# 	factory_cqc_header = factoryEntry['cqc_header']
	# 	self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
	# 	self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	factory_xtra_header = factoryEntry['xtra_header']
	# 	self.assertEqual(factory_xtra_header['step'], 10)
	#
	# 	for i in range(1, 11):
	# 		xEntry = lastEntries[i]
	# 		x_cmd_cmd_header = xEntry['cmd_header']
	# 		self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_X)
	# 		self.assertEqual(x_cmd_cmd_header['qubit_id'], q1._qID)
	# 	# cqc header is the same as the first.
	#
	# 	measureEntry = lastEntries[11]
	# 	self.assertEqual(measureEntry['cmd_header']['instruction'], CQC_CMD_MEASURE_INPLACE)
	# 	self.assertEqual(measureEntry['cmd_header']['qubit_id'], q1._qID)
	#
	#
	# def testFactoryCNOTFalse(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q2 = qubit(self._alice, print_info=False)
	# 	with self.assertRaises(CQCUnsuppError):
	# 		self._alice.sendFactory(q1._qID, CQC_CMD_CNOT, 10)
	#
	# def testFactoryCNOT(self):
	# 	q1 = qubit(self._alice, print_info=False)
	# 	q2 = qubit(self._alice, print_info=False)
	# 	self._alice.sendFactory(q1._qID, CQC_CMD_CNOT, 10, xtra_qID=q2._qID)
	#
	# 	entries = get_last_entries(11)
	# 	factoryEntry = entries[0]
	# 	factory_cmd_header = factoryEntry['cmd_header']
	# 	self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_CNOT)
	# 	self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
	# 	factory_cqc_header = factoryEntry['cqc_header']
	# 	self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
	# 	self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	factory_xtra_header = factoryEntry['xtra_header']
	# 	self.assertEqual(factory_xtra_header['step'], 10)
	# 	self.assertEqual(factory_xtra_header['qubit_id'], q2._qID)
	#
	# 	for i in range(1, 11):
	# 		xEntry = entries[i]
	# 		x_cmd_cmd_header = xEntry['cmd_header']
	# 		self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_CNOT)
	# 		self.assertEqual(x_cmd_cmd_header['qubit_id'], q1._qID)
	# 		x = xEntry['xtra_header']
	# 		self.assertEqual(x['qubit_id'], q2._qID)
	#
	# def testFactoryROTX(self):
	# 	# Issue with this is that the angle of rotation (up to a factor) is
	# 	# equal to the amount of calls to this rotation
	# 	# So if the extra parameter is x, the rotation done is x*(x*tau/256)
	# 	q1 = qubit(self._alice, print_info=False)
	# 	self._alice.sendFactory(q1._qID, CQC_CMD_ROT_X, 10)
	# 	m1 = q1.measure(inplace=True, print_info=False)
	#
	# 	# Checking the factory and the measure, factory should not log any commands
	# 	lastEntries = get_last_entries(12)
	# 	factoryEntry = lastEntries[0]
	# 	factory_cmd_header = factoryEntry['cmd_header']
	# 	self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_ROT_X)
	# 	self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
	# 	factory_cqc_header = factoryEntry['cqc_header']
	# 	self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
	# 	self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
	# 	factory_xtra_header = factoryEntry['xtra_header']
	# 	self.assertEqual(factory_xtra_header['step'], 10)
	#
	# 	for i in range(1, 11):
	# 		xEntry = lastEntries[i]
	# 		x_cmd_cmd_header = xEntry['cmd_header']
	# 		self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_ROT_X)
	# 		self.assertEqual(x_cmd_cmd_header['qubit_id'], q1._qID)
	# 	# cqc header is the same as the first.
	#
	# 	measureEntry = lastEntries[11]
	# 	self.assertEqual(measureEntry['cmd_header']['instruction'], CQC_CMD_MEASURE_INPLACE)
	# 	self.assertEqual(measureEntry['cmd_header']['qubit_id'], q1._qID)
	#
	def testFactoryNew(self):
		# Should return a list of qubits with consecutive qubit ids
		qubits = self._alice.sendFactory(2, CQC_CMD_NEW, 10)
		# Checking the factory and the measure, factory should not log any commands
		lastEntries = get_last_entries(11)
		factoryEntry = lastEntries[0]
		factory_cmd_header = factoryEntry['cmd_header']
		self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_NEW)
		self.assertEqual(factory_cmd_header['qubit_id'], 2)
		factory_cqc_header = factoryEntry['cqc_header']
		self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
		self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
		factory_xtra_header = factoryEntry['xtra_header']
		self.assertEqual(factory_xtra_header['step'], 10)

		for i in range(1, 11):
			xEntry = lastEntries[i]
			x_cmd_cmd_header = xEntry['cmd_header']
			self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_NEW)
			self.assertEqual(x_cmd_cmd_header['qubit_id'], 2)  # This id does not matter


		curID = qubits[0]._qID
		for q in qubits[1:]:
			self.assertEqual(q._qID, curID + 1)
			curID = q._qID

	def testFactoryMeasure(self):
		q1 = qubit(self._alice, print_info=False)
		measurements = self._alice.sendFactory(q1._qID, CQC_CMD_MEASURE, 10)
		# All measurements should be equal to 2
		self.assertTrue(all(x == 2 for x in measurements))

		lastEntries = get_last_entries(11)
		factoryEntry = lastEntries[0]
		factory_cmd_header = factoryEntry['cmd_header']
		self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_MEASURE)
		self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
		factory_cqc_header = factoryEntry['cqc_header']
		self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
		self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
		factory_xtra_header = factoryEntry['xtra_header']
		self.assertEqual(factory_xtra_header['step'], 10)

		for i in range(1, 11):
			xEntry = lastEntries[i]
			x_cmd_cmd_header = xEntry['cmd_header']
			self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_MEASURE)

	def testFactoryMeasureInplace(self):
		# should give the same results as inplace = false
		q1 = qubit(self._alice, print_info=False)
		measurements = self._alice.sendFactory(q1._qID, CQC_CMD_MEASURE_INPLACE, 10)
		# All measurements should be equal to 2
		self.assertTrue(all(x == 2 for x in measurements))

		lastEntries = get_last_entries(11)
		factoryEntry = lastEntries[0]
		factory_cmd_header = factoryEntry['cmd_header']
		self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_MEASURE_INPLACE)
		self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
		factory_cqc_header = factoryEntry['cqc_header']
		self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
		self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
		factory_xtra_header = factoryEntry['xtra_header']
		self.assertEqual(factory_xtra_header['step'], 10)

		for i in range(1, 11):
			xEntry = lastEntries[i]
			x_cmd_cmd_header = xEntry['cmd_header']
			self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_MEASURE_INPLACE)

	def testFactoryReset(self):

		q1 = qubit(self._alice, print_info=False)
		res = self._alice.sendFactory(q1._qID, CQC_CMD_RESET, 10)

		self.assertListEqual(res, [])

		lastEntries = get_last_entries(11)
		factoryEntry = lastEntries[0]
		factory_cmd_header = factoryEntry['cmd_header']
		self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_RESET)
		self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
		factory_cqc_header = factoryEntry['cqc_header']
		self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
		self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
		factory_xtra_header = factoryEntry['xtra_header']
		self.assertEqual(factory_xtra_header['step'], 10)

		for i in range(1, 11):
			xEntry = lastEntries[i]
			x_cmd_cmd_header = xEntry['cmd_header']
			self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_RESET)

	def testFactorySend(self):

		q1 = qubit(self._alice, print_info=False)
		res = self._alice.sendFactory(q1._qID, CQC_CMD_SEND, 10)

		self.assertListEqual(res, [])

		lastEntries = get_last_entries(11)
		factoryEntry = lastEntries[0]
		factory_cmd_header = factoryEntry['cmd_header']
		self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_SEND)
		self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
		factory_cqc_header = factoryEntry['cqc_header']
		self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
		self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
		factory_xtra_header = factoryEntry['xtra_header']
		self.assertEqual(factory_xtra_header['step'], 10)

		for i in range(1, 11):
			xEntry = lastEntries[i]
			x_cmd_cmd_header = xEntry['cmd_header']
			self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_SEND)

	def testFactoryRecv(self):

		q1 = qubit(self._alice, print_info=False)
		qubits = self._alice.sendFactory(q1._qID, CQC_CMD_RECV, 10)

		curID = qubits[0]._qID
		for q in qubits[1:]:
			self.assertEqual(q._qID, curID + 1)
			curID = q._qID

		lastEntries = get_last_entries(11)
		factoryEntry = lastEntries[0]
		factory_cmd_header = factoryEntry['cmd_header']
		self.assertEqual(factory_cmd_header['instruction'], CQC_CMD_RECV)
		self.assertEqual(factory_cmd_header['qubit_id'], q1._qID)
		factory_cqc_header = factoryEntry['cqc_header']
		self.assertEqual(factory_cqc_header['type'], CQC_TP_FACTORY)
		self.assertEqual(factory_cqc_header['header_length'], CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH)
		factory_xtra_header = factoryEntry['xtra_header']
		self.assertEqual(factory_xtra_header['step'], 10)

		for i in range(1, 11):
			xEntry = lastEntries[i]
			x_cmd_cmd_header = xEntry['cmd_header']
			self.assertEqual(x_cmd_cmd_header['instruction'], CQC_CMD_RECV)




if __name__ == '__main__':
	unittest.main()

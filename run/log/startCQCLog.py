import logging
import os
import sys

import re
from SimulaQron.settings import Settings
from SimulaQron.general.hostConfig import networkConfig
from SimulaQron.cqc.backend.cqcProtocol import CQCFactory, reactor
from SimulaQron.cqc.backend.cqcLogMessageHandler import CQCLogMessageHandler
from twisted.internet.error import ConnectionRefusedError, CannotListenError


def setup_CQC_server(names, hosts, factories):
	logging.debug("LOCAL: Starting CQC Log server.")
	for myName in names:
		cqc_factory = factories[myName]
		myHost = hosts[myName]
		try:
			logging.debug("LOCAL %s: Starting local classical communication server.", myName)
			myHost = cqc_factory.host
			myHost.root = cqc_factory
			myHost.factory = cqc_factory
			reactor.listenTCP(myHost.port, myHost.factory)
		except CannotListenError as e:
			logging.error("LOCAL {}: CQC server address ({}) is already in use.".format(myName, myHost.port))
			reactor.stop()
		except Exception as e:
			logging.error("LOCAL {}: Critical error when starting CQC server: {}".format(myName, e))
			reactor.stop()


	pass


def main(names):
	# This file defines the network of CQC servers interfacing to virtual quantum nodes
	cqcFile = Settings.CONF_CQCNODES_FILE

	# Read configuration files for the virtual quantum, as well as the classical network
	cqcNet = networkConfig(cqcFile)

	# Check if we are in the host-dictionary
	myHosts = {}
	cqc_factories = {}
	for myName in names:
		if myName in cqcNet.hostDict:
			myHosts[myName] = cqcNet.hostDict[myName]
			cqc_factories[myName] = CQCFactory(myHosts[myName], myName, cqcNet, CQCLogMessageHandler)
		else:
			logging.error("LOCAL %s: Cannot start classical communication servers.", myName)
			return

	setup_CQC_server(names, myHosts, cqc_factories)

	# Run reactor
	reactor.run()


##################################################################################################
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=Settings.CONF_LOGGING_LEVEL_BACKEND)


names = sys.argv[1:]
if not names:
	nodeFile = Settings.CONF_NODES_FILE
	with open(nodeFile) as file:
		for line in file:
			if line:
				names.append(re.sub('[^0-9a-zA-Z_\-]+', '', line))

main(names)


import sys
import os

from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList, Deferred

from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcProtocol import *

from qutip import *

import logging
import time

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

##################################################################################################
#
# init_register
#
# Called if all servers are started and all connections are made. Retrieves the relevant
# root objects to talk to such remote connections
#

def init_register(resList, myName, lNode):

	logging.debug("LOCAL %s: All connections set up.", myName)

 	# Retrieve the connection to the local virtual node, if successfull
	j = 0
	if resList[j][0]:
		virtRoot = resList[j][1]
		lNode.set_virtual_node(virtRoot)
	else:
		logging.error("LOCAL %s: Connection to virtual server failed!",myName)
		reactor.stop()

	# On the local virtual node, we still want to initialize a qubit register
	defer = virtRoot.callRemote("new_register")
	defer.addCallback(fill_register, myName, lNode, virtRoot)
	defer.addErrback(localError)

def fill_register(obj, myName, lNode, virtRoot):
	logging.debug("LOCAL %s: Created quantum register at virtual node.",myName)
	qReg = obj

	# Record the handle to the local virtual register
	lNode.set_virtual_reg(qReg)

def localError(reason):
	'''
	Error handling for the connection.
	'''
	print("Critical error: ",reason)
	reactor.stop()

#####################################################################################################
#
# main
#
# Start the indicated backend CQC Server
#

def main(myName):

	# This file defines the network of virtual quantum nodes
	virtualFile = os.environ.get('NETSIM') + "/config/virtualNodes.cfg"

	# This file defines the network of CQC servers interfacing to virtual quantum nodes
	cqcFile = os.environ.get('NETSIM') + "/config/cqcNodes.cfg"

	# Read configuration files for the virtual quantum, as well as the classical network
	virtualNet = networkConfig(virtualFile)
	cqcNet = networkConfig(cqcFile)

	# Check if we should run a local classical server. If so, initialize the code
	# to handle remote connections on the classical communication network
	if myName in cqcNet.hostDict:
		myHost = cqcNet.hostDict[myName]
		cqc_factory = CQCFactory(myHost)
	else:
		logging.error("LOCAL %s: Cannot start classical communication servers.",myName,e.strerror)

	# Initialize Twisted callback framework
	dList = []

	try:
		logging.debug("LOCAL %s: Starting local classical communication server.",myName)
		myHost.root = cqc_factory
		myHost.factory = cqc_factory
		reactor.listenTCP(myHost.port, myHost.factory)
	except Exception as e:
		logging.error("LOCAL %s: Cannot start CQC server.",myName,e.strerror)
		return

	# Connect to the local virtual node simulating the "local" qubits
	try:
		logging.debug("LOCAL %s: Connecting to local virtual node.",myName)
		virtual_node = virtualNet.hostDict[myName]
		factory = pb.PBClientFactory()
		reactor.connectTCP(virtual_node.hostname, virtual_node.port, factory)
		deferVirtual = factory.getRootObject()
		dList.append(deferVirtual)

		deferList = DeferredList(dList, consumeErrors=True)
		deferList.addCallback(init_register, myName, cqc_factory)
		deferList.addErrback(localError)
		reactor.run()
	except Exception as e:
		logging.error("LOCAL %s: Cannot connect to SimulaQron backend.",myName)
		return


##################################################################################################
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)
main(sys.argv[1])


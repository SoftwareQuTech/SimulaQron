import logging
import os
import sys

from simulaqron.settings import Settings
from simulaqron.general.hostConfig import networkConfig
from cqc.backend.cqcProtocol import CQCFactory
from cqc.backend.cqcLogMessageHandler import CQCLogMessageHandler
from simulaqron.toolbox import get_simulaqron_path
from twisted.internet.error import CannotListenError
from twisted.internet import reactor


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
        except CannotListenError:
            logging.error("LOCAL {}: CQC server address ({}) is already in use.".format(myName, myHost.port))
            reactor.stop()
        except Exception as e:
            logging.error("LOCAL {}: Critical error when starting CQC server: {}".format(myName, e))
            reactor.stop()

    pass


def main(names):
    # Get path to SimulaQron folder
    simulaqron_path = get_simulaqron_path.main()

    # This file defines the network of CQC servers interfacing to virtual quantum nodes
    cqcFile = os.path.join(simulaqron_path, "config/cqcNodes.cfg")

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
logging.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s", level=Settings.CONF_LOGGING_LEVEL_BACKEND)


names = sys.argv[1:]

main(names)

#!/usr/bin/env python
import logging
import os
import sys

import re
from SimulaQron.settings import Settings
from SimulaQron.general.hostConfig import networkConfig
from SimulaQron.cqc.backend.cqcProtocol import CQCFactory
from twisted.internet import reactor
from SimulaQron.cqc.backend.cqcLogMessageHandler import CQCLogMessageHandler
from twisted.internet.error import ConnectionRefusedError, CannotListenError


def setup_CQC_server(name, cqc_factory):
    """Setup CQC server to handle remote on the classical communication network."""
    try:
        logging.debug(
            "LOCAL %s: Starting local classical communication server.", name
        )
        myHost = cqc_factory.host
        myHost.root = cqc_factory
        myHost.factory = cqc_factory
        reactor.listenTCP(myHost.port, myHost.factory)
    except CannotListenError as e:
        logging.error(
            "LOCAL {}: CQC server address ({}) is already in use.".format(
                name, myHost.port
            )
        )
        reactor.stop()
    except Exception as e:
        logging.error(
            "LOCAL {}: Critical error when starting CQC server: {}".format(name, e)
        )
        reactor.stop()


def main(name, run_reactor=True):
    # This file defines the network of CQC servers interfacing to virtual quantum nodes
    cqcFile = os.environ.get("NETSIM") + "/config/cqcNodes.cfg"

    # Read configuration files for the virtual quantum, as well as the classical network
    cqcNet = networkConfig(cqcFile)

    # Check if we are in the host-dictionary
    if name in cqcNet.hostDict:
        host = cqcNet.hostDict[name]
        cqc_factory = CQCFactory(host, name, cqcNet, CQCLogMessageHandler)
    else:
        logging.error(
            "LOCAL %s: Cannot start classical communication servers.", name
        )
        return

    setup_CQC_server(name, cqc_factory)

    # Run reactor
    if run_reactor:
        reactor.run()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s",
        level=Settings.CONF_LOGGING_LEVEL_BACKEND,
    )
    names = sys.argv[1:]
    if not names:
        nodeFile = os.environ.get("NETSIM") + "/config/Nodes.cfg"
        with open(nodeFile) as file:
            for line in file:
                if line:
                    names.append(re.sub("[^0-9a-zA-Z_\-]+", "", line))

    for name in names:
        main(name, run_reactor=False)
    reactor.run()

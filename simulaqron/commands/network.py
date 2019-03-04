import os
import click
import logging

from simulaqron.settings import Settings
from simulaqron.network import Network


_common_options = [
    click.option(
        "-N",
        "--nrnodes",
        help="Number of nodes to start \n(WARNING: overwites existing config files)",
        type=click.INT,
        default=None,
    ),
    click.option(
        "-n",
        "--nodes",
        help="Comma separated list of nodes to start \n(WARNING: overwites existing config files)",
        type=click.STRING,
        default=None,
    ),
    click.option(
        "-t",
        "--topology",
        help="Topology of network \n(WARNING: overwites existing config files)",
        type=click.STRING,
        default=None,
    ),
]


def common_options(func):
    """Decorator to add all common options to a click command"""
    for option in reversed(_common_options):
        func = option(func)
    return func


@click.group()
def network():
    """Commands for managing SimulaQron networks."""
    pass


@network.command()
@common_options
def start_all(nrnodes, nodes, topology, print_process_info=True):
    """Starts all nodes defined in netsim's config directory."""
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s",
        level=Settings.CONF_LOGGING_LEVEL_BACKEND,
    )
    logger = logging.getLogger(__name__)

    if nrnodes or nodes or topology:
        if nodes:
            nodes = nodes.split(",")
        else:
            nodes = []

        if nrnodes and (nrnodes > len(nodes)):
            nodes += ["Node{}".format(i) for i in range(nrnodes - len(nodes))]

    network = Network(nodes=nodes, topology=topology)
    network.start()

    if print_process_info:
        to_print = "--------------------------------------------------\n"
        to_print += "| Network is now running with process ID {: <5}.  |\n".format(os.getpid())
        to_print += "| If the process is running in the foreground,   |\n"
        to_print += "| press any button to kill the network or press  |\n"
        to_print += "| CTRL-Z to put the process in the background.   |\n"
        to_print += "| If the process is running in the background,   |\n"
        to_print += "| type e.g. 'kill -9 {: <5}' to kill the network. |\n".format(os.getpid())
        to_print += "--------------------------------------------------\n"
    else:
        to_print = ""
    input(to_print)

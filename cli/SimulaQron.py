#!/usr/bin/env python3
import os
import click
import logging

from simulaqron.network import Network
from simulaqron.settings import Settings

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """Command line interface for interacting with SimulaQron."""
    pass

#################
# start command #
#################


@cli.command()
@click.option(
    "-N",
    "--nrnodes",
    help="Number of nodes to start \n(WARNING: overwites existing config files)",
    type=click.INT,
    default=None,
)
@click.option(
    "-n",
    "--nodes",
    help="Comma separated list of nodes to start \n(WARNING: overwites existing config files)",
    type=click.STRING,
    default=None,
)
@click.option(
    "-t",
    "--topology",
    help="Topology of network \n(WARNING: overwites existing config files)",
    type=click.STRING,
    default=None,
)
@click.option(
    "-q",
    "--quiet",
    help="No output, except warnings and errors.",
    is_flag=True,
)
@click.option(
    "-v",
    "--verbose",
    help="Print debug output (overrides the -q flag).",
    is_flag=True,
)
def start(nrnodes, nodes, topology, quiet, verbose):
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

    if verbose:
        Settings.set_setting("BACKEND", "loglevel", "debug")
        Settings.set_setting("FRONTEND", "loglevel", "debug")
    else:
        if quiet:
            Settings.set_setting("BACKEND", "loglevel", "warning")
            Settings.set_setting("FRONTEND", "loglevel", "warning")
        else:
            Settings.set_setting("BACKEND", "loglevel", "info")
            Settings.set_setting("FRONTEND", "loglevel", "info")

    network = Network(nodes=nodes, topology=topology)
    network.start()

    if verbose or (not quiet):
        to_print = "--------------------------------------------------\n"
        to_print += "| Network is now running with process ID {: <5}.  |\n".format(os.getpid())
        to_print += "| If the process is running in the foreground,   |\n"
        to_print += "| press any button to kill the network or press  |\n"
        to_print += "| CTRL-Z to put the process in the background.   |\n"
        to_print += "| If the process is running in the background,   |\n"
        to_print += "| type e.g. 'kill -9 {: <5}' to kill the network. |\n".format(os.getpid())
        to_print += "--------------------------------------------------\n"

        Settings.set_setting("BACKEND", "loglevel", "warning")
        Settings.set_setting("FRONTEND", "loglevel", "warning")
    else:
        to_print = ""
    input(to_print)

###############
# set command #
###############


@cli.group()
def set():
    """Change a setting"""
    pass


@set.command()
def default():
    """Sets all settings back to default"""
    Settings.default_settings()


@set.command()
@click.argument('value', type=click.Choice(["stabilizer", "projectq", "qutip"]))
def backend(value):
    """The backend to use (stabilizer, projectq, qutip)."""
    Settings.set_setting("BACKEND", "backend", value)


@set.command()
@click.argument('value', type=int)
def max_qubits(value):
    """Max virt-qubits per node and max sim-qubits per register."""
    Settings.set_setting("BACKEND", "maxqubits_per_node", str(value))


@set.command()
@click.argument('value', type=int)
def max_registers(value):
    """How many registers a node can hold."""
    Settings.set_setting("BACKEND", "maxregs_per_node", str(value))


@set.command()
@click.argument('value', type=float)
def conn_retry_time(value):
    """If setup fails, how long to wait until a retry."""
    Settings.set_setting("BACKEND", "waittime", str(value))


@set.command()
@click.argument('value', type=click.Choice(["debug", "info", "warning", "error", "critical"]))
def log_level(value):
    """Log level for both backend and frontend."""
    Settings.set_setting("BACKEND", "loglevel", value)
    Settings.set_setting("FRONTEND", "loglevel", value)


@set.command()
@click.argument('value', type=str)
def topology_file(value):
    """The path to the topology file to be used, can be ""."""
    Settings.set_setting("BACKEND", "topology_file", value)


@set.command()
@click.argument('value', type=click.Choice("on", "off"))
def noisy_qubits(value):
    """Whether qubits should be noisy (on/off)"""
    if value == "on":
        Settings.set_setting("BACKEND", "noisy_qubits", 'True')
    else:
        Settings.set_setting("BACKEND", "noisy_qubits", 'False')


@set.command()
@click.argument('value', type=float)
def t1(value):
    """The effective T1 to be used for noisy qubits"""
    Settings.set_setting("BACKEND", "t1", str(value))

###############
# get command #
###############


@cli.group()
def get():
    """Get a setting"""
    pass


@get.command()
def backend():
    """The backend to use (stabilizer, projectq, qutip)."""
    print(Settings.CONF_BACKEND)


@get.command()
def max_qubits():
    """Max virt-qubits per node and max sim-qubits per register."""
    print(Settings.CONF_MAXQUBITS)


@get.command()
def max_registers():
    """How many registers a node can hold."""
    print(Settings.CONF_MAXREGS)


@get.command()
def conn_retry_time():
    """If setup fails, how long to wait until a retry."""
    print(Settings.CONF_WAIT_TIME)


@get.command()
def log_level():
    """Log level for both backend and frontend."""
    print("Backend: {}, Frontend: {}".format(Settings.CONF_LOGGING_LEVEL_BACKEND, Settings.CONF_LOGGING_LEVEL_FRONTEND))


@get.command()
def topology_file():
    """The path to the topology file to be used, can be ""."""
    print(Settings.CONF_TOPOLOGY_FILE)


@get.command()
def noisy_qubits():
    """Whether qubits should be noisy (on/off)"""
    if Settings.CONF_NOISY_QUBITS == 'True':
        print("on")
    else:
        print("off")


@get.command()
def t1():
    """The effective T1 to be used for noisy qubits"""
    print(Settings.CONF_T1)


if __name__ == "__main__":
    cli()


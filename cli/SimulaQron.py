#!/usr/bin/env python3
import os
import time
import click
import logging
from daemons.prefab import run

from simulaqron.network import Network
from simulaqron.settings import Settings

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class SimulaQronDaemon(run.RunDaemon):
    def __init__(self, pidfile, name=None, nrnodes=None, nodes=None, topology=None, quiet=False, verbose=False):
        super().__init__(pidfile=pidfile)
        self.name = name
        self.nrnodes = nrnodes
        self.nodes = nodes
        self.topology = topology
        self.quiet = quiet
        self.verbose = verbose

    def run(self):
        """Starts all nodes defined in netsim's config directory."""

        if self.nrnodes or self.nodes or self.topology:
            if self.nodes:
                nodes = self.nodes.split(",")
            else:
                nodes = []

            if self.nrnodes and (self.nrnodes > len(nodes)):
                nodes += ["Node{}".format(i) for i in range(self.nrnodes - len(nodes))]
        else:
            nodes = self.nodes

        if self.verbose:
            self._set_log_level("debug")
        else:
            if self.quiet:
                self._set_log_level("warning")
            else:
                self._set_log_level("info")

        network = Network(name=self.name, nodes=nodes, topology=self.topology)
        network.start()

        while True:
            time.sleep(0.1)

    @staticmethod
    def _set_log_level(level):
        Settings.set_setting("BACKEND", "loglevel", level)
        Settings.set_setting("FRONTEND", "loglevel", level)

        logging.basicConfig(
            format="%(asctime)s:%(levelname)s:%(message)s",
            level=Settings.log_levels[level],
        )


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """Command line interface for interacting with SimulaQron."""
    pass

#################
# start command #
#################


@cli.command()
@click.option(
    "--name",
    help="Give the network a name to be able to start multiple (default: default)",
    type=click.STRING,
    default=None,
)
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
def start(name, nrnodes, nodes, topology, quiet, verbose):
    """Starts a network with the given parameters or from config files."""
    if name is None:
        name = "default"
    pidfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulaqron_network_{}.pid".format(name))
    if os.path.exists(pidfile):
        logging.warning("Network with name {} is already running".format(name))
        return
    d = SimulaQronDaemon(pidfile=pidfile, name=name, nrnodes=nrnodes, nodes=nodes, topology=topology, quiet=quiet,
                         verbose=verbose)
    d.start()

###############
# stop command #
###############


@cli.command()
@click.option(
    "--name",
    help="Stop the network with then a given name (default: default)",
    type=click.STRING,
    default=None,
)
def stop(name):
    """Stops a network."""
    if name is None:
        name = "default"
    pidfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulaqron_network_{}.pid".format(name))
    if not os.path.exists(pidfile):
        logging.warning("Network with name {} is not running".format(name))
        return
    d = SimulaQronDaemon(pidfile=pidfile)
    d.stop()


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
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s",
        level=Settings.CONF_LOGGING_LEVEL_BACKEND,
    )
    cli()


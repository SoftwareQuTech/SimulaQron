#!/usr/bin/env python3
import os
import time
import click
import logging
from daemons.prefab import run
from daemons.interfaces import exit

import simulaqron
from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings
from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor
from simulaqron.toolbox.reset import main as reset_simulaqron

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
PID_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".simulaqron_pids")

# Check that the default network_config_file exists
default_network_config_file = simulaqron_settings._default_config["network_config_file"]
if not os.path.exists(default_network_config_file):
    networks_config = NetworksConfigConstructor()
    networks_config.reset()
    networks_config.write_to_file(default_network_config_file)


class SimulaQronDaemon(run.RunDaemon):
    def __init__(self, pidfile, name=None, nrnodes=None, nodes=None, topology=None, new=True):
        super().__init__(pidfile=pidfile)
        self.name = name
        self.nrnodes = nrnodes
        self.nodes = nodes
        self.topology = topology
        self.new = new

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

        network = Network(name=self.name, nodes=nodes, topology=self.topology, new=self.new, force=True)
        network.start()

        while True:
            time.sleep(0.1)


def _is_positive_answer(answer):
    """
    Used to check if an answer is positive from a user.
    """
    if answer in ["yes", "y"]:
        return True
    return False


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """Command line interface for interacting with SimulaQron."""
    pass


###########
# version #
###########

@cli.command()
def version():
    """
    Prints the version of simulqron.
    """
    print(simulaqron.__version__)


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
    "-f",
    "--force",
    help="Force re-write of network_config_file.\n"
         "Note used if --keep flag is used.",
    is_flag=True,
)
@click.option(
    "--keep",
    help="If set, the network_config_file won't be changed.\n"
         "This is useful if you wish to start a subset of the nodes in the config "
         "file without changing it.\n"
         "If not set, simulaqron will ask if you really wan't to change the config-file.\n"
         "If you want to supress this question, use the --force/-f flag.",
    is_flag=True,
)
def start(name, nrnodes, nodes, topology, force, keep):
    """Starts a network with the given parameters or from config files."""
    new = not keep
    if name is None:
        name = "default"
    pidfile = os.path.join(PID_FOLDER, "simulaqron_network_{}.pid".format(name))
    if os.path.exists(pidfile):
        logging.warning("Network with name {} is already running".format(name))
        logging.warning("The pidfile for this network is located at {}".format(pidfile))
        return
    if new:
        if not force:
            answer = input("Do you want to add/replace the network '{}' in the file {} "
                           "with a new network? (yes/no)"
                           .format(name, simulaqron_settings.network_config_file))
            if not _is_positive_answer(answer):
                print("Aborted!")
                return
    d = SimulaQronDaemon(pidfile=pidfile, name=name, nrnodes=nrnodes, nodes=nodes, topology=topology, new=new)
    try:
        d.start()
    except SystemExit as e:
        if e.code == exit.PIDFILE_INACCESSIBLE or\
           e.code == exit.DAEMONIZE_FAILED:
            logging.debug("Failed to launch Simulaqron Daemon. "
                          "Exit code reported by daemons: {}".format(e.code))
            print("Failed to launch SimulaQron Daemon. Aborted!")

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
    pidfile = os.path.join(PID_FOLDER, "simulaqron_network_{}.pid".format(name))
    if not os.path.exists(pidfile):
        logging.warning("Network with name {} is not running".format(name))
        return
    d = SimulaQronDaemon(pidfile=pidfile)
    d.stop()

#################
# reset command #
#################


@cli.command()
@click.option(
    "-f",
    "--force",
    help="Don't ask for confirmation.",
    is_flag=True,
)
def reset(force):
    """Resets simulaqron"""
    if not force:
        answer = input("Are you sure you want to reset simulaqron?\nThis will revert settings and "
                       "network config files to the default values.\nNote, this will not edit or remove "
                       "the file at ~/.simulaqron.json if it exists, this you have to do manually if "
                       "you wish to revert all settings.\n"
                       "(yes/no)")
    else:
        answer = "yes"
    if _is_positive_answer(answer):
        for entry in os.listdir(PID_FOLDER):
            if entry.endswith(".pid"):
                pidfile = os.path.join(PID_FOLDER, entry)
                d = SimulaQronDaemon(pidfile=pidfile)
                d.stop()
                if os.path.exists(pidfile):
                    os.remove(pidfile)
        reset_simulaqron()
    else:
        print("Aborting!")


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
    simulaqron_settings.default_settings()


@set.command()
@click.argument('value', type=click.Choice(["stabilizer", "projectq", "qutip"]))
def backend(value):
    """The backend to use (stabilizer, projectq, qutip)."""
    simulaqron_settings.backend = value


@set.command()
@click.argument('value', type=int)
def max_qubits(value):
    """Max virt-qubits per node and max sim-qubits per register."""
    simulaqron_settings.max_qubits = value


@set.command()
@click.argument('value', type=int)
def max_registers(value):
    """How many registers a node can hold."""
    simulaqron_settings.max_registers = value


@set.command()
@click.argument('value', type=float)
def conn_retry_time(value):
    """If setup fails, how long to wait until a retry."""
    simulaqron_settings.conn_retry_time = value


@set.command()
@click.argument('value', type=float)
def recv_timeout(value):
    """When receiving a qubit or EPR pair, how long to wait until raising a timeout."""
    simulaqron_settings.recv_timeout = value


@set.command()
@click.argument('value', type=float)
def recv_retry_time(value):
    """When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."""
    simulaqron_settings.recv_retry_time = value


@set.command()
@click.argument('value', type=int)
def log_level(value):
    """Log level for both backend and frontend\n10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL."""
    simulaqron_settings.log_level = value


@set.command()
@click.argument('value', type=str)
def network_config_file(value):
    """The path to the network_config_file to be used"""
    simulaqron_settings.network_config_file = value


@set.command()
@click.argument('value', type=click.Choice("on", "off"))
def noisy_qubits(value):
    """Whether qubits should be noisy (on/off)"""
    if value == "on":
        simulaqron_settings.noisy_qubits = True
    else:
        simulaqron_settings.noisy_qubits = False


@set.command()
@click.argument('value', type=float)
def t1(value):
    """The effective T1 to be used for noisy qubits"""
    simulaqron_settings.t1 = value

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
    print(simulaqron_settings.backend)


@get.command()
def max_qubits():
    """Max virt-qubits per node and max sim-qubits per register."""
    print(simulaqron_settings.max_qubits)


@get.command()
def max_registers():
    """How many registers a node can hold."""
    print(simulaqron_settings.max_registers)


@get.command()
def conn_retry_time():
    """If setup fails, how long to wait until a retry."""
    print(simulaqron_settings.conn_retry_time)


@get.command()
def recv_timeout():
    """When receiving a qubit or EPR pair, how long to wait until raising a timeout."""
    print(simulaqron_settings.recv_timeout)


@get.command()
def recv_retry_time():
    """When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."""
    print(simulaqron_settings.recv_retry_time)


@get.command()
def log_level():
    """Log level for both backend and frontend."""
    print(simulaqron_settings.log_level)


@get.command()
def network_config_file():
    """The path to the network_config_file to be used"""
    print(simulaqron_settings.network_config_file)


@get.command()
def noisy_qubits():
    """Whether qubits should be noisy (on/off)"""
    if simulaqron_settings.noisy_qubits:
        print("on")
    else:
        print("off")


@get.command()
def t1():
    """The effective T1 to be used for noisy qubits"""
    print(simulaqron_settings.t1)

###############
# node command #
###############


@cli.group()
def nodes():
    """
    Manage the nodes in the simulated network.

    NOTE: This needs to be done before starting the network.
    """
    pass


@nodes.command()
@click.argument('name', type=str)
@click.option('--network-name', type=str,
              help="The name of the network")
@click.option('--hostname', type=str,
              help="The host name of the node, e.g. localhost (default) or 192.168.0.1\n"
                   "If you wish to have different components on different hostname,"
                   "for example the cqc nodes on one computer and the virtual nodes on another,"
                   "you have to manually construct you config file.")
@click.option('--app-port', type=int,
              help="Port number for the application.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--cqc-port', type=int,
              help="Port number for the cqc server.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--vnode-port', type=int,
              help="Port number for the virtual node.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--neighbors', type=str,
              help="The neighbors of the node in the network seperated by ',' (no space).\n \
                    For example '--neighbors Bob,Charlie,David'.\n \
                    If not specified all current nodes in the network will be neighbors.")
@click.option(
    "-f",
    "--force",
    help="Force re-write of network_config_file.\n",
    is_flag=True,
)
def add(name, network_name=None, hostname=None, app_port=None, cqc_port=None, vnode_port=None, neighbors=None,
        force=False):
    """
    Add a node to the network.

    NAME: The name of the node, e.g. Alice

    HOSTNAME: The host name of the node, e.g. localhost or 192.168.0.1
    """
    if not force:
        answer = input("Do you want to add the node {} to the network {} in the file {}? (yes/no)."
                       .format(name, network_name, simulaqron_settings.network_config_file))
        if not _is_positive_answer(answer):
            print("Aborting!")
            return
    if neighbors is not None:
        neighbors = neighbors.split(',')
        neighbors = [neighbor.strip() for neighbor in neighbors]
    networks_config = NetworksConfigConstructor(simulaqron_settings.network_config_file)
    networks_config.add_node(node_name=name, network_name=network_name,
                             app_hostname=hostname, cqc_hostname=hostname, vnode_hostname=hostname,
                             app_port=app_port, cqc_port=cqc_port, vnode_port=vnode_port,
                             neighbors=neighbors)
    networks_config.write_to_file()


@nodes.command()
@click.argument('name', type=str)
@click.option('--network-name', type=str,
              help="The name of the network")
@click.option(
    "-f",
    "--force",
    help="Force re-write of network_config_file.\n",
    is_flag=True,
)
def remove(name, network_name=None, force=False):
    """
    Remove a node to the network.

    NAME: The name of the node, e.g. Alice
    """
    if not force:
        answer = input("Do you want to remove the node {} to the network {} in the file {}? (yes/no)."
                       .format(name, network_name, simulaqron_settings.network_config_file))
        if not _is_positive_answer(answer):
            print("Aborting!")
            return
    networks_config = NetworksConfigConstructor(simulaqron_settings.network_config_file)
    networks_config.remove_node(node_name=name, network_name=network_name)
    networks_config.write_to_file()


@nodes.command()
@click.option('--network-name', type=str,
              help="The name of the network")
@click.option(
    "-f",
    "--force",
    help="Force re-write of network_config_file.\n",
    is_flag=True,
)
def default(network_name=None, force=False):
    """
    Sets the default nodes of the network.

    The default network consists of the five nodes:
    Alice, Bob, Charlie, David, Eve
    """
    if not force:
        answer = input("Do you want to set the network {} in the file {} to default,"
                       "i.e. with nodes Alice, Bob, Charlie, David and Eve? (yes/no)."
                       .format(network_name, simulaqron_settings.network_config_file))
        if not _is_positive_answer(answer):
            print("Aborting!")
            return
    networks_config = NetworksConfigConstructor(simulaqron_settings.network_config_file)
    node_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
    networks_config.add_network(node_names=node_names, network_name=network_name)
    networks_config.write_to_file()


@nodes.command()
@click.option('--network-name', type=str,
              help="The name of the network")
def get(network_name=None):
    """Get the current nodes of the network."""
    networks_config = NetworksConfigConstructor(simulaqron_settings.network_config_file)
    try:
        nodes = networks_config.get_node_names(network_name=network_name)
    except ValueError:
        print("No network {}".format(network_name))
    else:
        print(("{} " * len(nodes))[:-1].format(*nodes))


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s",
        level=simulaqron_settings.log_level,
    )
    cli()

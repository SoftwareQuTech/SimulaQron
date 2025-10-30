#!/usr/bin/env python3
import time
from typing import Optional, Callable

import click
import logging
from daemons.prefab import run
from daemons.interfaces import exit
from pathlib import Path
import importlib.metadata as metadata

from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings
from simulaqron.settings.simulaqron_config import SimBackend, DEFAULT_SIMULAQRON_SETTINGS_FILENAME
from simulaqron.settings.network_config import NetworkConfigBuilder

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
# PID folder should be "LOCAL"
PID_FOLDER = Path.home() /  ".simulaqron_pids"

# If the pid folder does not exist, create it
if not PID_FOLDER.exists():
    Path.mkdir(PID_FOLDER)


class SimulaQronDaemon(run.RunDaemon):
    def __init__(self, pidfile: Path, name: Optional[str] = None, nrnodes: Optional[int] = None,
                 nodes: Optional[str] = None, topology=None, new: bool = True):
        super().__init__(pidfile=pidfile)
        self.name = name if name is not None else "default"
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
                nodes += [f"Node{i}" for i in range(self.nrnodes - len(nodes))]
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
    print(metadata.version('simulaqron'))


#################
# start command #
#################

@cli.command()
@click.option(
    "--name",
    help="Give the network a name to be able to start multiple (default: default)",
    type=click.STRING,
    default="default",
)
@click.option(
    "-N",
    "--nrnodes",
    help="Number of nodes to start \n(WARNING: overwrites existing config files)",
    type=click.INT,
    default=None,
)
@click.option(
    "-n",
    "--nodes",
    help="Comma separated list of nodes to start \n(WARNING: overwirtes existing config files)",
    type=click.STRING,
    default=None,
)
@click.option(
    "-t",
    "--topology",
    help="Topology of network \n(WARNING: overwrites existing config files)",
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

def start(name: str, nrnodes: Optional[int], nodes: Optional[str],
          topology: Optional[str], force: Optional[bool], keep: Optional[bool]):
    """Starts a network with the given parameters or from config files."""
    new = not keep
    pidfile = PID_FOLDER / f"simulaqron_network_{name}.pid"
    if pidfile.exists():
        logging.warning("Network with name %s is already running", name)
        logging.warning("The pidfile for this network is located at %s", pidfile)
        return
    if new:
        if not force:
            # We will save this new network file in the current directory
            simulaqron_settings.network_config_file = Path.cwd() / sim_backend.DEFAULT_NETWORK_CONFIG_FILE
            answer = input(f"Do you want to add/replace the network '{name}' in the file "
                           f"{simulaqron_settings.network_config_file} with a new network? "
                           f"(yes/no)")
            if not _is_positive_answer(answer):
                print("Aborted!")
                return
    d = SimulaQronDaemon(pidfile=pidfile, name=name, nrnodes=nrnodes, nodes=nodes, topology=topology, new=new)
    try:
        d.start()
    except SystemExit as e:
        if e.code == exit.PIDFILE_INACCESSIBLE or\
           e.code == exit.DAEMONIZE_FAILED:
            logging.debug(f"Failed to launch Simulaqron Daemon. "
                          f"Exit code reported by daemons: {e.code}")
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
def stop(name: Optional[str]):
    """Stops a network."""
    if name is None:
        name = "default"
    pidfile = PID_FOLDER / f"simulaqron_network_{name}.pid"
    if pidfile.exists():
        logging.warning("Network with name %s is not running", name)
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
def reset(force: Optional[bool]):
    """Resets simulaqron"""
    if not force:
        answer = input("Are you sure you want to reset simulaqron?\nThis will revert settings and "
                       "network config files to the default values.\nNote, this action will remove "
                       f"the file at {DEFAULT_SIMULAQRON_SETTINGS_FILENAME} if it exists.\n"
                       "(yes/no)")
    else:
        answer = "yes"
    if _is_positive_answer(answer):
        for entry in PID_FOLDER.iterdir():
            if entry.suffix == ".pid":
                d = SimulaQronDaemon(pidfile=entry)
                d.stop()
                if entry.exists():
                    entry.unlink()
        simulaqron_settings.default_settings()
    else:
        print("Aborting!")

def updates_local_config(command_function: Callable):
    def wrapper(*args, **kwargs):
        local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
        if local_settings.exists() and local_settings.is_file():
            simulaqron_settings.load_from_file(local_settings)
        else:
            simulaqron_settings.default_settings()
            simulaqron_settings.save_to_file(local_settings)
        simulaqron_settings.load_from_file(local_settings)
        command_function(*args, **kwargs)
        simulaqron_settings.save_to_file(local_settings)
    return wrapper


###############
# set command #
###############

@cli.group()
def set():
    """Change a setting"""
    pass


@set.command()
def default():
    """Sets all settings back to default and saves it as a local configuration file"""
    simulaqron_settings.default_settings()
    simulaqron_settings.save_to_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)


@set.command()
@click.argument('value', type=click.Choice([b.value for b in SimBackend]))
@updates_local_config
def sim_backend(value):
    """The backend to use (stabilizer, projectq, qutip)."""
    simulaqron_settings.sim_backend = value


@set.command()
@click.argument('value', type=int)
@updates_local_config
def max_qubits(value):
    """Max virt-qubits per node and max sim-qubits per register."""
    simulaqron_settings.max_qubits = value


@set.command()
@click.argument('value', type=int)
@updates_local_config
def max_registers(value):
    """How many registers a node can hold."""
    simulaqron_settings.max_registers = value


@set.command()
@click.argument('value', type=float)
@updates_local_config
def conn_retry_time(value):
    """If setup fails, how long to wait until a retry."""
    simulaqron_settings.conn_retry_time = value


@set.command()
@click.argument('value', type=float)
@updates_local_config
def recv_timeout(value):
    """When receiving a qubit or EPR pair, how long to wait until raising a timeout."""
    simulaqron_settings.recv_timeout = value


@set.command()
@click.argument('value', type=float)
@updates_local_config
def recv_retry_time(value):
    """When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."""
    simulaqron_settings.recv_retry_time = value


@set.command()
@click.argument('value', type=int)
@updates_local_config
def log_level(value):
    """Log level for both backend and frontend\n10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL."""
    simulaqron_settings.log_level = value


@set.command()
@click.argument('value', type=str)
@updates_local_config
def network_config_file(value):
    """The path to the network_config_file to be used"""
    simulaqron_settings.network_config_file = value


@set.command()
@click.argument('value', type=click.Choice(["on", "off"]))
@updates_local_config
def noisy_qubits(value):
    """Whether qubits should be noisy (on/off)"""
    if value == "on":
        simulaqron_settings.noisy_qubits = True
    else:
        simulaqron_settings.noisy_qubits = False


@set.command()
@click.argument('value', type=float)
@updates_local_config
def t1(value):
    """The effective T1 to be used for noisy qubits"""
    simulaqron_settings.t1 = value

###############
# get command #
###############

def loads_local_config(command_function: Callable):
    def wrapper(*args, **kwargs):
        local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
        if local_settings.exists() and local_settings.is_file():
            simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        else:
            simulaqron_settings.default_settings()
        command_function(*args, **kwargs)
    return wrapper


@cli.group()
def get():
    """Get a setting"""
    pass


@get.command()
@loads_local_config
def sim_backend():
    """The backend to use (stabilizer, projectq, qutip)."""
    print(simulaqron_settings.sim_backend)


@get.command()
@loads_local_config
def max_qubits():
    """Max virt-qubits per node and max sim-qubits per register."""
    print(simulaqron_settings.max_qubits)


@get.command()
@loads_local_config
def max_registers():
    """How many registers a node can hold."""
    print(simulaqron_settings.max_registers)


@get.command()
@loads_local_config
def conn_retry_time():
    """If setup fails, how long to wait until a retry."""
    print(simulaqron_settings.conn_retry_time)


@get.command()
@loads_local_config
def recv_timeout():
    """When receiving a qubit or EPR pair, how long to wait until raising a timeout."""
    print(simulaqron_settings.recv_timeout)


@get.command()
@loads_local_config
def recv_retry_time():
    """When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."""
    print(simulaqron_settings.recv_retry_time)


@get.command()
@loads_local_config
def log_level():
    """Log level for both backend and frontend."""
    print(simulaqron_settings.log_level)


@get.command()
@loads_local_config
def network_config_file():
    """The path to the network_config_file to be used"""
    print(simulaqron_settings.network_config_file)


@get.command()
@loads_local_config
def noisy_qubits():
    """Whether qubits should be noisy (on/off)"""
    if simulaqron_settings.noisy_qubits:
        print("on")
    else:
        print("off")


@get.command()
@loads_local_config
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
                   "for example the qnodeos nodes on one computer and the virtual nodes on another,"
                   "you have to manually construct you config file.")
@click.option('--app-port', type=int,
              help="Port number for the application.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--qnodeos-port', type=int,
              help="Port number for the qnodeos server.\n \
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
def add(name: Optional[str], network_name: Optional[str], hostname=None, app_port=None, qnodeos_port=None, vnode_port=None, neighbors=None,
        force=False):
    """
    Add a node to the network.

    NAME: The name of the node, e.g. Alice

    HOSTNAME: The host name of the node, e.g. localhost or 192.168.0.1
    """
    if not force:
        answer = input(f"Do you want to add the node {name} to the "
                       f"network {network_name} in the file "
                       f"{simulaqron_settings.network_config_file}? (yes/no).")
        if not _is_positive_answer(answer):
            print("Aborting!")
            return
    if neighbors is not None:
        neighbors = neighbors.split(',')
        neighbors = [neighbor.strip() for neighbor in neighbors]
    networks_config = NetworkConfigBuilder()
    networks_config.read_from_file(simulaqron_settings.network_config_file)
    networks_config.add_node(node_name=name, network_name=network_name,
                             app_hostname=hostname, qnodeos_hostname=hostname, vnode_hostname=hostname,
                             app_port=app_port, qnodeos_port=qnodeos_port, vnode_port=vnode_port,
                             neighbors=neighbors)
    networks_config.write_to_file(simulaqron_settings.network_config_file)


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
        answer = input(f"Do you want to remove the node {name} to the network "
                       f"{network_name} in the file "
                       f"{simulaqron_settings.network_config_file}? (yes/no).")
        if not _is_positive_answer(answer):
            print("Aborting!")
            return
    networks_config = NetworkConfigBuilder()
    networks_config.read_from_file(simulaqron_settings.network_config_file)
    networks_config.remove_node(node_name=name, network_name=network_name)
    networks_config.write_to_file(simulaqron_settings.network_config_file)


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
        answer = input(f"Do you want to set the network {network_name} in the file "
                       f"{simulaqron_settings.network_config_file} to default, i.e. "
                       f"with nodes Alice, Bob, Charlie, David and Eve? (yes/no).")
        if not _is_positive_answer(answer):
            print("Aborting!")
            return
    networks_config = NetworkConfigBuilder()
    node_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
    networks_config.add_network(node_names=node_names, network_name=network_name)
    networks_config.write_to_file(simulaqron_settings.network_config_file)


@nodes.command()
@click.option('--network-name', type=str,
              help="The name of the network")
def get(network_name=None):
    """Get the current nodes of the network."""
    networks_config = NetworkConfigBuilder()
    networks_config.read_from_file(simulaqron_settings.network_config_file)
    try:
        nodes = networks_config.get_node_names(network_name=network_name)
    except ValueError:
        print(f"No network {network_name}")
    else:
        print(("{} " * len(nodes))[:-1].format(*nodes))


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s",
        level=simulaqron_settings.log_level,
    )
    cli()

#!/usr/bin/env python3
import importlib.metadata as metadata
import logging
import time
from pathlib import Path
from typing import Optional, Callable, List

import click
from daemons.interfaces import exit
from daemons.prefab import run

from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings, network_config
from simulaqron.settings.network_config import DEFAULT_SIMULAQRON_NETWORK_FILENAME, NodeConfig
from simulaqron.settings.simulaqron_config import SimBackend, DEFAULT_SIMULAQRON_SETTINGS_FILENAME

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
# PID folder should be "LOCAL"
PID_FOLDER = Path.home() / ".simulaqron_pids"

# If the pid folder does not exist, create it
if not PID_FOLDER.exists():
    Path.mkdir(PID_FOLDER)


class RunningSimulaQronDaemon(run.RunDaemon):
    """
    SimulaQronDaemon class used to represent SimulaQron daemons that are already running.
    This class is useful to stop the already-running daemons without needed to read all
    the required configurations.
    """
    def __init__(self, pidfile: Path):
        assert pidfile is not None
        super().__init__(pidfile=pidfile)


class SimulaQronDaemon(run.RunDaemon):
    def __init__(self, pidfile: Path, name: str, nodes: List[str]):
        super().__init__(pidfile=pidfile)
        self.name = name
        self.nodes = nodes

    def run(self):
        """Starts all nodes defined in netsim's config directory."""
        network = Network(network_name=self.name, nodes=self.nodes)
        network.start()

        while True:
            time.sleep(0.1)


def _is_positive_answer(answer: str):
    """
    Used to check if an answer is positive from a user.
    """
    if answer.lower() in ["yes", "y"]:
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
    "--network-config-file",
    help=f"Use the given network config file. Defaults to the file named '{DEFAULT_SIMULAQRON_NETWORK_FILENAME}' "
         f"on the current directory.",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, path_type=Path),
    default=Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME
)
@click.option(
    "--name",
    help="Give the network a name to be able to start multiple (default: 'default')",
    type=str,
    default="default",
)
@click.option(
    "-N",
    "--nrnodes",
    help="Number of nodes to start. This argument will start nodes named 'Node<i>', "
         "until the number of nodes is reached.",
    type=int,
    default=0,
)
@click.option(
    "-n",
    "--nodes",
    help="Comma separated list of nodes to start.",
    type=str,
    default="",
)
def start(name: str, nrnodes: int, nodes: str, network_config_file: Path):
    """Starts a network with the given parameters or from config files."""
    network_config.read_from_file(network_config_file)
    pidfile = PID_FOLDER / f"simulaqron_network_{name}.pid"
    if pidfile.exists():
        logging.warning("Network with name %s is already running", name)
        logging.warning("The pidfile for this network is located at %s", pidfile)
        return
    nodes = nodes.split(",")
    if nrnodes > 0 and len(nodes) < nrnodes:
        nodes += [f"Node{i}" for i in range(nrnodes - len(nodes))]
    d = SimulaQronDaemon(pidfile=pidfile, name=name, nodes=nodes)
    try:
        d.start()
    except SystemExit as e:
        if e.code == exit.PIDFILE_INACCESSIBLE or \
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
    default="default",
)
def stop(name: str):
    """Stops a network."""
    assert name is not None
    pidfile = PID_FOLDER / f"simulaqron_network_{name}.pid"
    if not pidfile.exists():
        logging.warning("Network with name %s is not running", name)
        return
    d = RunningSimulaQronDaemon(pidfile=pidfile)
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
def reset(force: bool):
    """Resets simulaqron"""
    cwd_simulaqron_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not force:
        answer = input("Are you sure you want to reset simulaqron?\nThis will revert settings and "
                       "network config files to the default values.\nNote, this action will remove "
                       f"the file at {cwd_simulaqron_settings} if it exists.\n"
                       "(yes/no)")
    else:
        answer = "yes"
    if _is_positive_answer(answer):
        for entry in PID_FOLDER.iterdir():
            if entry.suffix == ".pid":
                d = RunningSimulaQronDaemon(pidfile=entry)
                d.stop()
                if entry.exists():
                    entry.unlink()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(cwd_simulaqron_settings)
    else:
        print("Aborting!")


###############
# set command #
###############

@cli.group(
    help="Change a simulaqron setting"
)
def set():
    pass


@set.command(
    help="Sets all settings back to default and saves it as a local configuration file in the current folder."
)
def default():
    simulaqron_settings.default_settings()
    simulaqron_settings.save_to_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)


@set.command(
    help="The backend to use (stabilizer, projectq, qutip)."
)
@click.argument(
    "value",
    type=click.Choice([b.value for b in SimBackend])
)
def sim_backend(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    simulaqron_settings.sim_backend = value
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


@set.command(
    help="Max virt-qubits per node and max sim-qubits per register."
)
@click.argument(
    'value',
    type=int
)
def max_qubits(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    simulaqron_settings.max_qubits = value
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


@set.command(
    help="How many registers a node can hold."
)
@click.argument(
    'value',
    type=int
)
def max_registers(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    simulaqron_settings.max_registers = value
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


@set.command(
    help="If setup fails, how long to wait until a retry."
)
@click.argument(
    'value',
    type=float
)
def conn_retry_time(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    simulaqron_settings.conn_retry_time = value
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


@set.command(
    help="When receiving a qubit or EPR pair, how long to wait until raising a timeout."
)
@click.argument(
    'value',
    type=float
)
def recv_timeout(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    simulaqron_settings.recv_timeout = value
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


@set.command(
    help="When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."
)
@click.argument(
    'value',
    type=float
)
def recv_retry_time(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    simulaqron_settings.recv_retry_time = value
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


@set.command(
    help="Log level for both backend and frontend\n10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL."
)
@click.argument(
    'value',
    type=int
)
def log_level(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    simulaqron_settings.log_level = value
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


@set.command(
    help="Whether qubits should be noisy (on/off)"
)
@click.argument(
    'value',
    type=click.Choice(["on", "off"])
)
def noisy_qubits(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    if value == "on":
        simulaqron_settings.noisy_qubits = True
    else:
        simulaqron_settings.noisy_qubits = False
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


@set.command(
    help="The effective T1 to be used for noisy qubits"
)
@click.argument(
    'value',
    type=float
)
def t1(value):
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if not local_settings.exists():
        local_settings.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.save_to_file(local_settings)
    simulaqron_settings.load_from_file(local_settings)
    simulaqron_settings.t1 = value
    simulaqron_settings.save_to_file(local_settings)
    print(f"Configuration saved to file: '{local_settings}'")


###############
# get command #
###############


@cli.group()
def get():
    """Get a setting"""
    pass


@get.command(
    help="The backend to use (stabilizer, projectq, qutip).",
)
def sim_backend():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
    print(simulaqron_settings.sim_backend)


@get.command(
    help="Max virt-qubits per node and max sim-qubits per register."
)
def max_qubits():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
    print(simulaqron_settings.max_qubits)


@get.command(
    help="How many registers a node can hold."
)
def max_registers():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
    print(simulaqron_settings.max_registers)


@get.command(
    help="If setup fails, how long to wait until a retry."
)
def conn_retry_time():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
    print(simulaqron_settings.conn_retry_time)


@get.command(
    help="When receiving a qubit or EPR pair, how long to wait until raising a timeout."
)
def recv_timeout():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
    print(simulaqron_settings.recv_timeout)


@get.command(
    help="When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."
)
def recv_retry_time():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
    print(simulaqron_settings.recv_retry_time)


@get.command(
    help="Log level for both backend and frontend."
)
def log_level():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
    print(simulaqron_settings.log_level)


@get.command(
    help="Whether qubits should be noisy (on/off)"
)
def noisy_qubits():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
    if simulaqron_settings.noisy_qubits:
        print("on")
    else:
        print("off")


@get.command(
    help="The effective T1 to be used for noisy qubits"
)
def t1():
    local_settings = Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME
    if local_settings.exists() and local_settings.is_file():
        simulaqron_settings.load_from_file(Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME)
        print(f"Configuration loaded from file: '{local_settings}':")
    else:
        print(f"Configuration from default configuration:")
        simulaqron_settings.default_settings()
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
@click.argument('name', type=str, required=True)
@click.option('--network-name', type=str, default="default",
              help="The name of the network")
@click.option('--hostname', type=str, default="localhost",
              help="The host name of the node, e.g. localhost (default) or 192.168.0.1\n"
                   "If you wish to have different components on different hostname,"
                   "for example the qnodeos nodes on one computer and the virtual nodes on another,"
                   "you have to manually construct you config file.")
@click.option('--app-port', type=int, default=-1,
              help="Port number for the application.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--qnodeos-port', type=int, default=-1,
              help="Port number for the qnodeos server.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--vnode-port', type=int, default=-1,
              help="Port number for the virtual node.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--neighbors', type=str,
              help="The neighbors of the node in the network separated by ',' (no space).\n \
                    For example '--neighbors Bob,Charlie,David'.\n \
                    If not specified all current nodes in the network will be neighbors.")
def add(name: str, network_name: str, hostname: str , app_port: int, qnodeos_port: int,
        vnode_port: int, neighbors: Optional[str]=None):
    """
    Add a node to the network.

    NAME: The name of the node, e.g. Alice

    HOSTNAME: The host name of the node, e.g. localhost or 192.168.0.1
    """
    if neighbors is not None:
        neighbors = neighbors.split(',')
        neighbors = [neighbor.strip() for neighbor in neighbors]
    cwd_network_config_path = Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME
    network_config.read_from_file(cwd_network_config_path)
    network_config.add_node(node_name=name, network_name=network_name,
                             app_hostname=hostname, qnodeos_hostname=hostname, vnode_hostname=hostname,
                             app_port=app_port, qnodeos_port=qnodeos_port, vnode_port=vnode_port,
                             neighbors=neighbors)
    network_config.write_to_file(cwd_network_config_path)
    added_node: NodeConfig = network_config.get_nodes(network_name=network_name)[name]
    print(f"Node with name '{added_node.name}' was added to the network with name '{network_name}'.\n"
          f"Socket addresses are:\n"
          f"* App/Classical: '({added_node.app_hostname}, {added_node.app_port})\n"
          f"* QNodeOS: '({added_node.qnodeos_hostname}, {added_node.qnodeos_port})\n"
          f"* Virtual Node: '({added_node.vnode_hostname}, {added_node.vnode_port})\n")


@nodes.command()
@click.argument('name', type=str, required=True)
@click.option('--network-name', type=str, default="default",
              help="The name of the network")
def remove(name: str, network_name: str):
    """
    Remove a node to the network.

    NAME: The name of the node, e.g. Alice
    """
    cwd_network_config_path = Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME
    network_config.read_from_file(cwd_network_config_path)
    network_config.remove_node(node_name=name, network_name=network_name)
    network_config.write_to_file(cwd_network_config_path)
    print(f"Node with name '{name}' was removed from the network with name '{network_name}'.\n")


@nodes.command()
def default():
    """
    Sets the default nodes of the network.

    The default network consists of the five nodes:
    Alice, Bob, Charlie, David, Eve
    """
    cwd_network_config_path = Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME
    network_config.using_default_network()
    network_config.write_to_file(cwd_network_config_path)
    print(f"Default network saved to file: '{cwd_network_config_path}'")


@nodes.command()
@click.option('--network-name', type=str, default="default",
              help="The name of the network")
def get(network_name: str):
    """Get the current nodes of the network."""
    cwd_network_config_path = Path.cwd() / DEFAULT_SIMULAQRON_NETWORK_FILENAME
    network_config.read_from_file(cwd_network_config_path)
    try:
        nodes = network_config.get_node_names(network_name=network_name)
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

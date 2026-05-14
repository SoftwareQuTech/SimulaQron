import importlib.metadata as metadata
import logging
import os
import signal
import sys
import time
from pathlib import Path
from psutil import Process
from typing import Optional, List

import click
from daemons.interfaces import exit  # type: ignore[import-untyped]
from daemons.prefab import run  # type: ignore[import-untyped]

from simulaqron.general.constants import SIMULAQRON_LOGS_FOLDER
from simulaqron.network import Network
from simulaqron.toolbox.cliutil import find_processes_by_cmdline
from simulaqron.settings import LOCAL_SIMULAQRON_SETTINGS, LOCAL_NETWORK_SETTINGS, HOME_NETWORK_SETTINGS
from simulaqron.settings import simulaqron_settings, network_config
from simulaqron.settings.network_config import (NodeConfig, DEFAULT_SIMULAQRON_NETWORK_FILENAME,
                                                get_default_network_config_file)
from simulaqron.settings.simulaqron_config import SimBackend, get_default_simulaqron_config_file

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
# PID folder should be "LOCAL"
PID_FOLDER = Path.home() / ".simulaqron_pids"

# If the pid folder does not exist, create it
if not PID_FOLDER.exists():
    Path.mkdir(PID_FOLDER)


# The following two classes (SimulaQronDaemon and RunningSimulaQronDaemon) are 2 classes that
# implement the simulaqron daemon process.
# The former class models a daemon process used to launch the backend processes
# (1 Vnode and 1 QNodeOS process per node starting), and then it simply goes to sleep.
# The latter class is used when invoking "simulaqron stop" to "reattach" to the launching
# daemon process, and kill all the backend processes.
# Both of the mentioned classes rely on the python "daemons" package, **which is designed
# to run on Unix platforms** (Linux/macOS). Implementing a similar behavior in Windows
# will require a heavy reimplementation of these 2 classes.


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
    def __init__(self, pidfile: Path, name: str, nodes: List[str], network_config_file: Path):
        """
        Daemon process that runs a SimulaQron network in the background.

        This daemon spawns virtual nodes and QNodeOS servers for each node
        in the network configuration. It runs until explicitly stopped.

        :param pidfile: Path to the PID file used to track the daemon process.
        :type pidfile: Path
        :param name: Name of the network (e.g., 'default').
        :type name: str
        :param nodes: List of node names to start (e.g., ['Alice', 'Bob']).
        :type nodes: List[str]
        :param network_config_file: Path to the network configuration file.
        :type network_config_file: Path

        """
        super().__init__(pidfile=pidfile)
        self.name = name
        self.nodes = nodes
        self.network_config_file = network_config_file

    def run(self):
        """Starts all nodes defined in netsim's config directory."""

        # Let's make sure we can record the output where it's accessible
        simulaqron_driver_log = SIMULAQRON_LOGS_FOLDER / f"simulaqron-driver-{os.getpid()}.log"
        sys.stdout = open(simulaqron_driver_log, 'w', buffering=1)
        sys.stderr = open(simulaqron_driver_log, 'w', buffering=1)

        # Let's read the config file we should be working from
        network_config.read_from_file(self.network_config_file)

        # Start the network to be simulated on this node
        network = Network(
            nodes=self.nodes,
            network_config_file=self.network_config_file,
            network_name=self.name,
        )
        network.start()

        while True:
            time.sleep(0.1)


def _path_exists(path: Path) -> bool:
    if not path.exists() or path.is_dir():
        return False
    return True


def _load_local_settings_or_default():
    if LOCAL_SIMULAQRON_SETTINGS.exists() and LOCAL_SIMULAQRON_SETTINGS.is_file():
        simulaqron_settings.read_from_file(LOCAL_SIMULAQRON_SETTINGS)
        click.echo(f"Configuration loaded from file: '{LOCAL_SIMULAQRON_SETTINGS}'")
    else:
        click.echo("Configuration from default configuration")
        simulaqron_settings.default_settings()


def _create_local_settings_if_needed_and_load():
    if not LOCAL_SIMULAQRON_SETTINGS.exists():
        LOCAL_SIMULAQRON_SETTINGS.touch()
        simulaqron_settings.default_settings()
        simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    # At this point we are sure that the local settings exists, so we can
    # load them using the function from above.
    _load_local_settings_or_default()


def _load_local_network_or_default():
    if LOCAL_NETWORK_SETTINGS.exists() and LOCAL_NETWORK_SETTINGS.is_file():
        network_config.read_from_file(LOCAL_NETWORK_SETTINGS)
        click.echo(f"Network configuration loaded from file: '{LOCAL_NETWORK_SETTINGS}'")
    else:
        click.echo("Configuration from default configuration")
        network_config.default_settings()


def _create_local_networks_if_needed_and_load():
    if not LOCAL_NETWORK_SETTINGS.exists():
        LOCAL_NETWORK_SETTINGS.touch()
        network_config.default_settings()
        network_config.write_to_file(LOCAL_NETWORK_SETTINGS)
    # At this point we are sure that the local settings exists, so we can
    # load them using the function from above.
    _load_local_network_or_default()


@click.group(
    context_settings=CONTEXT_SETTINGS,
    epilog="Run 'simulaqron COMMAND --help' for more information on a command."
)
def cli_entry_point():
    """Command line interface for interacting with SimulaQron."""
    pass


###########
# version #
###########

@cli_entry_point.command()
def version():
    """
    Prints the version of simulqron.
    """
    click.echo(metadata.version('simulaqron'))


#################
# start command #
#################

@cli_entry_point.command()
@click.option(
    "--network-config-file",
    help=f"Path to network config file. If not specified, uses ./{DEFAULT_SIMULAQRON_NETWORK_FILENAME} "  # noqa: E131
         f"or ~/.simulaqron/{DEFAULT_SIMULAQRON_NETWORK_FILENAME}",  # noqa: E131
    type=click.Path(exists=False, dir_okay=False, resolve_path=True, path_type=Path),
    default=get_default_network_config_file()
)
@click.option(
    "--simulaqron-config-file",
    help=f"Use the given simulaqron config file. Defaults to the file named "  # noqa: E131
         f"'{DEFAULT_SIMULAQRON_NETWORK_FILENAME}' on the current directory.",  # noqa: E131
    type=click.Path(exists=False, dir_okay=False, resolve_path=True, path_type=Path),
    default=get_default_simulaqron_config_file()
)
@click.option(
    "--network-name",
    help="Give the network a name to be able to start multiple (default: 'default')",
    type=str,
    default="default",
)
@click.option(
    "-n",
    "--nodes",
    help="Comma separated list of nodes to start.",
    type=str,
    default="",
)
def start(network_name: str, nodes: str, simulaqron_config_file: Path, network_config_file: Path):
    """
    Starts a network with the given parameters or from config files.

    :param network_name: Name of the network to start.
    :type network_name: str
    :param nodes: Comma separated list of nodes to start.
    :type nodes: str
    :param simulaqron_config_file: Path to simulaqron's config file.
    :type simulaqron_config_file: Path
    :param network_config_file: Path to network config file.
    :type network_config_file: Path
    """
    # Checks the simulaqron config
    if not _path_exists(simulaqron_config_file):
        raise click.BadOptionUsage(
            option_name="simulaqron-config-file",
            message=f"The given simulaqron config file '{simulaqron_config_file}' does not exist or it "
                    "is a folder.\nPlease check the path given to the --simulaqron-config-file option."  # noqa: E131
        )
    # Checks the network config
    if not _path_exists(network_config_file):
        raise click.BadOptionUsage(
            option_name="network-config-file",
            message=f"The given network config file '{network_config_file}' does not exist or it is a "
                    "folder.\nPlease check the path given to the --network-config-file option."  # noqa: E131
        )
    # Load SimulaQron and network configs
    simulaqron_settings.read_from_file(simulaqron_config_file)
    network_config.read_from_file(network_config_file)
    # Check that the network name exists in the network configuration
    if network_name not in network_config.networks:
        raise click.BadOptionUsage(
            option_name="name",
            message=f"The network '{network_name}' was not found in the network configuration file "  # noqa: E713
                    f"'{network_config_file}'.\nPlease check the name you passed in the"  # noqa: E131
                    " --name option and try again."  # noqa: E131
        )
    # Check that the nodes to start exist in the given network
    start_all = False
    if len(nodes) <= 0:
        click.echo(f"No nodes specified to start. Starting all nodes configured in '{network_config_file}'.")
        start_all = True
        parsed_nodes = []
    else:
        parsed_nodes = nodes.split(",")

    if start_all:
        for node_to_start in network_config.networks[network_name].nodes:
            parsed_nodes.append(node_to_start)
    else:
        for node_to_start in parsed_nodes:
            if node_to_start not in network_config.networks[network_name].nodes:
                raise click.BadOptionUsage(
                    option_name="nodes",
                    message=f"The node '{node_to_start}' was not found in the network named "  # noqa: E713
                            f"'{network_name} 'specified in the configuration file "  # noqa: E131
                            f"'{network_config_file}'.\n"  # noqa: E131
                            "Please check the list of names you passed in the --nodes option "  # noqa: E131
                            "and try again."  # noqa: E131
                )
    # Check that there is no other network with the same name running
    pidfile = PID_FOLDER / f"simulaqron_network_{network_name}.pid"
    if pidfile.exists():
        click.echo(
            f"Network with name {network_name} is seems to be already running.\n"
            f"This is based on the fact that the PID file '{str(pidfile)}' already exists.\n"
            "\n"
            f"To try to stop the running backend, run 'simulaqron stop --name {network_name}'.\n"
            "If the error persist, you might need to use 'simulaqron reset' commands to reset the\n"
            "backend execution state:\n"
            f"* 'simulaqron reset pidfiles' will delete *all* the PID files in '{str(PID_FOLDER)}'.\n"
            f"* 'simulaqron reset processes' will *kill all* running simulaqron-related processes.\n"
            "\n"
            "Check the help of the simulaqron reset command ('simulaqron reset -h') to know more."
        )
        return

    # Let's start the simulaqron daemon. We will pass the config file so it will be available
    # in the child process and load the same config
    d = SimulaQronDaemon(
        pidfile=pidfile,
        name=network_name,
        nodes=parsed_nodes,
        network_config_file=network_config_file
    )
    try:
        d.start()
    except SystemExit as e:
        if e.code == exit.PIDFILE_INACCESSIBLE or \
                e.code == exit.DAEMONIZE_FAILED:
            logging.debug(f"Failed to launch Simulaqron Daemon. "
                          f"Exit code reported by daemons: {e.code}")
            raise click.BadParameter("Failed to launch SimulaQron Daemon. Aborted!")


###############
# stop command #
###############

@cli_entry_point.command()
@click.option(
    "--name",
    help="Stop the network with then a given name (default: default)",
    type=click.STRING,
    default="default",
)
def stop(name: str):
    """
    Stops a network.

    :param name: Name of the network to stop.
    :type name: str
    """
    assert name is not None
    pidfile = PID_FOLDER / f"simulaqron_network_{name}.pid"
    logging.debug("Trying to open PIDfile")
    if not pidfile.exists():
        logging.warning("Network with name %s is not running", name)
        return
    d = RunningSimulaQronDaemon(pidfile=pidfile)
    d.stop()


#################
# reset command #
#################

@cli_entry_point.group(
    help="Resets a simulaqron setting or the backend state"
)
def reset():
    pass


@click.option(
    "-f",
    "--force",
    help="Don't ask for any confirmation.",
    is_flag=True,
)
@reset.command(
    help="Forcefully terminate any SimulaQron backend-related processes.IMPORTANT: Please note\n"
         "that this command *will not* terminate any processes from the application layer (i.e.\n"
         "processes that were invoked manually - namely \"Alice\", \"Bob\", and processes alike).\n"
         "WARNING: This potentially leaves the system in a state where SimulaQron thinks that the "
         "backend is running, but the processes are not running anymore. This is due to "
         f"the fact that the associated PID is still in the {PID_FOLDER} folder. In this "
         "state, subsequent invocations of `simulaqron start` will fail with the \"network "
         "is already running\". error. Use the `-d` option of this command to also delete "
         "the corresponding .pid files."
)
def processes(force: bool):
    """
    Send SIGKILL to all the processes that contain "simulaqron" in their command line.
    **WARNING**: This potentially leaves the system in a state where SimulaQron thinks
    that the backend is running, but the processes are not running anymore. This is due
    to the fact that the associated PID is still in the {PID_FOLDER} folder. In this
    state, subsequent invocations of `simulaqron start` will fail with the network
    is already running. error. Use the `-d` option of this command to also delete
    the corresponding .pid files.

    :param force: Don't ask for any confirmation when resetting.
    :type force: bool
    """
    # Find processes related with "simulaqron" and kill them
    processes_prompt = "Are you sure you want to forcefully stop all the simulaqron backend processes?"
    if force or click.confirm(processes_prompt):
        simulaqron_processes: List[Process] = find_processes_by_cmdline("simulaqron")
        for proc in simulaqron_processes:
            if "reset" in proc.cmdline() and "processes" in proc.cmdline():
                continue
            logging.warning(
                "Sending SIGKILL to PID = %d, cmd = %s",
                proc.pid, str(proc.cmdline())
            )
            os.kill(proc.pid, signal.SIGKILL)


@click.option(
    "-f",
    "--force",
    help="Don't ask for any confirmation.",
    is_flag=True,
)
@reset.command(
    help=f"Deletes any .pid files in {PID_FOLDER} representing a running network backend.\n"
         "WARNING: This potentially leaves the system in a state where SimulaQron thinks "  # noqa: E131
         "that the backend is not running, but the ports are taken by running processes. "
         "In this state, subsequent invocations of `simulaqron start` will fail with the "
         "\"cannot bind address\" error. Use the `-p` option of this command to also "
         "forcefully kill those processes.",
)
def pidfiles(force: bool):
    """
    Deletes all the simulaqron PID files in the PID_FOLDER location.
    WARNING: This potentially leaves the system in a state where SimulaQron thinks
    that the backend is not running, but the ports are taken by running processes
    In this state, subsequent invocations of `simulaqron start` will fail with the
    "cannot bind address error". Use the `-p` option of this command to also
    forcefully kill those processes.

    :param force: Don't ask for any confirmation when resetting.
    :type force: bool
    """
    # Delete all the -pid files in the PID_FOLDER folder
    pid_files_prompt = f"Are you sure you want to delete the .pid files in {PID_FOLDER}?"
    if force or click.confirm(pid_files_prompt):
        for entry in PID_FOLDER.iterdir():
            if entry.exists() and entry.suffix == ".pid":
                logging.warning("Deleting PID  file '%s'", str(entry))
                entry.unlink()


@click.option(
    "-f",
    "--force",
    help="Don't ask for any confirmation.",
    is_flag=True,
)
@reset.command(
    help="Reset the SimulaQron settings to their default. Using this option affects both "
         f"{LOCAL_SIMULAQRON_SETTINGS} *and* {LOCAL_NETWORK_SETTINGS} files.",
)
def network(force: bool):
    """
    Resets simulaqron settings to their default. Check the :py:class:`SimulaqronConfig` and
    :py:meth:`NetworksConfiguration.using_default_network` pydoc to check the default values
    of the configuration. **WARNING**: This method overwrites the LOCAL_SIMULAQRON_SETTINGS
    and LOCAL_NETWORK_SETTINGS.

    :param force: Don't ask for any confirmation when resetting.
    :type force: bool
    """
    # Reset the *local* network and simulaqron settings
    settings_prompt = ("Are you sure you want to reset simulaqron settings?\nThis will revert local "
                       "settings and network config files to the default values.\nNote, this action "
                       f"will remove the file at {LOCAL_SIMULAQRON_SETTINGS} and {LOCAL_NETWORK_SETTINGS} "
                       "if they exist.")
    if force or click.confirm(settings_prompt):
        simulaqron_settings.default_settings()
        if LOCAL_NETWORK_SETTINGS.exists():
            simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)

        network_config.using_default_network()
        if LOCAL_NETWORK_SETTINGS.exists():
            network_config.write_to_file(LOCAL_NETWORK_SETTINGS)


###############
# set command #
###############

@cli_entry_point.group(
    help="Change a simulaqron setting"
)
def set():
    """
    Change a SimulaQron setting.
    """
    pass


@set.command(
    help="Sets all settings back to default and saves it as a local configuration file in the current folder."
)
def default():
    """
    Sets all settings back to default and saves it as a local configuration file in the current folder.
    """
    simulaqron_settings.default_settings()
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)


@set.command(
    help="The backend to use (stabilizer, projectq, qutip)."
)
@click.argument(
    "value",
    type=click.Choice([b.value for b in SimBackend])
)
def backend(value: SimBackend):
    """
    The backend to use (stabilizer, projectq, qutip).

    :param value: Value of the backend to use. This can either be ``stabilizer``, ``projectq`` or ``qutip``.
    :type value: SimBackend
    """
    _create_local_settings_if_needed_and_load()
    simulaqron_settings.sim_backend = value
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


@set.command(
    help="Max virt-qubits per node and max sim-qubits per register."
)
@click.argument(
    'value',
    type=int
)
def max_qubits(value: int):
    """
    Sets the max virt-qubits per node and max sim-qubits per register.

    :param value: Value of the max virt-qubits per node and max sim-qubits per register.
    :type value: int
    """
    _create_local_settings_if_needed_and_load()
    simulaqron_settings.max_qubits = value
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


@set.command(
    help="How many registers a node can hold."
)
@click.argument(
    'value',
    type=int
)
def max_registers(value: int):
    """
    Sets how many registers a node can hold.

    :param value: Value of the max registers a node can hold.
    :type value: int
    """
    _create_local_settings_if_needed_and_load()
    simulaqron_settings.max_registers = value
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


@set.command(
    help="If setup fails, how long to wait until a retry."
)
@click.argument(
    'value',
    type=float
)
def conn_retry_time(value: float):
    """
    Sets the conn_retry_time; how long to wait until a retry a connection to a SimulaQron component.

    :param value: Value of the conn_retry_time.
    """
    _create_local_settings_if_needed_and_load()
    simulaqron_settings.conn_retry_time = value
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


@set.command(
    help="When receiving a qubit or EPR pair, how long to wait until raising a timeout."
)
@click.argument(
    'value',
    type=float
)
def recv_timeout(value: float):
    """
    Sets the recv_timeout in seconds before raising a timeout when receiving a qubit or EPR pair.

    :param value: Value of the recv_timeout.
    """
    _create_local_settings_if_needed_and_load()
    simulaqron_settings.recv_timeout = int(value)
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


@set.command(
    help="When receiving a qubit or EPR pair, how long to wait between attempts to receive an EPR pair half."
)
@click.argument(
    'value',
    type=float
)
def recv_retry_time(value: float):
    """
    Sets the recv_retry_time value as the number of seconds to wait between attempts when receiving a qubit or EPR pair.

    :param value: Value of the recv_retry_time.
    """
    _create_local_settings_if_needed_and_load()
    simulaqron_settings.recv_retry_time = value
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


@set.command(
    help="Log level for both backend and frontend\n10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL."
)
@click.argument(
    'value',
    type=int
)
def log_level(value: int):
    """
    Sets the log level for both backend and frontend. Possible values are 10=DEBUG, 20=INFO, 30=WARNING,
    40=ERROR, 50=CRITICAL.

    :param value: Value of the log_level.
    :type value: int
    """
    _create_local_settings_if_needed_and_load()
    simulaqron_settings.log_level = value
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


@set.command(
    help="Whether qubits should be noisy (on/off)"
)
@click.argument(
    'value',
    type=click.Choice(["on", "off"])
)
def noisy_qubits(value: str):
    """
    Configures SimulaQron to simulate noisy qubits or not.
    :param value: A string whether to noisy qubits or not. The string "no" will be interpreted as
                  not using noisy qubits. Any other string will be interpreted as using noisy qubits.
    :type value: str
    """
    _create_local_settings_if_needed_and_load()
    if value == "on":
        simulaqron_settings.noisy_qubits = True
    else:
        simulaqron_settings.noisy_qubits = False
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


@set.command(
    help="The effective T1 to be used for noisy qubits"
)
@click.argument(
    'value',
    type=float
)
def t1(value: float):
    """
    Sets the T1 value for noisy qubits.
    :param value: The T1 value for noisy qubits.
    :type value: float
    """
    _create_local_settings_if_needed_and_load()
    simulaqron_settings.t1 = value
    simulaqron_settings.write_to_file(LOCAL_SIMULAQRON_SETTINGS)
    click.echo(f"Configuration saved to file: '{LOCAL_SIMULAQRON_SETTINGS}'")


###############
# get command #
###############


@cli_entry_point.group()
def get():
    """Get a setting"""
    pass


@get.command(
    help="The backend to use (stabilizer, projectq, qutip).",
)
def backend():
    """
    Prints the current configured simulaqron backend.
    """
    _load_local_settings_or_default()
    click.echo(simulaqron_settings.sim_backend)


@get.command(
    help="Max virt-qubits per node and max sim-qubits per register."
)
def max_qubits():
    """
    Prints the current configured max virt-qubits per node and max sim-qubits per register.
    """
    _load_local_settings_or_default()
    click.echo(simulaqron_settings.max_qubits)


@get.command(
    help="How many registers a node can hold."
)
def max_registers():
    """
    Prints the current configured max number of register a node can hold.
    """
    _load_local_settings_or_default()
    click.echo(simulaqron_settings.max_registers)


@get.command(
    help="If setup fails, how long to wait until a retry."
)
def conn_retry_time():
    """
    Prints the current configured conn_retry value; the number of seconds to wait before retrying
    to connect to another node or SimulaQron component.
    """
    _load_local_settings_or_default()
    click.echo(simulaqron_settings.conn_retry_time)


@get.command(
    help="When receiving a qubit or EPR pair, how long to wait until raising a timeout."
)
def recv_timeout():
    """
    Prints the current configured recv_timeout value; the number of seconds to wait for receiving
    an EPR half before raising a timeout error.
    """
    _load_local_settings_or_default()
    click.echo(simulaqron_settings.recv_timeout)


@get.command(
    help="When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."
)
def recv_retry_time():
    """
    Prints the current configured recv_retry_time value; the number of seconds to wait between
    attempts to receive an EPR half.
    """
    _load_local_settings_or_default()
    click.echo(simulaqron_settings.recv_retry_time)


@get.command(
    help="Log level for both backend and frontend."
)
def log_level():
    """
    Prints the current configured log level.
    """
    _load_local_settings_or_default()
    click.echo(simulaqron_settings.log_level)


@get.command(
    help="Whether qubits should be noisy (on/off)"
)
def noisy_qubits():
    """
    Prints whether SimulaQron has been configured to simulate noisy qubits or not.
    """
    _load_local_settings_or_default()
    if simulaqron_settings.noisy_qubits:
        click.echo("on")
    else:
        click.echo("off")


@get.command(
    help="The effective T1 to be used for noisy qubits"
)
def t1():
    """
    Prints the current configured t1 value when simulating noisy qubits.
    """
    _load_local_settings_or_default()
    click.echo(simulaqron_settings.t1)


###############
# node command #
###############

@cli_entry_point.group()
def nodes():
    """
    Manage the nodes in the simulated network. This command *will alter* the
    ``simulaqron_network.json`` file in the current directory.

    .. note:: This needs to be done before starting the network.
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
def add(name: str, network_name: str, hostname: str, app_port: int, qnodeos_port: int,
        vnode_port: int, neighbors: Optional[str] = None):
    """
    Add a node to the network. This command *will modify* the ``simulaqron_network.json``
    file in the current directory.

    :param name: The name of the node to add.
    :type name: str
    :param network_name: The name of the network to add the node to.
    :type network_name: str
    :param hostname: The hostname of the machine that will run  the node, e.g. localhost.
    :type hostname: str
    :param app_port: The port number for the application, e.g. 8000
    :type app_port: int
    :param qnodeos_port: The port number for the qnodeos server, e.g. 8000
    :type qnodeos_port: int
    :param vnode_port: The port number for the virtual node, e.g. 8000
    :type vnode_port: int
    :param neighbors: A comma-separated list of neighbors of the given node. The given names
                      *will not be checked* if they exist in the given network.
    :type neighbors: Optional[str]
    """
    _create_local_networks_if_needed_and_load()
    network_config.read_from_file(LOCAL_NETWORK_SETTINGS)
    if neighbors is not None:
        neighbors = neighbors.split(',')
        neighbors = [neighbor.strip() for neighbor in neighbors]
    network_config.add_node(node_name=name, network_name=network_name,
                            app_hostname=hostname, qnodeos_hostname=hostname, vnode_hostname=hostname,
                            app_port=app_port, qnodeos_port=qnodeos_port, vnode_port=vnode_port,
                            neighbors=neighbors)
    network_config.write_to_file(LOCAL_NETWORK_SETTINGS)
    added_node: NodeConfig = network_config[network_name][name]
    click.echo(f"Node with name '{added_node.name}' was added to the network with name '{network_name}'.\n"
               "Socket addresses are: \n"
               f"* App/Classical: '({added_node.app_hostname}, {added_node.app_port})\n"
               f"* QNodeOS: '({added_node.qnodeos_hostname}, {added_node.qnodeos_port})\n"
               f"* Virtual Node: '({added_node.vnode_hostname}, {added_node.vnode_port})\n")


@nodes.command()
@click.argument('name', type=str, required=True)
@click.option('--network-name', type=str, default="default",
              help="The name of the network")
def remove(name: str, network_name: str):
    """
    Remove a node to the network. This command *will modify* the ``simulaqron_network.json``
    file in the current directory.

    :param name: The name of the node to remove.
    :type name: str
    :param network_name: The name of the network to remove the node from.
    :type network_name: str
    """

    if not LOCAL_NETWORK_SETTINGS.exists() or not LOCAL_NETWORK_SETTINGS.is_file():
        click.echo(f"WARNING - the file '{LOCAL_NETWORK_SETTINGS}' was not found. The loaded "
                   f"configuration corresponds to the one on '{HOME_NETWORK_SETTINGS}'")
    else:
        network_config.read_from_file(LOCAL_NETWORK_SETTINGS)
    network_config.remove_node(node_name=name, network_name=network_name)
    network_config.write_to_file(LOCAL_NETWORK_SETTINGS)
    click.echo(f"Node with name '{name}' was removed from the network with name '{network_name}'.\n")


@nodes.command()
def default():
    """
    Sets the default nodes of the network. This command *will modify* the ``simulaqron_network.json``
    file in the current directory.

    The default network consists of the five nodes:
    Alice, Bob, Charlie, David, Eve
    """
    network_config.using_default_network()
    network_config.write_to_file(LOCAL_NETWORK_SETTINGS)
    click.echo(f"Default network saved to file: '{LOCAL_NETWORK_SETTINGS}'")


@nodes.command()
@click.option('--network-name', type=str, default="default",
              help="The name of the network")
def get(network_name: str):
    """
    Print the nodes present in the given network.

    :param network_name: The name of the network to get the nodes from.
    :type network_name: str
    """

    if not LOCAL_NETWORK_SETTINGS.exists() or not LOCAL_NETWORK_SETTINGS.is_file():
        click.echo(f"WARNING - the file '{LOCAL_NETWORK_SETTINGS}' was not found. The loaded "
                   f"configuration corresponds to the one on '{HOME_NETWORK_SETTINGS}'")
    else:
        network_config.read_from_file(LOCAL_NETWORK_SETTINGS)
    try:
        nodes = network_config.get_node_names(network_name=network_name)
    except ValueError:
        raise click.BadParameter(f"No network {network_name}")
    else:
        click.echo(("{} " * len(nodes))[:-1].format(*nodes))


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(message)s",
        level=simulaqron_settings.log_level,
    )
    cli_entry_point()

import click
import logging
import multiprocessing as mp
import os
import time

from pathlib import Path

from SimulaQron.settings import Settings
from SimulaQron.virtNode.virtual import backEnd
from SimulaQron.run.startCQC import main as start_cqc
from SimulaQron.run.startCQCLog import main as start_cqc_log
from SimulaQron.run.startNode import main as start_node
from SimulaQron.configFiles import construct_node_configs, construct_topology_config


def _load_node_names(path):
    """Load list of nodes from Nodes.cfg file

    :path: pathlib.Path pointing to Nodes.cfg file"""
    with path.open() as f:
        return [line.strip() for line in f.readlines()]


_common_options = [
    click.option(
        "--netsim",
        envvar="NETSIM",
        help="Network simulation root (default: $NETSIM)",
        type=click.Path(exists=True, file_okay=False, dir_okay=True),
    ),
    click.option(
        "-nn",
        "--nrnodes",
        help="Number of nodes to start \n(WARNING: overwites existing config files)",
        type=click.INT,
        default=None,
    ),
    click.option(
        "-nd",
        "--nodes",
        help="Comma separated list of nodes to start \n(WARNING: overwites existing config files)",
        type=click.STRING,
        default=None,
    ),
    click.option(
        "-tp",
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
def start_all(netsim, nrnodes, nodes, topology):
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

        construct_node_configs(nodes=nodes)
        construct_topology_config(topology=topology, nodes=nodes)

    mp.set_start_method("spawn")

    config_dir = Path(netsim) / "config"
    nodes_cfg_path = config_dir / "Nodes.cfg"
    nodes = _load_node_names(nodes_cfg_path)
    processes = []

    for node in nodes:
        process_virtual = mp.Process(
            target=start_node, args=(node,), name="VirtNode {}".format(node)
        )
        process_cqc = mp.Process(
            target=start_cqc, args=(node,), name="CQCNode {}".format(node)
        )
        processes += [process_virtual, process_cqc]
    try:
        for p in processes:
            print("Starting process {}".format(p.name))
            p.start()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
        sys.exit(0)


@network.command()
@common_options
def start_all_log(netsim, nrnodes, nodes, topology):
    """Starts the CQC nodes defined in netsim's config directory."""
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

        construct_node_configs(nodes=nodes)
        construct_topology_config(topology=topology, nodes=nodes)

    mp.set_start_method("spawn")

    config_dir = Path(netsim) / "config"
    nodes_cfg_path = config_dir / "Nodes.cfg"
    nodes = _load_node_names(nodes_cfg_path)
    processes = []

    for node in nodes:
        process_cqc_log = mp.Process(
            target=start_cqc_log, args=(node,), name="CQCLogNode {}".format(node)
        )
        processes.append(process_cqc_log)

    try:
        for p in processes:
            print("Starting process {}".format(p.name))
            p.start()
    except KeyboardInterrupt:
        print("BOOP")
        for p in processes:
            p.terminate()
        sys.exit(0)

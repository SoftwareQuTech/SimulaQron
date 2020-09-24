import logging
from time import sleep
from typing import List
from importlib import reload
from concurrent.futures import ProcessPoolExecutor as Pool

from netqasm.sdk.shared_memory import reset_memories
from netqasm.logging import get_netqasm_logger
from netqasm.yaml_util import dump_yaml
from netqasm.output import save_all_struct_loggers, reset_struct_loggers
from netqasm.sdk.classical_communication import reset_socket_hub
from netqasm.settings import Formalism
from netqasm.run.app_config import AppConfig

from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings, SimBackend
from simulaqron.toolbox import has_module

logger = get_netqasm_logger()

# TODO similar code to squidasm.run.run, make base-class and subclasses?


_SIMULAQRON_BACKENDS = {
    Formalism.STAB: SimBackend.STABILIZER,
    Formalism.KET: SimBackend.PROJECTQ,
    Formalism.DM: SimBackend.QUTIP,
}


def as_completed(futures, names=None, sleep_time=0):
    futures = list(futures)
    if names is not None:
        names = list(names)
    while len(futures) > 0:
        for i, future in enumerate(futures):
            if future.done():
                futures.pop(i)
                if names is None:
                    yield future
                else:
                    name = names.pop(i)
                    yield future, name
        if sleep_time > 0:
            sleep(sleep_time)


def reset(save_loggers=False):
    if save_loggers:
        save_all_struct_loggers()
    reset_memories()
    reset_socket_hub()
    reset_struct_loggers()
    # Reset logging
    logging.shutdown()
    reload(logging)


def check_sim_backend(sim_backend):
    if sim_backend in [SimBackend.PROJECTQ, SimBackend.QUTIP]:
        assert has_module.main(sim_backend), f"To use {sim_backend} as backend you need to install the package"


def run_sim_backend(node_names, sim_backend):
    logger.debug(f"Starting simulaqron sim_backend process with nodes {node_names}")
    check_sim_backend(sim_backend=sim_backend)
    simulaqron_settings.sim_backend = sim_backend
    network = Network(name="default", nodes=node_names, force=True, new=True)
    network.start(wait_until_running=False)
    return network


def run_applications(
    app_cfgs: List[AppConfig],
    post_function=None,
    instr_log_dir=None,
    network_config=None,
    results_file=None,
    formalism=Formalism.KET,
    flavour=None,
    use_app_config=True,  # whether to give app_config as argument to app's main()
):
    """Executes functions containing application scripts,

    Parameters
    ----------
    applications : dict
        Keys should be names of nodes
        Values should be the functions
    """
    app_names = [app_cfg.app_name for app_cfg in app_cfgs]
    sim_backend = _SIMULAQRON_BACKENDS[formalism]

    with Pool(len(app_names)) as executor:
        # Start the backend process
        network = run_sim_backend(app_names, sim_backend=sim_backend)

        # Start the application processes
        app_futures = []
        for app_cfg in app_cfgs:
            inputs = app_cfg.inputs
            if use_app_config:
                inputs['app_config'] = app_cfg
            future = executor.submit(app_cfg.main_func, **inputs)
            app_futures.append(future)

        # Join the application processes and the backend
        names = [f'app_{app_name}' for app_name in app_names]
        results = {}
        for future, name in as_completed(app_futures, names=names):
            results[name] = future.result()
        if results_file is not None:
            save_results(results=results, results_file=results_file)

        network.stop()

    reset(save_loggers=True)
    return results


def save_results(results, results_file):
    dump_yaml(data=results, file_path=results_file)

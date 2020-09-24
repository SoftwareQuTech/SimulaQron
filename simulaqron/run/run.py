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
from netqasm.sdk.app_config import AppConfig

from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings, SimBackend
from simulaqron.toolbox import has_module

logger = get_netqasm_logger()

# TODO similar code to squidasm.run.run, make base-class and subclasses?


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


def get_backend(formalism):
    if formalism == "STAB":
        backend = SimBackend.STABILIZER
    elif formalism == "KET":
        backend = SimBackend.PROJECTQ
    elif formalism == "DM":
        backend = SimBackend.QUTIP
    else:
        raise TypeError(f"Unknown formalism {formalism}")
    return backend


def check_backend(backend):
    if backend in [SimBackend.PROJECTQ.value, SimBackend.QUTIP.value]:
        assert has_module.main(backend), f"To use {backend} as backend you need to install the package"


def run_backend(node_names, backend):
    logger.debug(f"Starting simulaqron backend process with nodes {node_names}")
    check_backend(backend=backend)
    simulaqron_settings.backend = backend
    network = Network(name="default", nodes=node_names, force=True, new=True)
    network.start(wait_until_running=False)
    return network


def run_applications(
    app_cfgs: List[AppConfig],
    post_function=None,
    instr_log_dir=None,
    network_config=None,
    results_file=None,
    q_formalism=Formalism.KET,
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
    backend = get_backend(formalism=q_formalism)

    with Pool(len(app_names)) as executor:
        # Start the backend process
        network = run_backend(app_names, backend=backend)

        # Start the application processes
        app_futures = []
        for app_cfg in app_cfgs:
            inputs = app_cfgs.inputs
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

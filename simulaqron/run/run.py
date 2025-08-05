import logging
import os
from concurrent.futures import ProcessPoolExecutor as Pool
from importlib import reload
from os import PathLike
from pathlib import Path
from time import sleep
from typing import Callable, Optional, Any, Dict, List, Union

from netqasm.logging.glob import get_netqasm_logger
from netqasm.logging.output import (reset_struct_loggers,
                                    save_all_struct_loggers)
from netqasm.runtime import env, process_logs
from netqasm.runtime.app_config import AppConfig
from netqasm.runtime.application import ApplicationInstance
from netqasm.runtime.settings import Formalism
from netqasm.sdk.classical_communication import reset_socket_hub
from netqasm.sdk.config import LogConfig
from netqasm.sdk.shared_memory import SharedMemoryManager
from netqasm.util.yaml import dump_yaml
from simulaqron.network import Network
from simulaqron.settings import SimBackend, simulaqron_settings
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
    SharedMemoryManager.reset_memories()
    reset_socket_hub()
    reset_struct_loggers()
    # Reset logging
    logging.shutdown()
    reload(logging)


def check_sim_backend(sim_backend: SimBackend):
    if sim_backend in [SimBackend.PROJECTQ, SimBackend.QUTIP]:
        assert has_module.main(sim_backend.value), f"To use {sim_backend} as backend you need to install the package"


def run_sim_backend(node_names: List[str], sim_backend: SimBackend, network_config_file: Optional[str]):
    logger.debug("Starting simulaqron sim_backend process with nodes %s", node_names)
    check_sim_backend(sim_backend)
    simulaqron_settings.sim_backend = sim_backend.value
    new_network = True if network_config_file is None else False
    network = Network(
        name="default",
        nodes=node_names,
        network_config_file=network_config_file,
        force=True,
        new=new_network
    )
    network.start()
    return network


def run_applications(
    app_instance: ApplicationInstance,
    num_rounds: int = 1,
    network_cfg: Union[str, PathLike, Path] = None,  # WARNING - The type of this argument *cannot* be harmonized
    nv_cfg: Any = None,  # Unused; it's here for harmonization with squidasm "simulate_application"
    log_cfg: LogConfig = None,
    formalism: Formalism = Formalism.KET,
    use_app_config: bool = True,
    post_function: Optional[Callable] = None,
    enable_logging: bool = True,
    hardware: Any = None,  # Unused; it's here for harmonization with squidasm "simulate_application"
) -> List[Dict[str, Any]]:
    """Executes functions containing application scripts,

    Parameters
    ----------
    app_instance : ApplicationInstance
        Keys should be names of nodes
        Values should be the functions
    num_rounds : int
        Number executions for this simulation
    network_cfg:
        Path of the network configuration file.
    nv_cfg: Any
        Unused argument. Any parameter given here will be ignored.
    log_cfg: LogConfig
        Configuration for the logging.
    formalism: Formalism
        Qubit formalism to use for the simulation. On this value depends
        The SimulaQron backend to use.
    use_app_config: bool
        Whether to give app_config as argument to app's main()
    post_function: Optional[Callable]
        Function to execute after all rounds have been executed.
    enable_logging: bool
        Whether to enable logging.
    hardware: Any
        Unused argument. Any parameter given here will be ignored.

    Returns
    -------
    List[Dict[str, Any]]
        List of dictionaries describing the application names and the simulation results.
        The i-th entry of the list will correspond to the i-th execution round of the
        simulation.
    """
    # app_names = [app_cfg.app_name for app_cfg in app_cfgs]
    app_names: List[str] = [program.party for program in app_instance.app.programs]
    sim_backend: SimBackend = _SIMULAQRON_BACKENDS[formalism]
    timed_log_dir: str = ""

    if enable_logging:
        log_cfg = LogConfig() if log_cfg is None else log_cfg
        app_instance.logging_cfg = log_cfg

        log_dir = (
            os.path.abspath("./log") if log_cfg.log_dir is None else log_cfg.log_dir
        )
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        timed_log_dir = env.get_timed_log_dir(log_dir)
        app_instance.logging_cfg.log_subroutines_dir = timed_log_dir
        app_instance.logging_cfg.comm_log_dir = timed_log_dir

    results: List[Dict[str, Any]] = []
    if isinstance(network_cfg, str) or isinstance(network_cfg, PathLike):
        net_cfg = str(network_cfg)
    elif isinstance(network_cfg, Path):
        net_cfg = str(network_cfg.resolve())
    else:
        net_cfg = None

    for _ in range(num_rounds):
        with Pool(len(app_names)) as executor:
            # Start the backend process
            network = run_sim_backend(app_names, sim_backend, net_cfg)

            # Start the application processes
            app_futures = []

            programs = app_instance.app.programs
            for program in programs:
                inputs = app_instance.program_inputs[program.party]
                if use_app_config:
                    app_cfg = AppConfig(
                        app_name=program.party,
                        node_name=program.party,  # node name should be same as app name
                        main_func=program.entry,
                        log_config=app_instance.logging_cfg,
                        inputs=inputs,
                    )
                    inputs["app_config"] = app_cfg
                future = executor.submit(program.entry, **inputs)
                app_futures.append(future)

            # for app_cfg in app_cfgs:
            #     inputs = app_cfg.inputs
            #     if use_app_config:
            #         inputs['app_config'] = app_cfg
            #     future = executor.submit(app_cfg.main_func, **inputs)
            #     app_futures.append(future)

            # Join the application processes and the backend
            names = [f'app_{app_name}' for app_name in app_names]
            result = {}
            for future, name in as_completed(app_futures, names=names):
                result[name] = future.result()
            # if results_file is not None:
            #     save_results(results=results, results_file=results_file)
            if enable_logging:
                assert timed_log_dir is not None
                path = os.path.join(timed_log_dir, "results.yaml")
                dump_yaml(data=result, file_path=path)

            results.append(result)
            network.stop()

        reset(save_loggers=True)

    if enable_logging:
        process_logs.make_last_log(log_dir=timed_log_dir)

    return results


def save_results(results, results_file):
    dump_yaml(data=results, file_path=results_file)

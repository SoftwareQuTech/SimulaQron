import logging
import os
from concurrent.futures import ProcessPoolExecutor as Pool
from importlib import reload
from time import sleep

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


def check_sim_backend(sim_backend):
    if sim_backend in [SimBackend.PROJECTQ, SimBackend.QUTIP]:
        assert has_module.main(sim_backend.value), f"To use {sim_backend} as backend you need to install the package"


def run_sim_backend(node_names, sim_backend):
    logger.debug(f"Starting simulaqron sim_backend process with nodes {node_names}")
    check_sim_backend(sim_backend=sim_backend)
    simulaqron_settings.sim_backend = sim_backend.value
    network = Network(name="default", nodes=node_names, force=True, new=True)
    network.start()
    return network


def run_applications(
    app_instance: ApplicationInstance,
    num_rounds=1,
    network_cfg=None,
    log_cfg=None,
    results_file=None,
    formalism=Formalism.KET,
    post_function=None,
    flavour=None,
    enable_logging=True,
    hardware=None,
    use_app_config=True,  # whether to give app_config as argument to app's main()
):
    """Executes functions containing application scripts,

    Parameters
    ----------
    applications : dict
        Keys should be names of nodes
        Values should be the functions
    """
    # app_names = [app_cfg.app_name for app_cfg in app_cfgs]
    app_names = [program.party for program in app_instance.app.programs]
    sim_backend = _SIMULAQRON_BACKENDS[formalism]

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

    with Pool(len(app_names)) as executor:
        # Start the backend process
        network = run_sim_backend(app_names, sim_backend=sim_backend)

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
        results = {}
        for future, name in as_completed(app_futures, names=names):
            results[name] = future.result()
        # if results_file is not None:
        #     save_results(results=results, results_file=results_file)
        if enable_logging:
            assert timed_log_dir is not None
            path = os.path.join(timed_log_dir, "results.yaml")
            dump_yaml(data=results, file_path=path)

        network.stop()

    if enable_logging:
        process_logs.make_last_log(log_dir=timed_log_dir)

    reset(save_loggers=True)
    return [results]


def save_results(results, results_file):
    dump_yaml(data=results, file_path=results_file)

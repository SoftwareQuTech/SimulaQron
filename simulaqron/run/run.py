import logging
import os
import signal

from multiprocess.context import ForkContext as ProcessContext
from multiprocess.pool import ApplyResult
from importlib import reload
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import Callable, Optional, Any, Dict, List, Union, Tuple

from multiprocess.sharedctypes import SynchronizedArray
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
from simulaqron.sdk import SimulaQronConnection
from simulaqron.settings import simulaqron_settings
from simulaqron.settings.simulaqron_config import SimBackend

logger = get_netqasm_logger()

# TODO similar code to squidasm.run.run, make base-class and subclasses?


_SIMULAQRON_BACKENDS = {
    Formalism.STAB: SimBackend.STABILIZER,
    Formalism.KET: SimBackend.PROJECTQ,
    Formalism.DM: SimBackend.QUTIP,
}


def as_completed(futures: List[ApplyResult], names: List[str]) -> List[Tuple[ApplyResult, str]]:
    if len(futures) is not len(names):
        raise RuntimeError("Not all registered applications have an associated name")
    return [(future, name) for future, name in zip(futures, names)]


def reset(save_loggers=False):
    if save_loggers:
        save_all_struct_loggers()
    SharedMemoryManager.reset_memories()
    reset_socket_hub()
    reset_struct_loggers()
    # Reset logging
    logging.shutdown()
    reload(logging)


def setup_sim_backend(sim_backend: SimBackend):
    if sim_backend in [SimBackend.PROJECTQ, SimBackend.QUTIP]:
        assert find_spec(sim_backend.value) is not None,\
            f"To use {sim_backend} as backend you need to install the package"
    simulaqron_settings.sim_backend = sim_backend


def configure_network(node_names: List[str], network_config_file: Optional[str]):
    new_network = True if network_config_file is None else False
    return Network(
        name="default",
        nodes=node_names,
        network_config_file=network_config_file,
        force=True,
        new=new_network
    )


# Global array helper to store PIDs of the children processes running the applications
# Note; this array *will not* store the pids of the QNodeOS and/or Vnode processes
apps_pids: Optional[SynchronizedArray] = None

def _worker_initializer(synced_array: SynchronizedArray):
    # We simply store the reference of the synced object for this process
    global apps_pids
    apps_pids = synced_array


def _app_wrapper(**kwargs):
    global apps_pids
    assert apps_pids is not None
    assert "__instance_num" in kwargs and isinstance(kwargs["__instance_num"], int)
    assert "__entry_function" in kwargs and isinstance(kwargs["__entry_function"], Callable)

    # Save the pid for this worker
    apps_pids[kwargs["__instance_num"]] = os.getpid()
    entry_function = kwargs["__entry_function"]
    del kwargs["__entry_function"]
    del kwargs["__instance_num"]

    # TODO - Signal handler for the SIGINT signal?

    # Call the app main function
    try:
        return entry_function(**kwargs)
    except BaseException as e:
        _signal_other_apps()
        raise e


def _signal_other_apps():
    global apps_pids
    assert apps_pids is not None
    for pid in apps_pids:
        # Do not send SIGINT to self process
        if pid != os.getpid():
            os.kill(pid, signal.SIGINT)


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
    init_func: Callable = None,
) -> List[Dict[str, Any]]:
    """Executes functions containing quantum applications.

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
        Qubit formalism to use for the simulation. The SimulaQron
        backend to use depends on this value.
    use_app_config: bool
        Whether to give app_config as argument to app's main()
    post_function: Optional[Callable]
        Function to execute after all rounds have been executed.
    enable_logging: bool
        Whether to enable logging.
    hardware: Any
        Unused argument. Any parameter given here will be ignored.
    init_func: Callable
        Function to execute to initialize the state of the child processes. The implemented
        executor uses the *spawn* method for creating new processes. In this sense, the
        child processes *do not receive* a copy of the full memory, but only what is needed.
        In particular, all modules will be reimported in the child processes, hence any
        state of the classes *will not transfer* to the child processes.

    Returns
    -------
    List[Dict[str, Any]]
        List of dictionaries describing the application names and the simulation results.
        The i-th entry of the list will correspond to the i-th execution round of the
        simulation.
    """
    # Before all; we need to instruct the OMP library to use a single thread to avoid
    # heavy-processes deadlocks
    os.environ["OMP_NUM_THREADS"] = "1"

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
        simulaqron_settings.network_config_file = Path(net_cfg).resolve()
    elif isinstance(network_cfg, Path):
        net_cfg = str(network_cfg.resolve())
        simulaqron_settings.network_config_file = Path(net_cfg).resolve()
    else:
        net_cfg = None

    for _ in range(num_rounds):
        network = configure_network(app_names, net_cfg)

        # Start the processes that support the simulator: QNodeOS + VirtualNode
        network.start()

        # Create the executor pool
        process_ctx = ProcessContext()
        synced_array =  process_ctx.Array('i', len(app_instance.app.programs))
        executor = process_ctx.Pool(
            processes=len(app_names) + 3,
            initializer=_worker_initializer,
            initargs=[synced_array]
        )

        try:
            with executor:
                SimulaQronConnection.PROCESS_POOL = executor
                global apps_pids
                apps_pids = synced_array
                logger.debug("Starting simulaqron sim_backend process with nodes %s", app_names)
                setup_sim_backend(sim_backend)

                # Start the application processes
                app_futures = []

                programs = app_instance.app.programs
                for i, program in enumerate(programs):
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
                    inputs["__instance_num"] = i
                    inputs["__entry_function"] = program.entry
                    future: ApplyResult = executor.apply_async(
                        _app_wrapper,
                        kwds=inputs,
                    )
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
                futures = as_completed(app_futures, names)
                while len(result) < len(app_names):
                    for future, name in futures:
                        if name in result:
                            continue
                        if future.ready():
                            result[name] = future.get()
                        time.sleep(0.1)
                # if results_file is not None:
                #     save_results(results=results, results_file=results_file)
                if enable_logging:
                    assert timed_log_dir is not None
                    path = os.path.join(timed_log_dir, "results.yaml")
                    dump_yaml(data=result, file_path=path)
                results.append(result)
                network.stop()
        finally:
            network.stop()
        reset(save_loggers=True)

    if enable_logging:
        process_logs.make_last_log(log_dir=timed_log_dir)

    return results


def save_results(results, results_file):
    dump_yaml(data=results, file_path=results_file)

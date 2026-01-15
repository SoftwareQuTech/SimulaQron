import os
import signal
import time
from importlib import reload
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import Callable, Optional, Any, Dict, List, Union, Tuple

from multiprocess.context import ForkContext as ProcessContext
from multiprocess.pool import ApplyResult
from multiprocess.sharedctypes import SynchronizedArray
import logging
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
from simulaqron.settings import simulaqron_settings, network_config
from simulaqron.settings import get_default_network_config_file
from simulaqron.settings.simulaqron_config import SimBackend

logger = logging.getLogger()


_SIMULAQRON_BACKENDS = {
    Formalism.STAB: SimBackend.STABILIZER,
    Formalism.KET: SimBackend.PROJECTQ,
    Formalism.DM: SimBackend.QUTIP,
}


def _as_completed(futures: List[ApplyResult], names: List[str]) -> List[Tuple[ApplyResult, str]]:
    if len(futures) is not len(names):
        raise RuntimeError("Not all registered applications have an associated name")
    return [(future, name) for future, name in zip(futures, names)]


def reset(save_loggers=False):
    """
    Resets the SimulaQron simulation to a clean state, leaving it ready for a new application execution.

    :param save_loggers: Whether to save the NetQASM's struct logs in a file or not.
    :type save_loggers: bool
    """
    if save_loggers:
        save_all_struct_loggers()
    SharedMemoryManager.reset_memories()
    reset_socket_hub()
    reset_struct_loggers()
    # Reset logging
    logging.shutdown()
    reload(logging)


def _setup_sim_backend(sim_backend: SimBackend):
    if sim_backend in [SimBackend.PROJECTQ, SimBackend.QUTIP]:
        assert find_spec(sim_backend.value) is not None, \
            f"To use {sim_backend} as backend you need to install the package"
    simulaqron_settings.sim_backend = sim_backend


# Global array helper to store PIDs of the children processes running the applications
# Note; this array *will not* store the pids of the QNodeOS and/or Vnode processes
_apps_pids: Optional[SynchronizedArray] = None


def _worker_initializer(synced_array: SynchronizedArray):
    # We simply store the reference of the synced object for this process
    global _apps_pids
    _apps_pids = synced_array


def _app_wrapper(**kwargs):
    global _apps_pids
    assert _apps_pids is not None
    assert "__instance_num" in kwargs and isinstance(kwargs["__instance_num"], int)
    assert "__entry_function" in kwargs and isinstance(kwargs["__entry_function"], Callable)

    # Save the pid for this worker
    _apps_pids[kwargs["__instance_num"]] = os.getpid()
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
    global _apps_pids
    assert _apps_pids is not None
    for pid in _apps_pids:
        # Do not send SIGINT to self process
        if pid != os.getpid():
            os.kill(pid, signal.SIGINT)


# The signature of this function was "harmonized" with the `run_applications` method exposed
# by the SquidASM simulator. The idea was to allow programs written in NetQASM to be executed
# both in SimulaQron and SquidASM _with minimal changes_.
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
    """
    Executes functions containing quantum applications.

    :param app_instance: A ``netqasm.runtime.Application`` instance containing the names of the nodes
                         and the function that implements the application. The easiest way to create
                         this object is by using the ``default_app_instance`` from the
                         ``netqasm.runtime.application`` module. Please check the documentation from that
                         method to get more information.
    :type app_instance: ApplicationInstance
    :param num_rounds: Number executions for this simulation.
    :type num_rounds: int
    :param network_cfg: Path of the network configuration file.
    :type network_cfg: str | Path | PathLike | None
    :param nv_cfg: Unused argument. Any parameter given here will be ignored.
    :type nv_cfg: Any
    :param log_cfg: Configuration object for the logging. Check the documentation of :py:class:`LogConfig`
                    for more information abut how to configure the logging.
    :type log_cfg: LogConfig
    :param formalism: Qubit formalism to use for the simulation. The SimulaQron backend to use depends
                      on this value.
    :type formalism: Formalism
    :param use_app_config: Whether to give app_config as argument to app's main().
    :type use_app_config: bool
    :param post_function: Function to execute after all rounds have been executed.
    :type post_function: Optional[Callable]
    :param enable_logging: Whether to enable logging.
    :type enable_logging: bool
    :param hardware: Unused argument. Any parameter given here will be ignored.
    :type hardware: Any
    :param init_func: Function to execute to initialize the state of the child processes. The implemented
                      executor uses the *spawn* method for creating new processes. In this sense, the
                      child processes *do not receive* a copy of the full memory, but only what is needed.
                      In particular, all modules will be reimported in the child processes, hence any
                      state of the classes *will not transfer* to the child processes.
    :type init_func: Callable
    :return: List of dictionaries describing the application names and the simulation results.
             The i-th entry of the list will correspond to the i-th execution round of the simulation.
    :rtype: List[Dict[str, Any]]
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

    # Read the network config
    if network_cfg is None:
        network_cfg = get_default_network_config_file()
   
    network_cfg = Path(network_cfg).resolve()
    network_config.read_from_file(network_cfg)
    network_config.read_from_file(network_cfg)

    for _ in range(num_rounds):
        network = Network(
            nodes=network_config.get_node_names("default"),
            network_config_file=network_cfg,
            network_name="default",
        )
        # Start the processes that support the simulator: QNodeOS + VirtualNode
        network.start()

        # Create the executor pool
        process_ctx = ProcessContext()
        synced_array = process_ctx.Array('i', len(app_instance.app.programs))
        executor = process_ctx.Pool(
            processes=len(app_names) + 3,
            initializer=_worker_initializer,
            initargs=[synced_array]
        )

        try:
            with executor:
                SimulaQronConnection.PROCESS_POOL = executor
                global _apps_pids
                _apps_pids = synced_array
                logger.debug("Starting simulaqron sim_backend process with nodes %s", app_names)
                _setup_sim_backend(sim_backend)

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
                futures = _as_completed(app_futures, names)
                start_time = time.time()
                while len(result) < len(app_names):
                    for future, name in futures:
                        if name in result:
                            continue
                        if future.ready():
                            result[name] = future.get()
                        time.sleep(0.1)
                        waited_for = time.time() - start_time
                        if 0.0 < simulaqron_settings.max_app_waiting_time < waited_for:
                            raise TimeoutError("SimulaQron: max app waiting time exceeded; "
                                               "app did not finish in time. Please check that "
                                               "your code runs correctly standalone. If your "
                                               "code takes a long time to run, please adjust the "
                                               "value of 'max_app_waiting_time' in your simulaqron"
                                               "settings file.")
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

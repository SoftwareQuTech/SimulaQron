from pathlib import Path

from netqasm.runtime.settings import set_simulator

from netqasm.runtime.application import default_app_instance

from simulaqron.run.run import run_applications

set_simulator("simulaqron")
from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import EPRSocket  # noqa: E402


def run_bob():
    epr_socket: EPRSocket = EPRSocket("Alice")
    with NetQASMConnection("Bob", epr_sockets=[epr_socket]):
        entangled_qubit = epr_socket.recv_keep()[0]
        meas = entangled_qubit.measure()
    return meas


if __name__ == "__main__":
    apps = default_app_instance(
        [
            ("Bob", run_bob)
        ]
    )
    network_cfg_path = Path() / "network-alice.json"
    raw_results = run_applications(
        apps, use_app_config=False, enable_logging=False, network_cfg=network_cfg_path.resolve()
    )

    results = {}

    for name, raw_result in raw_results[0].items():
        if isinstance(raw_result, tuple):
            results[name] = tuple(int(result) for result in raw_result)
        else:
            results[name] = int(raw_result)

    print(results)

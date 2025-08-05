from pathlib import Path

from netqasm.runtime.settings import set_simulator
from netqasm.runtime.application import default_app_instance

from simulaqron.run.run import run_applications

set_simulator("simulaqron")

from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import Qubit, EPRSocket  # noqa: E402


def run_alice():
    epr_socket: EPRSocket = EPRSocket("Bob")
    with NetQASMConnection("Alice", epr_sockets=[epr_socket]) as alice:
        # Create a qubit
        q = Qubit(alice)
        q.H()

        # Create entanglement
        epr = epr_socket.create_keep()[0]

        # Teleport
        q.cnot(epr)
        q.H()
        m1 = q.measure()
        m2 = epr.measure()
    return m1, m2


if __name__ == "__main__":
    apps = default_app_instance(
        [
            ("Alice", run_alice)
        ]
    )
    network_cfg_path = Path(__file__).parent / "network-alice.json"
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

from netqasm.runtime.settings import set_simulator

set_simulator("simulaqron")

from netqasm.runtime.application import default_app_instance
from netqasm.sdk.external import NetQASMConnection
from netqasm.sdk import Qubit, EPRSocket

from simulaqron.run.run import run_applications

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


def run_bob():
    epr_socket: EPRSocket = EPRSocket("Alice")
    with NetQASMConnection("Bob", epr_sockets=[epr_socket]):
        entangled_qubit = epr_socket.recv_keep()[0]
        meas = entangled_qubit.measure()
    return meas

if __name__ == "__main__":
    apps = default_app_instance(
        [
            ("Alice", run_alice),
            ("Bob", run_bob)
        ]
    )
    raw_results = run_applications(apps, use_app_config=False, enable_logging=False)

    results = {}

    for name, raw_result in raw_results[0].items():
        if isinstance(raw_result, tuple):
            results[name] = tuple(int(result) for result in raw_result)
        else:
            results[name] = int(raw_result)

    print(results)

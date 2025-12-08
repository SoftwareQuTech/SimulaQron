from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

from simulaqron.settings import simulaqron_settings
simulaqron_settings.network_config_file = "./simulaqron_settings.json"

from netqasm.sdk.external import NetQASMConnection
from netqasm.sdk import Qubit, EPRSocket

def run_alice():
    epr_socket = EPRSocket("Bob")
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
    return int(m1), int(m2)


if __name__ == "__main__":
    results = run_alice()
    print(f"Alice measurements: m1={results[0]}, m2={results[1]}")


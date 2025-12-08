from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

from simulaqron.settings import simulaqron_settings
simulaqron_settings.network_config_file = "./simulaqron_settings.json"

from netqasm.sdk.external import NetQASMConnection
from netqasm.sdk import EPRSocket


def run_bob():
    epr_socket = EPRSocket("Alice")
    with NetQASMConnection("Bob", epr_sockets=[epr_socket]):
        entangled_qubit = epr_socket.recv_keep()[0]
        meas = entangled_qubit.measure()
    return int(meas)


if __name__ == "__main__":
    result = run_bob()
    print(f"Bob measurement: {result}")


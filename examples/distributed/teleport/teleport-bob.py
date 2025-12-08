from netqasm.runtime.settings import set_simulator
set_simulator("simulaqron")

from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import EPRSocket  # noqa: E402


def run_bob():
    epr_socket = EPRSocket("Alice")
    with NetQASMConnection("Bob", epr_sockets=[epr_socket]):
        entangled_qubit = epr_socket.recv_keep()[0]
        meas = entangled_qubit.measure()
    return int(meas)


if __name__ == "__main__":
    result = run_bob()
    print(f"Bob measurement: {result}")

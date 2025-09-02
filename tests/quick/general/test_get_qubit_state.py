from netqasm.runtime.settings import set_simulator

set_simulator("simulaqron")

from netqasm.runtime.application import default_app_instance  # noqa: E402
from netqasm.sdk.external import NetQASMConnection, get_qubit_state  # noqa: E402
from netqasm.sdk import Qubit, EPRSocket  # noqa: E402

from simulaqron.run.run import run_applications  # noqa: E402

class TestGetQubit:
    @staticmethod
    def peek_local_qubit():
        with NetQASMConnection("Alice") as alice:
            q = Qubit(alice)
            q.H()

            alice.flush()
            return get_qubit_state(q)

    @staticmethod
    def alice_teleport():
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

    @staticmethod
    def bob_teleport():
        epr_socket: EPRSocket = EPRSocket("Alice")
        with NetQASMConnection("Bob", epr_sockets=[epr_socket]):
            entangled_qubit = epr_socket.recv_keep()[0]
            meas = entangled_qubit.measure()
        return meas

    def test_get_qubit_state_local(self):
        apps = default_app_instance(
            [
                ("Alice", TestGetQubit.peek_local_qubit)
            ]
        )
        raw_results = run_applications(apps, use_app_config=False, enable_logging=False)

    def test_get_qubit_state_teleport(self):
        apps = default_app_instance(
            [
                ("Alice", TestGetQubit.alice_teleport),
                ("Bob", TestGetQubit.bob_teleport)
            ]
        )
        raw_results = run_applications(apps, use_app_config=False, enable_logging=False)


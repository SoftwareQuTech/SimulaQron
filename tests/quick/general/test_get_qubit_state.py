import numpy as np
import pytest
from netqasm.runtime.settings import set_simulator

from simulaqron.settings import simulaqron_settings, SimBackend

set_simulator("simulaqron")

from netqasm.runtime.application import default_app_instance  # noqa: E402
from netqasm.sdk.external import NetQASMConnection, get_qubit_state  # noqa: E402
from netqasm.sdk import Qubit, EPRSocket  # noqa: E402

from simulaqron.run.run import run_applications, reset  # noqa: E402


class TestGetQubit:
    @pytest.fixture(autouse=True)
    def network(self):
        simulaqron_settings.default_settings()
        simulaqron_settings.sim_backend = SimBackend.PROJECTQ.value
        yield
        simulaqron_settings.default_settings()
        simulaqron_settings.sim_backend = SimBackend.PROJECTQ.value
        reset()

    @staticmethod
    def peek_new_unflushed_qubit():
        with NetQASMConnection("Alice") as alice:
            q_a = Qubit(alice)
            state_a = get_qubit_state(q_a)
            return state_a

    @staticmethod
    def peek_init_qubit():
        with NetQASMConnection("Alice") as alice:
            q_a = Qubit(alice)
            alice.flush()
            state_a = get_qubit_state(q_a)
            return state_a

    @staticmethod
    def peek_local_qubit():
        with NetQASMConnection("Alice") as alice:
            q_a = Qubit(alice)
            q_b = Qubit(alice)
            q_a.H()
            q_b.X()

            alice.flush()
            state_a = get_qubit_state(q_a)
            state_b = get_qubit_state(q_b)
            return state_a, state_b

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

    def test_peek_new_unflushed_qubit(self, network):
        apps = default_app_instance(
            [
                ("Alice", TestGetQubit.peek_new_unflushed_qubit)
            ]
        )
        with pytest.raises(RuntimeError) as exc:
            _ = run_applications(apps, use_app_config=False, enable_logging=False)
        assert "Alice: Qubit 0 not found" in str(exc.value)

    def test_get_basic_state_local(self, network):
        apps = default_app_instance(
            [
                ("Alice", TestGetQubit.peek_init_qubit)
            ]
        )
        raw_results = run_applications(apps, use_app_config=False, enable_logging=False)
        assert np.array_equal(raw_results[0]["app_Alice"], np.array([1.0 + 0j, 0 + 0j]))

    @pytest.mark.skip(reason="todo - fix this test")
    def test_get_qubit_state_local(self, network):
        apps = default_app_instance(
            [
                ("Alice", TestGetQubit.peek_local_qubit)
            ]
        )
        raw_results = run_applications(apps, use_app_config=False, enable_logging=False)
        print(raw_results)

    @pytest.mark.skip(reason="todo - fix this test")
    def test_get_qubit_state_teleport(self, network):
        apps = default_app_instance(
            [
                ("Alice", TestGetQubit.alice_teleport),
                ("Bob", TestGetQubit.bob_teleport)
            ]
        )
        raw_results = run_applications(apps, use_app_config=False, enable_logging=False)
        print(raw_results)

import math

import numpy as np
import pytest
from netqasm.runtime.settings import set_simulator
from netqasm.sdk.classical_communication.message import StructuredMessage

from simulaqron.settings import simulaqron_settings, SimBackend

set_simulator("simulaqron")

from netqasm.runtime.application import default_app_instance  # noqa: E402
from netqasm.sdk.external import NetQASMConnection, Socket, get_qubit_state  # noqa: E402
from netqasm.sdk import Qubit, EPRSocket, set_qubit_state  # noqa: E402

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
            return {"state_a": state_a, "state_b": state_b}

    @staticmethod
    def alice_teleport():
        classical_socket = Socket("Alice", "Bob")
        epr_socket: EPRSocket = EPRSocket("Bob")
        with NetQASMConnection("Alice", epr_sockets=[epr_socket]) as alice:
            # Create a qubit
            q = Qubit(alice)
            set_qubit_state(q, math.pi / 2.0, math.pi / 4.0)
            epr = epr_socket.create_keep()[0]
            alice.flush()
            alice_state = get_qubit_state(q)

            # Teleport
            q.cnot(epr)
            q.H()

            m1 = q.measure()
            m2 = epr.measure()
            alice.flush()

            classical_socket.send_structured(StructuredMessage("Corrections", f"{int(m1)},{int(m2)}"))
        return {"m1": int(m1), "m2": int(m2), "alice_state": alice_state}

    @staticmethod
    def bob_teleport():
        classical_socket = Socket("Bob", "Alice")
        epr_socket: EPRSocket = EPRSocket("Alice")
        with NetQASMConnection("Bob", epr_sockets=[epr_socket]) as bob:
            entangled_qubit = epr_socket.recv_keep()[0]
            bob.flush()

            msg = classical_socket.recv_structured()
            m1, m2 = msg.payload.split(",")
            if int(m2) == 1:
                entangled_qubit.X()
            if int(m1) == 1:
                entangled_qubit.Z()
            bob.flush()
            bob_state = get_qubit_state(entangled_qubit)
        return {"bob_state": bob_state}

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
        assert np.array_equal(raw_results[0]["app_Alice"], np.array([1.0 + 0.0j, 0 + 0.0j]))

    def test_get_qubit_state_local(self, network):
        apps = default_app_instance(
            [
                ("Alice", TestGetQubit.peek_local_qubit)
            ]
        )
        raw_results = run_applications(apps, use_app_config=False, enable_logging=False)
        print(raw_results)
        #qubit A: H(|0>) = 1/sqrt(2) |0> + 1/sqrt(2) |1> =  1/sqrt(2) [1 0] + 1/sqrt(2) [0 1]
        expected = np.array([1.0 / math.sqrt(2.0) + 0.0j, 1.0 / math.sqrt(2.0) + 0.0j])
        # Note: Due to loss in serialization, we allow a tolerance of 1e-5 when comparing all the members
        assert np.isclose(raw_results[0]["app_Alice"]["state_a"], expected, rtol=1e-5).all()
        # qubit B: X(|0>) = |1> = [0 1]
        assert np.array_equal(raw_results[0]["app_Alice"]["state_b"], np.array([0.0 + 0.0j, 1 + 0.0j]))

    def test_get_qubit_state_teleport(self, network):
        apps = default_app_instance(
            [
                ("Alice", TestGetQubit.alice_teleport),
                ("Bob", TestGetQubit.bob_teleport)
            ]
        )
        raw_results = run_applications(apps, use_app_config=False, enable_logging=False)
        assert np.array_equal(raw_results[0]["app_Alice"]["alice_state"], raw_results[0]["app_Bob"]["bob_state"])

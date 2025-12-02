import pytest

from netqasm.runtime.settings import set_simulator

from simulaqron.run.run import run_applications

set_simulator("simulaqron")

from netqasm.runtime.application import default_app_instance  # noqa: E402
from netqasm.sdk.external import NetQASMConnection  # noqa: E402
from netqasm.sdk import Qubit  # noqa: E402


class TestFreeQubit:
    @staticmethod
    def too_many_qubits():
        with NetQASMConnection("Alice", max_qubits=2) as alice:
            q_a = Qubit(alice)  # noqa: F841
            q_b = Qubit(alice)  # noqa: F841
            q_c = Qubit(alice)  # noqa: F841
            alice.flush()

    @staticmethod
    def release_qubit():
        with NetQASMConnection("Alice", max_qubits=2) as alice:
            q_a = Qubit(alice)  # noqa: F841
            q_b = Qubit(alice)
            q_b.free()
            alice.flush()
            return len(alice.active_qubits)

    @staticmethod
    def release_qubit_b():
        with NetQASMConnection("Alice", max_qubits=2) as alice:
            q_a = Qubit(alice)  # noqa: F841
            q_b = Qubit(alice)
            alice.flush()
            q_b.free()
            alice.flush()
            return len(alice.active_qubits)

    # This program compiles to the following NetQASM subroutine:
    # set Q0 0
    # qalloc Q0
    # init Q0
    # set Q0 1
    # qalloc Q0
    # init Q0
    # set Q0 1
    # qfree Q0
    # set Q0 2
    # qalloc Q0
    # init Q0
    # Note that this subroutine uses 3 virtual qubit addresses, *but* only uses
    # 2 physical qubits, since virtual address 1 is freed *before* allocating
    # virtual address 2. Executing that test case in SimulaQron and SquidASM
    # (configuring a QPU with 2 physical qubits) have different behaviors:
    # In SquidASM, this works correctly, since the executor class (which handles
    # the execution of the subroutine) assigns dynamically the physical qubit
    # addresses, meaning that the executor *realizes* that virtual qubit 1 is
    # freed, so it has physical availability for allocating virtual qubit 2.
    # In SimulaQron, this doesn't work correctly. SimulaQron uses the NetQASM
    # built-in memory manager (netqasm.sdk.memmgr module), which assigns the
    # physical qubit ids. This implementation is flawed, since *it assumes
    # the virtual id will map to the same physical id*. In this case, a QPU
    # with 2 qubits, whill have physical qubit 0, and 1. When trying to allocate
    # a physical qubit ID for virtual qubit 2, the memory manager will fail, since
    # it will try to allocate it to physical qubit 2, which is outside the
    # allowed physical qubit ids
    @staticmethod
    def release_and_reuse_qubit():
        with NetQASMConnection("Alice", max_qubits=2) as alice:
            q_a = Qubit(alice)  # noqa: F841
            q_b = Qubit(alice)
            q_b.free()
            q_c = Qubit(alice)  # noqa: F841
            alice.flush()
            return len(alice.active_qubits)

    @staticmethod
    def release_and_reuse_qubit_b():
        with NetQASMConnection("Alice", max_qubits=2) as alice:
            q_a = Qubit(alice)  # noqa: F841
            q_b = Qubit(alice)
            q_b.free()
            alice.flush()
            q_c = Qubit(alice)  # noqa: F841
            alice.flush()
            return len(alice.active_qubits)

    # Here we define the quantum programs used in the tests
    def test_too_many_qubits(self):
        apps = default_app_instance(
            [
                ("Alice", TestFreeQubit.too_many_qubits)
            ]
        )
        with pytest.raises(RuntimeError) as exc:
            _ = run_applications(apps, use_app_config=False, enable_logging=False)
        assert "Virtual address 2 is outside the unit module (app ID 0) which has length 2" in str(exc.value)

    def test_release_qubit(self):
        apps = default_app_instance(
            [
                ("Alice", TestFreeQubit.release_qubit)
            ]
        )
        result = run_applications(apps, use_app_config=False, enable_logging=False)
        assert result[0]["app_Alice"] == 1

    def test_release_qubit_b(self):
        apps = default_app_instance(
            [
                ("Alice", TestFreeQubit.release_qubit_b)
            ]
        )
        result = run_applications(apps, use_app_config=False, enable_logging=False)
        assert result[0]["app_Alice"] == 1

    def test_release_and_reuse_qubit(self):
        apps = default_app_instance(
            [
                ("Alice", TestFreeQubit.release_and_reuse_qubit)
            ]
        )
        result = run_applications(apps, use_app_config=False, enable_logging=False)
        assert result[0]["app_Alice"] == 2

    def test_release_and_reuse_qubit_b(self):
        apps = default_app_instance(
            [
                ("Alice", TestFreeQubit.release_and_reuse_qubit_b)
            ]
        )
        result = run_applications(apps, use_app_config=False, enable_logging=False)
        assert result[0]["app_Alice"] == 2

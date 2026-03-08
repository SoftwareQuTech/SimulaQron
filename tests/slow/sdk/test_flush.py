#
# Tests for mid-circuit flush behavior.
#
# The NetQASM programming model batches quantum operations inside a
# `with NetQASMConnection(...) as conn:` block.  Measurement results are
# "futures" — calling int(m) before the batch has executed is undefined.
#
# There are two ways to force execution:
#   1. Exit the `with` block (automatic flush on __exit__).
#   2. Call conn.flush() inside the block.
#
# These tests verify that flush() works mid-circuit so that users can:
#   - Read measurement results inside the with block
#   - Make classical decisions based on those results
#   - Continue with more quantum operations
#
import pytest

from netqasm.sdk.qubit import Qubit

from simulaqron.settings import simulaqron_settings, network_config
from simulaqron.settings.simulaqron_config import SimBackend
from simulaqron.network import Network
from simulaqron.sdk.connection import SimulaQronConnection
from simulaqron.run.run import reset


class TestFlush:
    @pytest.fixture(autouse=True)
    def network(self):
        simulaqron_settings.default_settings()
        simulaqron_settings.sim_backend = SimBackend.STABILIZER
        default_net_cfg_path = network_config.using_default_network()
        network = Network(nodes=["Alice"], network_config_file=default_net_cfg_path)
        network.start()
        yield
        network.stop()
        reset()

    def test_flush_makes_measurement_readable(self):
        """After flush(), int(m) should return 0 or 1."""
        with SimulaQronConnection("Alice") as conn:
            q = Qubit(conn)
            q.H()
            m = q.measure()
            conn.flush()
            m_val = int(m)
            assert m_val in (0, 1)

    def test_flush_deterministic_zero(self):
        """Measure |0> — should always give 0."""
        with SimulaQronConnection("Alice") as conn:
            q = Qubit(conn)
            # no gates → |0>
            m = q.measure()
            conn.flush()
            m_val = int(m)
            assert m_val == 0

    def test_flush_deterministic_one(self):
        """Prepare |1> with X gate — should always give 1."""
        with SimulaQronConnection("Alice") as conn:
            q = Qubit(conn)
            q.X()
            m = q.measure()
            conn.flush()
            m_val = int(m)
            assert m_val == 1

    def test_classical_decision_after_flush(self):
        """
        Mid-circuit classical logic: measure, flush, decide, then do more
        quantum operations based on the measurement result.

        Prepare |1> (via X), measure, flush, read result.
        If result is 1, prepare a new qubit in |0> (no gate).
        If result is 0, prepare a new qubit in |1> (X gate).
        Either way, the second qubit's measurement should be (1 - first).
        """
        with SimulaQronConnection("Alice") as conn:
            q1 = Qubit(conn)
            q1.X()  # |1>
            m1 = q1.measure()
            conn.flush()
            m1_val = int(m1)
            assert m1_val == 1

            # Classical decision: prepare opposite state
            q2 = Qubit(conn)
            if m1_val == 1:
                pass  # leave as |0>
            else:
                q2.X()  # flip to |1>
            m2 = q2.measure()
            conn.flush()
            m2_val = int(m2)
            assert m2_val == 0
            assert m1_val + m2_val == 1

    def test_multiple_flush_rounds(self):
        """
        Three rounds of measure-flush-decide, each building on previous results.
        This simulates a state-machine-like quantum program.
        """
        results = []
        with SimulaQronConnection("Alice", max_qubits=5) as conn:
            # Round 1: prepare |+>, measure
            q1 = Qubit(conn)
            q1.H()
            m1 = q1.measure()
            conn.flush()
            r1 = int(m1)
            results.append(r1)
            assert r1 in (0, 1)

            # Round 2: if round 1 gave 0, prepare |1>; if 1, prepare |0>
            q2 = Qubit(conn)
            if r1 == 0:
                q2.X()
            m2 = q2.measure()
            conn.flush()
            r2 = int(m2)
            results.append(r2)
            # r2 should be the opposite of r1
            assert r2 == 1 - r1

            # Round 3: prepare qubit based on XOR of previous results
            q3 = Qubit(conn)
            if r1 ^ r2 == 1:
                q3.X()
            m3 = q3.measure()
            conn.flush()
            r3 = int(m3)
            results.append(r3)
            # r1 XOR r2 is always 1 (since r2 = 1-r1), so r3 should be 1
            assert r3 == 1

        assert len(results) == 3

    def test_flush_then_exit_still_works(self):
        """
        Values read after flush() inside the block should still be
        valid after exiting the block.
        """
        with SimulaQronConnection("Alice") as conn:
            q = Qubit(conn)
            q.X()
            m = q.measure()
            conn.flush()
            inner_val = int(m)

        outer_val = int(m)
        assert inner_val == outer_val == 1

#
# Copyright (c) 2017, Stephanie Wehner and Axel Dahlberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import numpy as np
import pytest
from netqasm.runtime.application import default_app_instance

from simulaqron.sdk.connection import SimulaQronConnection
from netqasm.sdk import Qubit, EPRSocket
from simulaqron.sdk.socket import Socket
from simulaqron.run.run import run_applications
from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings
from simulaqron.run.run import reset


def calc_exp_values(q):
    """
    Calculates the expected value for measurements in the X,Y and Z basis and returns these in a tuple.
    q should be a numpy array representing a qubit density matrix
    """
    # eigenvectors
    z0 = np.array([[1], [0]])
    z1 = np.array([[0], [1]])
    x1 = 1 / np.sqrt(2) * (z0 - z1)
    y1 = 1 / np.sqrt(2) * (z0 - 1j * z1)

    # projectors
    P_X1 = np.dot(x1, np.transpose(np.conj(x1)))
    P_Y1 = np.dot(y1, np.transpose(np.conj(y1)))
    P_Z1 = np.dot(z1, np.transpose(np.conj(z1)))

    # probabilities
    p_x = np.real(np.trace(np.dot(P_X1, q)))
    p_y = np.real(np.trace(np.dot(P_Y1, q)))
    p_z = np.real(np.trace(np.dot(P_Z1, q)))

    return p_x, p_y, p_z


def prep_CNOT_control(conn):
    q1 = Qubit(conn)
    q2 = Qubit(conn)
    q1.H()
    q1.cnot(q2)
    q2.measure()
    return q1


def prep_CNOT_target(conn):
    q1 = Qubit(conn)
    q2 = Qubit(conn)
    q1.H()
    q1.cnot(q2)
    q1.measure()
    return q2


def prep_CPHASE_control(conn):
    q1 = Qubit(conn)
    q2 = Qubit(conn)
    q1.H()
    q2.H()
    q1.cphase(q2)
    q2.H()
    q2.measure()
    return q1


def prep_CPHASE_target(conn):
    q1 = Qubit(conn)
    q2 = Qubit(conn)
    q1.H()
    q2.H()
    q1.cphase(q2)
    q2.H()
    q1.measure()
    return q2


def EPR_Alice():
    epr_socket = EPRSocket("Bob")
    with SimulaQronConnection("Alice", epr_sockets=[epr_socket]):
        qA = epr_socket.create_keep()[0]
        m = qA.measure()
        # "flush" is not necessary, since it is triggered when exiting the context.
    return m


def EPR_Bob():
    epr_socket = EPRSocket("Alice")
    with SimulaQronConnection("Bob", epr_sockets=[epr_socket]):
        qB = epr_socket.recv_keep()[0]
        m = qB.measure()
        # "flush" is not necessary, since it is triggered when exiting the context.
    return m


def teleport_alice():
    socket = Socket("Alice", "Bob")
    epr_socket = EPRSocket("Bob")
    with SimulaQronConnection("Alice", epr_sockets=[epr_socket]) as alice:
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

    # Send the correction information
    msg = str((int(m1), int(m2)))
    socket.send(msg)
    return m1, m2


def teleport_bob():
    socket = Socket("Bob", "Alice")
    epr_socket = EPRSocket("Alice")
    with SimulaQronConnection("Bob", epr_sockets=[epr_socket]) as bob:
        epr = epr_socket.recv_keep()[0]
        bob.flush()

        # Get the corrections
        msg = socket.recv()

        m1, m2 = eval(msg)
        if m2 == 1:
            epr.X()
        if m1 == 1:
            epr.Z()
        meas = epr.measure()
    return meas


def prep_mixed_state():
    q = np.eye(2) / 2
    return q


def prep_H_state():
    q = np.array([[1], [0]])
    H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    q2 = np.dot(H, q)
    return np.dot(q2, np.transpose(np.conj(q2)))


# TODO - We can test these things better when we have implemented a get_qubit_state function for simulaqron
#  for now, we will perform tests based on the tomography function.
class TestTwoQubitGates:
    iterations = 100

    @pytest.fixture
    def network(self):
        print(f"Testing two qubit gates with {self.iterations} iterations\n")

        simulaqron_settings.default_settings()
        network = Network(nodes=["Alice", "Bob"], force=True)
        network.start(wait_until_running=True)
        yield network

        network.stop()
        simulaqron_settings.default_settings()
        reset()

    def test_CNOT_control(self, network):
        with SimulaQronConnection("Bob") as conn:
            # Test CNOT control
            exp_values = calc_exp_values(prep_mixed_state())
            ans = conn.test_preparation(prep_CNOT_control, exp_values, iterations=self.iterations)
            assert ans

    def test_CNOT_target(self, network):
        with SimulaQronConnection("Bob") as conn:
            # Test CNOT target
            exp_values = calc_exp_values(prep_mixed_state())
            ans = conn.test_preparation(prep_CNOT_target, exp_values, iterations=self.iterations)
            assert ans

    def test_CPHASE_control(self, network):
        with SimulaQronConnection("Bob") as conn:
            # Test CPHASE control
            exp_values = calc_exp_values(prep_mixed_state())
            ans = conn.test_preparation(prep_CPHASE_control, exp_values, iterations=self.iterations)
            assert ans

    def test_CPHASE_target(self, network):
        with SimulaQronConnection("Bob") as conn:
            # Test CPHASE target
            exp_values = calc_exp_values(prep_mixed_state())
            ans = conn.test_preparation(prep_CPHASE_target, exp_values, iterations=self.iterations)
            assert ans

    # Tests using multiple nodes

    def test_EPRS(self, network):
        apps = default_app_instance(
            [
                ("Alice", EPR_Alice),
                ("Bob", EPR_Bob)
            ]
        )
        results = run_applications(apps, use_app_config=False, enable_logging=False, num_rounds=self.iterations)
        # both sides MUST measure the same state
        assert int(results[0]["app_Alice"]) == int(results[0]["app_Bob"])

    def test_teleport(self, network):
        # To avoid stalling the simulation, the applications *need* to run
        # in parallel. For this reason, we use the "run_applications" method
        # which spawns a process for each node
        apps = default_app_instance(
            [
                ("Alice", teleport_alice),
                ("Bob", teleport_bob)
            ]
        )
        results = run_applications(apps, use_app_config=False, enable_logging=False, num_rounds=self.iterations)
        #print(results)

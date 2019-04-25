import os
import logging
import unittest
import numpy as np
import multiprocessing as mp

from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from simulaqron.general.hostConfig import socketsConfig
from simulaqron.local.setup import setup_local, assemble_qubit
from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings
from simulaqron.toolbox.stabilizerStates import StabilizerState


class localNode(pb.Root):
    def __init__(self, node, classicalNet):
        self.node = node
        self.classicalNet = classicalNet

        self.virtRoot = None
        self.qReg = None

        self.num_qubits_received = 0

    def set_virtual_node(self, virtRoot):
        self.virtRoot = virtRoot

    def set_virtual_reg(self, qReg):
        self.qReg = qReg

    # This can be called by Alice or Bob to tell Charlie where to get the qubit and what to do next
    @inlineCallbacks
    def remote_receive_two_qubits(self, virtualNum):
        """
        Recover the qubit from Alice. We should now have a tripartite GHZ state

        Arguments
        virtualNum	number of the virtual qubit corresponding to the EPR pair received
        """

        logging.debug("LOCAL %s: Getting reference to qubit number %d.", self.node.name, virtualNum)

        if self.num_qubits_received == 0:
            self.q1 = yield self.virtRoot.callRemote("get_virtual_ref", virtualNum)
            self.num_qubits_received += 1
            return True
        else:
            self.q2 = yield self.virtRoot.callRemote("get_virtual_ref", virtualNum)
            correct = yield self.got_both()
            return correct

    @inlineCallbacks
    def got_both(self):
        """
        Recover the qubit from Bob. We should now have a tripartite GHZ state

        Arguments
        virtualNum	number of the virtual qubit corresponding to the EPR pair received
        """

        logging.debug("LOCAL %s: Got both qubits from Alice and Bob.", self.node.name)

        # We'll test an operation that will cause a merge of the two remote registers
        yield self.q1.callRemote("apply_H")
        yield self.q1.callRemote("cnot_onto", self.q2)

        if simulaqron_settings.backend == "qutip":
            # Output state
            (realRho, imagRho) = yield self.virtRoot.callRemote("get_multiple_qubits", [self.q1, self.q2])
            rho = assemble_qubit(realRho, imagRho)
            expectedRho = [[0.5, 0, 0, 0.5], [0, 0, 0, 0], [0, 0, 0, 0], [0.5, 0, 0, 0.5]]
            correct = np.all(np.isclose(rho, expectedRho))
        elif simulaqron_settings.backend == "projectq":
            (realvec, imagvec) = yield self.virtRoot.callRemote("get_register_RI", self.q1)
            state = [r + (1j * j) for r, j in zip(realvec, imagvec)]
            expectedState = [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)]
            correct = np.all(np.isclose(state, expectedState))
        elif simulaqron_settings.backend == "stabilizer":
            (array, _) = yield self.virtRoot.callRemote("get_register_RI", self.q1)
            state = StabilizerState(array)
            expectedState = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
            correct = state == expectedState
        else:
            ValueError("Unknown backend {}".format(simulaqron_settings.backend))

        return bool(correct)

    # This can be called by Alice to tell Bob where to get the qubit and what corrections to apply
    @inlineCallbacks
    def remote_receive_one_qubit(self, virtualNum, cnot_direction=0):
        """
        Recover the qubit from teleportation.

        Arguments
        a,b		received measurement outcomes from Alice
        virtualNum	number of the virtual qubit corresponding to the EPR pair received
        """

        logging.debug("LOCAL %s: Getting reference to qubit number %d.", self.node.name, virtualNum)

        # Get a reference to our side of the EPR pair
        qA = yield self.virtRoot.callRemote("get_virtual_ref", virtualNum)

        # Create a fresh qubit
        q = yield self.virtRoot.callRemote("new_qubit_inreg", self.qReg)

        # Create the GHZ state by entangling the fresh qubit
        if cnot_direction == 0:
            yield qA.callRemote("apply_H")
            yield qA.callRemote("cnot_onto", q)
        else:
            yield q.callRemote("apply_H")
            yield q.callRemote("cnot_onto", qA)

        if simulaqron_settings.backend == "qutip":
            # Output state
            (realRho, imagRho) = yield self.virtRoot.callRemote("get_multiple_qubits", [qA, q])
            rho = assemble_qubit(realRho, imagRho)
            expectedRho = [[0.5, 0, 0, 0.5], [0, 0, 0, 0], [0, 0, 0, 0], [0.5, 0, 0, 0.5]]
            correct = np.all(np.isclose(rho, expectedRho))
        elif simulaqron_settings.backend == "projectq":
            (realvec, imagvec) = yield self.virtRoot.callRemote("get_register_RI", qA)
            state = [r + (1j * j) for r, j in zip(realvec, imagvec)]
            expectedState = [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)]
            correct = np.all(np.isclose(state, expectedState))
        elif simulaqron_settings.backend == "stabilizer":
            (array, _) = yield self.virtRoot.callRemote("get_register_RI", qA)
            state = StabilizerState(array)
            expectedState = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
            correct = state == expectedState
        else:
            ValueError("Unknown backend {}".format(simulaqron_settings.backend))

        return bool(correct)


# @for_all_methods()
class TestMerge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = []
        cls.node_codes = []

        cls.processes = []
        cls.processes_to_wait_for = None

        simulaqron_settings.default_settings()
        path_to_here = os.path.dirname(os.path.abspath(__file__))
        network_config_file = os.path.join(path_to_here, "configs", "network.json")
        simulaqron_settings.network_config_file = network_config_file
        nodes = ["Alice", "Bob", "Charlie"]
        cls.network = Network(nodes=nodes, force=True)
        cls.network.start()

    @classmethod
    def tearDownClass(cls):
        for p in cls.processes:
            p.terminate()

        cls.network.stop()
        reactor.crash()
        simulaqron_settings.default_settings()

    @staticmethod
    def setup_node(name, node_code, classical_net_file, send_end):
        # This file defines the network of virtual quantum nodes
        virtualFile = os.path.join(os.path.dirname(__file__), "configs", "network.json")

        # This file defines the nodes acting as servers in the classical communication network
        classicalFile = os.path.join(os.path.dirname(__file__), "configs", classical_net_file)

        # Read configuration files for the virtual quantum, as well as the classical network
        virtualNet = socketsConfig(virtualFile)
        classicalNet = socketsConfig(classicalFile)

        # Check if we should run a local classical server. If so, initialize the code
        # to handle remote connections on the classical communication network
        if name in classicalNet.hostDict:
            lNode = localNode(classicalNet.hostDict[name], classicalNet)
        else:
            lNode = None

        # Set up the local classical server if applicable, and connect to the virtual
        # node and other classical servers. Once all connections are set up, this will
        # execute the function runClientNode
        setup_local(name, virtualNet, classicalNet, lNode, node_code, send_end)

    def run_test(self, classical_net_file):
        mp.set_start_method("spawn", force=True)
        pipe_list = []
        for name, node_code in zip(self.nodes, self.node_codes):
            recv_end, send_end = mp.Pipe(False)
            p = mp.Process(target=self.setup_node,
                           args=[name, node_code, classical_net_file, send_end],
                           name=name)
            self.processes.append(p)
            pipe_list.append(recv_end)

        for p in self.processes:
            p.start()

        if self.processes_to_wait_for is None:
            for p in self.processes:
                p.join()
        else:
            for i in self.processes_to_wait_for:
                self.processes[i].join()
        results = [pipe.recv() for pipe in pipe_list]
        self.assertTrue(all(results))


class TestBothLocal(TestMerge):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.nodes = ["Alice"]
        cls.node_codes = [cls.alice]

    @classmethod
    @inlineCallbacks
    def alice(cls, qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execute for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)

        # Create 2 qubits
        qA = yield virtRoot.callRemote("new_qubit_inreg", qReg)
        qB = yield virtRoot.callRemote("new_qubit_inreg", qReg)

        # Put qubits A and B in an EPR state
        yield qA.callRemote("apply_H")
        yield qA.callRemote("cnot_onto", qB)

        if simulaqron_settings.backend == "qutip":
            # Output state
            (realRho, imagRho) = yield virtRoot.callRemote("get_multiple_qubits", [qA, qB])
            rho = assemble_qubit(realRho, imagRho)
            expectedRho = [[0.5, 0, 0, 0.5], [0, 0, 0, 0], [0, 0, 0, 0], [0.5, 0, 0, 0.5]]
            correct = np.all(np.isclose(rho, expectedRho))
        elif simulaqron_settings.backend == "projectq":
            (realvec, imagvec, _, _, _) = yield virtRoot.callRemote("get_register", qA)
            state = [r + (1j * j) for r, j in zip(realvec, imagvec)]
            expectedState = [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)]
            correct = np.all(np.isclose(state, expectedState))
        elif simulaqron_settings.backend == "stabilizer":
            (array, _, _, _, _) = yield virtRoot.callRemote("get_register", qA)
            state = StabilizerState(array)
            expectedState = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
            correct = state == expectedState
        else:
            ValueError("Unknown backend {}".format(simulaqron_settings.backend))

        send_end.send(correct)

        reactor.stop()

    def test(self):
        self.run_test("Alice.cfg")


class TestBothLocalNotSameReg(TestBothLocal):
    @classmethod
    @inlineCallbacks
    def alice(cls, qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execute for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)
        # Create a second register
        newReg = yield virtRoot.callRemote("add_register")

        # Create 2 qubits
        qA = yield virtRoot.callRemote("new_qubit_inreg", qReg)
        qB = yield virtRoot.callRemote("new_qubit_inreg", newReg)

        # Put qubits A and B in an EPR state
        yield qA.callRemote("apply_H")
        yield qA.callRemote("cnot_onto", qB)

        if simulaqron_settings.backend == "qutip":
            # Output state
            (realRho, imagRho) = yield virtRoot.callRemote("get_multiple_qubits", [qA, qB])
            rho = assemble_qubit(realRho, imagRho)
            expectedRho = [[0.5, 0, 0, 0.5], [0, 0, 0, 0], [0, 0, 0, 0], [0.5, 0, 0, 0.5]]
            correct = np.all(np.isclose(rho, expectedRho))
        elif simulaqron_settings.backend == "projectq":
            (realvec, imagvec, _, _, _) = yield virtRoot.callRemote("get_register", qA)
            state = [r + (1j * j) for r, j in zip(realvec, imagvec)]
            expectedState = [1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)]
            correct = np.all(np.isclose(state, expectedState))
        elif simulaqron_settings.backend == "stabilizer":
            (array, _, _, _, _) = yield virtRoot.callRemote("get_register", qA)
            state = StabilizerState(array)
            expectedState = StabilizerState([[1, 1, 0, 0], [0, 0, 1, 1]])
            correct = state == expectedState
        else:
            ValueError("Unknown backend {}".format(simulaqron_settings.backend))

        send_end.send(correct)

        reactor.stop()


class TestBothRemote(TestMerge):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nodes = ["Alice", "Bob", "Charlie"]
        cls.node_codes = [cls.alice, cls.bob, cls.charlie]
        cls.processes_to_wait_for = [0, 1]  # Don't wait for charlie

    @staticmethod
    @inlineCallbacks
    def alice(qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execute for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)

        # Create qubit
        qA = yield virtRoot.callRemote("new_qubit_inreg", qReg)

        # Instruct the virtual node to transfer the qubit
        remoteNum = yield virtRoot.callRemote("send_qubit", qA, "Charlie")
        logging.debug("LOCAL %s: Remote qubit is %d.", myName, remoteNum)

        # Tell Charlie the number of the virtual qubit so the can use it locally
        # and extend it to a GHZ state with Charlie
        charlie = classicalNet.hostDict["Charlie"]
        correct = yield charlie.root.callRemote("receive_two_qubits", remoteNum)

        send_end.send(correct)

        reactor.stop()

    @staticmethod
    @inlineCallbacks
    def bob(qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execute for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)

        # Create qubits
        qB = yield virtRoot.callRemote("new_qubit_inreg", qReg)

        # Instruct the virtual node to transfer the qubit
        remoteNum = yield virtRoot.callRemote("send_qubit", qB, "Charlie")
        logging.debug("LOCAL %s: Remote qubit is %d.", myName, remoteNum)

        # Tell Charlie the number of the virtual qubit so the can use it locally
        # and extend it to a GHZ state with Charlie
        charlie = classicalNet.hostDict["Charlie"]
        correct = yield charlie.root.callRemote("receive_two_qubits", remoteNum)

        send_end.send(correct)

        reactor.stop()

    @staticmethod
    def charlie(qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execture for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)
        send_end.send(True)

    def test(self):
        self.run_test("AliceBobCharlie.cfg")


class TestBothRemoteSameNodeDiffReg(TestMerge):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nodes = ["Alice", "Bob"]
        cls.node_codes = [cls.alice, cls.bob]
        cls.processes_to_wait_for = [0]  # Don't wait for charlie

    @staticmethod
    @inlineCallbacks
    def alice(qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execute for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)

        # Create new register
        newReg = yield virtRoot.callRemote("new_register")

        # Create 2 qubits
        qA = yield virtRoot.callRemote("new_qubit_inreg", qReg)
        qB = yield virtRoot.callRemote("new_qubit_inreg", newReg)

        # Instruct the virtual node to transfer the qubit
        remoteNumA = yield virtRoot.callRemote("send_qubit", qA, "Bob")
        remoteNumB = yield virtRoot.callRemote("send_qubit", qB, "Bob")
        logging.debug("LOCAL %s: Remote qubit is %d.", myName, remoteNumA)
        logging.debug("LOCAL %s: Remote qubit is %d.", myName, remoteNumB)

        # Tell Charlie the number of the virtual qubit so the can use it locally
        # and extend it to a GHZ state with Charlie
        bob = classicalNet.hostDict["Bob"]
        correct1 = yield bob.root.callRemote("receive_two_qubits", remoteNumA)
        correct2 = yield bob.root.callRemote("receive_two_qubits", remoteNumB)
        correct = correct1 and correct2

        send_end.send(correct)

        reactor.stop()

    @staticmethod
    def bob(qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execture for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)
        send_end.send(True)

    def test(self):
        self.run_test("AliceBob.cfg")


class TestBothRemoteSameNodeSameReg(TestBothRemoteSameNodeDiffReg):
    @staticmethod
    @inlineCallbacks
    def alice(qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execute for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)

        # Create 2 qubits
        qA = yield virtRoot.callRemote("new_qubit_inreg", qReg)
        qB = yield virtRoot.callRemote("new_qubit_inreg", qReg)

        # # Put qubits A and B in an EPR state
        # yield qA.callRemote("apply_H")
        # yield qA.callRemote("cnot_onto", qB)

        # Send qubit B to Bob
        # Instruct the virtual node to transfer the qubit
        remoteNumA = yield virtRoot.callRemote("send_qubit", qA, "Bob")
        remoteNumB = yield virtRoot.callRemote("send_qubit", qB, "Bob")
        logging.debug("LOCAL %s: Remote qubit is %d.", myName, remoteNumA)
        logging.debug("LOCAL %s: Remote qubit is %d.", myName, remoteNumB)

        # Tell Charlie the number of the virtual qubit so the can use it locally
        # and extend it to a GHZ state with Charlie
        bob = classicalNet.hostDict["Bob"]
        correct1 = yield bob.root.callRemote("receive_two_qubits", remoteNumA)
        correct2 = yield bob.root.callRemote("receive_two_qubits", remoteNumB)
        correct = correct1 and correct2

        send_end.send(correct)

        reactor.stop()


class TestRemoteAtoB(TestBothRemoteSameNodeDiffReg):
    @staticmethod
    @inlineCallbacks
    def alice(qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execute for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)

        # Create qubit
        qA = yield virtRoot.callRemote("new_qubit_inreg", qReg)

        # Instruct the virtual node to transfer the qubit
        remoteNum = yield virtRoot.callRemote("send_qubit", qA, "Bob")
        logging.debug("LOCAL %s: Remote qubit is %d.", myName, remoteNum)

        # Tell Bob the number of the virtual qubit so the can use it locally
        bob = classicalNet.hostDict["Bob"]
        correct = yield bob.root.callRemote("receive_one_qubit", remoteNum, cnot_direction=0)

        send_end.send(correct)

        reactor.stop()


class TestRemoteBtoA(TestBothRemoteSameNodeDiffReg):
    @staticmethod
    @inlineCallbacks
    def alice(qReg, virtRoot, myName, classicalNet, send_end):
        """
        Code to execute for the local client node. Called if all connections are established.

        Arguments
        qReg		quantum register (twisted object supporting remote method calls)
        virtRoot	virtual quantum ndoe (twisted object supporting remote method calls)
        myName		name of this node (string)
        classicalNet	servers in the classical communication network (dictionary of hosts)
        """

        logging.debug("LOCAL %s: Runing client side program.", myName)

        # Create qubit
        qA = yield virtRoot.callRemote("new_qubit_inreg", qReg)

        # Instruct the virtual node to transfer the qubit
        remoteNum = yield virtRoot.callRemote("send_qubit", qA, "Bob")
        logging.debug("LOCAL %s: Remote qubit is %d.", myName, remoteNum)

        # Tell Bob the number of the virtual qubit so the can use it locally
        bob = classicalNet.hostDict["Bob"]
        correct = yield bob.root.callRemote("receive_one_qubit", remoteNum, cnot_direction=1)

        send_end.send(correct)

        reactor.stop()


if __name__ == '__main__':
    unittest.main()

from netqasm.sdk import Qubit, EPRSocket
# from netqasm.sdk import ThreadSocket as Socket
from netqasm.sdk.toolbox import set_qubit_state
from netqasm.output import get_new_app_logger
from simulaqron.sdk import SimulaQronConnection


def main(log_config=None, phi=0., theta=0.):
    print("RUNNING APP ALICE")
    app_logger = get_new_app_logger(node_name="alice", log_config=log_config)

    # Create a socket to send classical information
    # TODO
    # socket = Socket("alice", "bob", log_config=log_config)

    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket("bob")

    # Initialize the connection to the backend
    alice = SimulaQronConnection(
        name="alice",
        log_config=log_config,
        epr_sockets=[epr_socket]
    )
    with alice:
        # Create a qubit to teleport
        q = Qubit(alice)
        set_qubit_state(q, phi, theta)

        # Create EPR pairs
        epr = epr_socket.create()[0]

        # Teleport
        q.cnot(epr)
        q.H()
        m1 = q.measure()
        m2 = epr.measure()

    # Send the correction information
    m1, m2 = int(m1), int(m2)

    app_logger.log(f"m1 = {m1}")
    app_logger.log(f"m2 = {m2}")

    msg = str((m1, m2))
    print(msg)
    # TODO
    # socket.send(msg)

    return {'m1': m1, 'm2': m2}


if __name__ == "__main__":
    main()

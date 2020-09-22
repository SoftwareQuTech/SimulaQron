from netqasm.logging import get_netqasm_logger
from netqasm.sdk import EPRSocket
from simulaqron.sdk import SimulaQronConnection, Socket

logger = get_netqasm_logger()


def main(log_config=None):

    # Create a socket to recv classical information
    socket = Socket("bob", "alice", log_config=log_config)

    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket("alice")

    # Initialize the connection
    bob = SimulaQronConnection(
        "bob",
        log_config=log_config,
        epr_sockets=[epr_socket]
    )
    with bob:
        epr = epr_socket.recv()[0]
        bob.flush()

        # Get the corrections
        msg = socket.recv()
        logger.info(f"bob got corrections: {msg}")
        m1, m2 = eval(msg)
        if m2 == 1:
            epr.X()
        if m1 == 1:
            epr.Z()


if __name__ == "__main__":
    main()

from netqasm.sdk import Qubit
# from netqasm.sdk import ThreadSocket as Socket
from netqasm.sdk.toolbox import set_qubit_state
from simulaqron.sdk import SimulaQronConnection

# import snoop
# @snoop
def main(log_config=None, phi=0., theta=0.):
    print("Starting Alice")
    # Initialize the connection to the backend
    alice = SimulaQronConnection(
        name="alice",
        log_config=log_config,
    )
    with alice:
        q = Qubit(alice)
        # set_qubit_state(q, phi, theta)

        # q2 = Qubit(alice)
        # q.cnot(q2)
        q.H()
        m1 = q.measure()
        # m2 = q2.measure()
        m2 = 0

    # Send the correction information
    m1, m2 = int(m1), int(m2)
    print(f"m1 = {m1}, m2 = {m2}")

    print("Ending Alice")
    return {'m1': m1, 'm2': m2}


if __name__ == "__main__":
    main()

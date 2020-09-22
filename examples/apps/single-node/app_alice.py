from netqasm.sdk import Qubit
from netqasm.sdk.toolbox import set_qubit_state
from simulaqron.sdk import SimulaQronConnection


def main(log_config=None, phi=0., theta=0.):
    # Initialize the connection to the backend
    alice = SimulaQronConnection(
        name="alice",
        log_config=log_config,
    )
    with alice:
        q = Qubit(alice)
        set_qubit_state(q, phi, theta)

        q2 = Qubit(alice)
        q.cnot(q2)
        q.H()
        m1 = q.measure()
        m2 = q2.measure()

    # Send the correction information
    m1, m2 = int(m1), int(m2)
    print(f"m1 = {m1}, m2 = {m2}")

    return {'m1': m1, 'm2': m2}


if __name__ == "__main__":
    main()

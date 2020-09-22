from simulaqron.sdk import Socket


def main(log_config=None, phi=0., theta=0.):

    # Create a socket to send classical information
    socket = Socket("alice", "bob", log_config=log_config)

    msg = "Hello"
    print(f"Alice saying '{msg}'")
    socket.send(msg)

    msg = socket.recv()
    print(f"Alice got msg '{msg}'")


if __name__ == "__main__":
    main()

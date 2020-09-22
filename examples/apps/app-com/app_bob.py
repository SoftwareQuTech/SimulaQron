from simulaqron.sdk import Socket


def main(log_config=None):
    # Create a socket to send classical information
    socket = Socket("bob", "alice", log_config=log_config)

    msg = socket.recv()
    print(f"Bob got msg '{msg}'")

    msg = f"Thanks for saying '{msg}'"
    print(f"Bob saying '{msg}'")
    socket.send(msg)


if __name__ == "__main__":
    main()

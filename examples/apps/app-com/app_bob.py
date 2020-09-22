from simulaqron.sdk import Socket


def main(log_config=None):
    print("RUNNING APP BOB")

    # Create a socket to send classical information
    socket = Socket("bob", "alice", log_config=log_config)

    msg = socket.recv()
    print(f"Bob got msg '{msg}'")

    msg = f"Thanks for saying '{msg}'"
    print(f"Bob saying '{msg}'")
    socket.send(msg)

    print("BOB FINISHED")


if __name__ == "__main__":
    main()

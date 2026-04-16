# Classical Client-Server example

Very simple example to demonstrate how to write client-server applications which exchange
classical messages.


# How to run

There are two ways to run this example:


## On a single machine

The simplest way to run this example is on a single machine. To do this, you can use the
provided bash script:

```shell
./run.sh
```

Alternatively, you can manually start the client and teh server in two different terminals.
First, start the server on one terminal

```shell
python example_server_alice.py
```

which start the server and keeps listening for new incoming connections. Then start the client:

```shell
python example_client_bob.py
```

which will connect to the server and send a message that will be sent back by the server.


## On different machines

To run this example on different machines, it is necessary that both machines can reach each
other via a network (or the internet). Additionally, you need to know the IP addresses of both
machines.

Assuming that the server (alice) will run on a machine with IP `192.168.0.1` and the client (bob)
will run on the machine with IP `192.168.0.2`, modify the `simulaqron_network.json` file *on both*
the server and the client to look like this:

```json
[
    {
        "name": "default",
        "nodes":  [
            {
                "Alice": {
                    "app_socket": ["192.168.0.1", 8821],
                    "qnodeos_socket": ["192.168.0.1", 8822],
                    "vnode_socket": ["192.168.0.1", 8823]
                }
            },
            {
                "Bob": {
                    "app_socket": ["192.168.0.2", 9831],
                    "qnodeos_socket": ["192.168.0.2", 9832],
                    "vnode_socket": ["192.168.0.2", 9833]
                }
            }
        ],
        "topology": null
    }
]
```

Note that the `localhost` entries from Alice were changed to `192.168.0.1`. Similarly, the
`localhost` entries from Bob were changed to `192.168.0.2`.

After these modifications, start the server and client in their respective terminals as described
before.

# Quantum teleport example
Quantum teleport example, using simple NetQASM code both for Alice and Bob.


# How to run

First of all, make sure you are not already running existing simulaqron programs.


## Initial cleanup

You can run

```shell
simulaqron stop
sh terminate.sh
```

which should get rid of all things running for the teleport example itself. If you want to be a bit
more radical and confident you are not running other things to preserve you can run:

```shell
simulaqron stop
pkill -9 python
```

This will kill ALL python processes run by you so beware.  If you have a debugging enabled, you may also
wish to wipe old log files by running:

```shell
rm /tmp/simulaqron*
```

This should leave you a clear slate. We can now start the application.


## On a single machine
If you are running everything on the same machine, first we start the simulaqron backend by typing

```shell
simulaqron start --node Alice,Bob
```

This needs to be done only once. Now type

```shell
sh run.sh
```

WARNING: It seems restarting the simulaqron backend is needed! - There is no need to restart the simulaqron backend again if you want to re-run your example. 


## On multiple machines

If you are starting on two different machines run, you first need to update the network configuration
file. To run this example on different machines, it is necessary that both machines can reach each
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

After these modifications, yu can start the simulaqron backends by invoking:

```shell
simulaqron start --node Alice
simulaqron start --node Bob
```

on the machines you will use as Alice and Bob respectively. Again this needs to be run only once.
Now you can run:

* on Bob:
```shell
python teleport-bob.py
```

* on Alice:
```shell
python teleport-alice.py
```

The code assumes you start Bob before starting Alice. Using your knowledge of network programming
from our ping pong example - do you have an idea to make this more robust?

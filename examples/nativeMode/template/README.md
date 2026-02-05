# SimulaQron native mode template

You can use the files in this folder as a template for implementing new SimulaQron applications.
Please check the comments inside the `nodeTest.py` file to learn how to modify it.


# Update network configuration

Additionally, this template also contains a file that you can use for defining the network:
`network_config.json`.

This file contains a single network, named "default". This network contains 4 nodes named
"Alice", "Bob", "Charlie" and "David".

Each one of those nodes defines 3 entries:
* `app_socket`: The hostname and port used by other nodes to send classical messages to this node.
  SimulaQron applications will bind to this hostname and port to listen for classical messages coming
  from other nodes.
* `qnodeos_socket`: The hostname and port to bind the QNodeOS server. This configuration is required
  when using SimulaQron's NetQASM interface.
* `vnode_socket`: The hostname and port to bind SimulaQron's Virtual Node server. This server is in
  charge of executing the quantum simulation. Configuring this entry is required in all cases.s


## Adding new nodes

To add a new node named "Eva", follow these steps:
1. Open the config.json file in a text editor.
2. Locate the "nodes" array inside the "default" object.
3. Add a new object to the "nodes" array for "Eva". The structure should match the existing nodes:
```json
{
    "Eva": {
        "app_socket": ["localhost", PORT_NUMBER],
        "qnodeos_socket": ["localhost", PORT_NUMBER],
        "vnode_socket": ["localhost", PORT_NUMBER]
    }
}
```
  Replace PORT_NUMBER with unique port numbers for each socket type (e.g., 8851, 8852, 8853). The result should
  look like:
```json
Copy

{
    "name": "default",
    "nodes": [
        {"Alice": {...}},
        {"Bob": {...}},
        {"Charlie": {...}},
        {"David": {...}},
        {
            "Eva": {
                "app_socket": ["localhost", 8851],
                "qnodeos_socket": ["localhost", 8852],
                "vnode_socket": ["localhost", 8853]
            }
        }
    ],
    "topology": null
}
```

4. Save the file after making the changes.


# Additional tools

This folder also contains a few bash scripts you can use for executing you application.


## `run.sh`

This script is a helper to quickly start the SimulaQron backend for a list of specified nodes, and then
start the application code for those same nodes.

This script needs a small change depending on how many nodes you want to run *on the current machine*.
If you open this file, you can see this content:
```shell
#!/usr/bin/env bash

# Check if SimulaQron is already running
if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
    if ! simulaqron start --nodes=Alice,Bob --network-config-file network_config.json
    then
        echo "SimulaQron could not start correctly"
        exit 1
    fi
fi


# Run the files for Alice, Bob or whatever nodes you construct
python3 bobTest.py &
python3 aliceTest.py
```

Change the `--nodes` option of the `simulaqron start` command, with the list (separated with commas, no spaces)
of nodes you want to start locally. Also, change the `python3` lines to also start all your python programs
that implement the nodes.

Finally, if you changed the name of the network configuration file, also reflect this change by changing
the argument next to the `--network-config-file` option.


## `terminate.sh`

This script can be used to stop the SimulaQron backend and terminate all the applications processes
that are still running.


## `doNew.sh`

This is ascript that you can use to start a new instance of your application from a clean state.
This scrip simply invokes `terminate.sh` and `run.sh` sequentially.

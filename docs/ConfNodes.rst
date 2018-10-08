Configuring the simulated network
=================================

-------------------------------
Starting the SimulaQron backend
-------------------------------

The backend of SimulaQron, i.e. the virtual nodes and the corresponding CQC servers can be started by running the file run/startAll.sh. If no arguments are given, a network is setup using the files in the folder config. By default this network consist of the five nodes Alice, Bob, Charlie, David and Eve, in a fully connected topology. One can easily also setup networks using different nodes and topologies by providing arguments to run/startAll.sh as described in this section. To setup a specific topology see the next section :ref:`topologyConf`. How to manually setup a network by editing the config files, see the section :ref:`manualSetup` below. This is useful if you don't want run/startAll.sh to choose the port numbers used for the servers. Finally, to know how to connect to an already running simulated network using CQC, see section :ref:`remoteNetwork`.

If you want to start a network with for example the three nodes Alex, Bart, Curt, simply type::

    sh run/startAll.sh --nodes "Alex Bart Curt"

.. warning:: This will kill python processes containing the keywords `Test`, `start` or `setup`, edit files in the directory config and start servers at `localhost` using port numbers from 8801 to 8800 + 2 * (# nodes).

If you simply want a network with 10 nodes, type::

    sh run/startAll.sh --nrnodes 10

This will start up a network where the nodes are called Node0, Node1, ..., Node9.

The --nodes and --nrnodes can be combined. Let's say you want a network with 10 nodes and that three of the nodes are called Alice, Bob and Charlie, type::

    sh run/startAll.sh --nodes "Alice Bob Charlie" --nrnodes 10

Which will start up a network with the nodes Alice, Bob, Charlie, Node0, Node1, ..., Node6. If --nrnodes is less than the entries in --nodes, then --nrnodes is ignored. The two keywords can also be specified shorter as -nd and -nn respectively. So the above can also be done as::

    sh run/startAll.sh -nd "Alice Bob Charlie" -nn 10

You can also specify a topology of the network. For example if you want 10 nodes in a ring topology, type::

    sh run/startAll.sh --nrnodes 10 --topology ring

In this network Node :math:`i` can create EPR pairs and send qubits to Node :math:`i-1 \pmod{10}` and Node :math:`i+1 \pmod{10}`. However, if a CQC message is sent to for example Node2 to produce entanglement with Node5, a error message (CQC_ERR_UNSUPP) will be returned. The options for the automatically generated topologies are currently:

* `complete`: A fully connected. This is also used if the argument --topology is not used.
* `ring`: A ring network, i.e. a connected topology where every node has exactly two neighbors.
* `path`: A path network, i.e. a connected topology where every node has exactly two neighbors but there are no cycles.
* `random_tree`: Generates a random tree, i.e. a topology without cycles.
* `random_connected_{int}`: Generates a random connected graph with a specified number of edges. For example a random connected network on 10 nodes, can be specified as `random_connected_20`. Note that the number of edges for a network with :math:`n` nodes must be greater or equal to :math:`n-1` and less or equal to :math:`n(n-1)/1`.

Along with setting up the network with the specified topology a .png figure is also generated and stored as config/topology.png. This is useful if a random network is used, to easily visualize the network used.

As a final example let's combine all the arguments specified above and create a network using 15 nodes, where two of then are called Alice and Bob and the topology of the network is randomly generated as a connected graph with 20 edges::

    sh run/startAll.sh -nd "Alice Bob" -nn 15 -tp random_connected_20

The network that is then started might look like this (you can find a similar picture for you network at `config/topology.png`:

.. image:: figs/topology.png
    :width: 400px
    :align: center
    :alt: Programming SimulaQrons Interfaces

To create a custom topology, see the next section.

.. _topologyConf:

--------------------------------
Configuring the network topology
--------------------------------

As seen in the previous section a pre-defined network topology can be used by passing an argument when running run/startAll.sh. The topology is then specified to SimulaQron as a .json-file stored at config/topology.json. The content of this .json file is a dictionary where the keys are the names of the nodes and the values a list of the neighbors. For example, a file specifying a topology where Alice is adjacent to Bob, Bob is adjacent to Alice and Charlie and Charlie is adjacent to Bob would be::

    {
     "Alice": ["Bob"],
     "Bob": ["Alice", "Charlie"]
     "Charlie": ["Bob"]
    }

.. note:: Undirected topologies are also supported. That is, networks where for example Alice can send a qubit to Bob but Bob cannot send a qubit to Alice.

You can create your own .json file specifying the network topology you want to use. When doing so, make sure that the names of the nonodes you use are consistent with the nodes used by SimulaQron. To have SimulaQron use your specified topology, set the entry :code:`topology_file` in the file config/settings to be the relative path to the .json file, as seen from the root of the repository.

.. note:: When using the keyword argument --topology (or -tp) for run/startAll.sh, the file config/topology.json is overwritten. It is therefore recommended to create your own topology-file with another name or in a different directory, to not accidentally overwrite your file.

.. _manualSetup:

------------
Manual setup
------------

In this section we describe what the file run/startAll.sh does and how one can manually start up the SimulaQron and editing the nodes and port numbers used. This is useful if you don't want run/startAll.sh to automatically set the port numbers for you. Depending on what arguments are given to run/startAll.sh, the following is done:

* If no arguments to run/startAll.sh are given then SimulaQron will start using the configuration specified by the files in the directory config. If there the file config/Nodes.cfg doesn't exist then it will be created and the files config/{virtualNodes.cfg, cqcNodes.cfg, appNodes.cfg} will be overwritten using the nodes Alice, Bob, Charlie, David and Eve.

* If the arguments --nodes (-nd) or --nrnodes (-nn) are used for run/startAll.sh then the files config/{Nodes.cfg, virtualNodes.cfg, cqcNodes.cfg, appNodes.cfg} are overwritten using the specified nodes. Port numbers will be used froThe files run/startVNodes.sh and run/startCQCNodes.sh are then called. What these scripts in turn do is specified below.m 8801.

* If the argument --topology (-tp) is used then the files config/topology.json and config/topology.png will be overwritten which the specified topology and the entry :code:`topology_file` in config/settings.ini will be set to point to this file.

The files run/startVNodes.sh and run/startCQCNodes.sh are then called. What these scripts in turn do is specified below.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Starting the virtual node servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default SimulaQron uses the five nodes Alice, Bob, Charlie, David and Eve on your local computers.

You may do so by executing::

	sh run/startVNodes.sh

Let us now see in detail what happens when you execute this example script. 
The configuration for the test network is read from config/virtualNodes.cfg. This file defines which virtualNodes to start up and what their names are. The example runs them all locally, but you can as well run them on remote hosts by using one such file on each host.

For the example, this file is::

	# Network configuration file
	# 
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]
	#

	Alice, localhost, 8801
	Bob, localhost, 8802
	Charlie, localhost, 8803

Provided a configuration in the file above, you can run::

	python run/startNode.py Alice & 

To start the virtual node for Alice. The script startVNodes.sh then simply starts any number of desired virtual nodes::

	# startVNodes.sh - start the node Alice, Bob and Charlie 

	cd "$NETSIM"/run
	python startNode.py Alice &
	python startNode.py Bob &
	python startNode.py Charlie &

Provided the virtual nodes started successfully you now have a network of 3 simulated quantum nodes that accept connections on the ports indicated above to allow an application program to access qubits on the virtual node servers. The 3 virtual nodes have also established connections to each other in order to exchange simulated quantum traffic. 

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Starting the CQC servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similarly to the virtual nodes we also need to start the CQC servers, which provide the possibility to talk to SimulaQron using the CQC interface.
A test configuration of CQC servers will start 3 nodes, Alice, Bob and Charlie on your local computers. You may do so by executing::

	sh run/startCQCNodes.sh

The configuration for the CQC network is read from config/cqcNodes.cfg. This file defines which CQC servers to start up and what their names are.

.. note:: The names for the virtual nodes and the CQC servers have to be the same.

For the example, this file is::

	# Network configuration file
	# 
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]
	#

	Alice, localhost, 8821
	Bob, localhost, 8822
	Charlie, localhost, 8823

The script startCQCNodes.sh starts any number of desired CQC servers::

	# startCQCNodes.sh - start the node Alice, Bob and Charlie 

	cd "$NETSIM"/run
	python startCQC.py Alice &
	python startCQC.py Bob &
	python startCQC.py Charlie &

Provided the CQC servers started successfully you now have a network of 3 simulated quantum nodes that accept connections on the ports indicated above and takes messages specified by the CQC header.

.. _remoteNetwork:

----------------------------------------
Connecting to a remote simulated network
----------------------------------------

If a simulated network (consisting of virtual nodes and CQC servers) are setup on a remote computer (or on your own computer), CQC messages can be sent to the correct address and port numbers to control the nodes of the network. In this section we describe how to do this.

Given the ip and port number of the CQC server of a node, you can send CQC messages over TCP using in any way you prefer. To know how these messages should look like to perform certain instructions, refer to :doc:`CQCInterface`.

An easier way to send CQC messages to a CQC server of a node is to use the provided Python library. Assuming that you have a file in the form of the config/cqcNodes.cfg above, i.e. consisting of lines of the form `[name], [hostname/ip], [port]` you can then easily instanciate an object of the class :code:`SimulaQron.cqc.pythonLib.cqc.CQCConnection` which will communicate with the CQC server for you, using the CQC interface.

Let's assume that you have a file cqcNodes_example.cfg which consist of the following lines::

    Alice, 1.1.1.1, 8801
    Bob, 2.2.2.2, 8802
    Charlie, localhost, 8803

you can connect to the CQC server for the node Alice at 1.1.1.1 and port number 8801 by executing the following Python code::

    from SimulaQron.cqc.pythonLib.cqc import CQCConnection

    cqc = CQCConnection("Alice", cqcFile=/path/to/cqcNodes_example.cfg)

Alternatively, instead of specifying the path to the config file containing the ip and the port number of the CQC server for the node Alice, you can directly specify the ip and port number as follows::

    cqc = CQCConnection("Alice", socket_address=("1.1.1.1", 8801))

More information on how to then actually allocating qubits, manipulating these and creating simulated entanglement see :doc:`PythonLib`

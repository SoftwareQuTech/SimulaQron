Overview
========

----------------------
Programming SimulaQron
----------------------

There are two ways to program SimulaQron to run applications. The first is to use SimulaQron's native interface via `Twisted <https://twistedmatrix.com/>`_ Perspective Broker. This interface is specific to Python, and not (easily) accessible from other languages. We will call this interface SimulaQron's native interface throughout. While you may play with simple applications this way, the main purpose of this interface is to allow the development of higher protocol layers and abstractions which will ultimately be used to program quantum networks. 
In the light of the alternate interface below it may appear inefficient to export an intermediary interface. However, the purpose of SimulaQron is precisely to explore and play with highler layer abstractions on top of any hardware, or its simulated version, SimulaQron. As such it is best to think of SimulaQron as a piece of simulated hardware with its own native interface, which we may first abstract into a higher level command language for programming. Examples of how to program SimulaQron in native mode can be found in :doc:`ExamplesDirect`.

The second way to run applications is via a higher level interface bundled with SimulaQron, called the classical-quantum combiner (CQC) interface. This interface is universally accessible from any language, and will be available on the planned 2020 quantum internet demonstrator connecting several Dutch cities. If you want your applications to later use real quantum hardware instead of SimulaQron, then this is the interface to use. Internally, the CQC included in this package, uses SimulaQron's native interface from above in place of real quantum hardware. Examples of how to program using the CQC can be found in :doc:`ExamplesNodeOS`.

-------------------------------
How SimulaQron works internally
-------------------------------

Let us here briefly sketch how SimulaQron works internally. Further details can be found in this arXiv paper.
This simulator consists of two parts and has a relatively modular design:


^^^^^^^^^^^^^^^^^^^^^
Virtual quantum nodes
^^^^^^^^^^^^^^^^^^^^^

A virtual quantum node is a server program running on a particular computer that pretends to be quantum hardware, simulating qubits and quantum communication.
That is, you may thnk of these nodes as fake hardware programmable directly via SimulaQron's native interface. Each node presents
a number of virtual qubits for you to use. These virtual qubits would correspond to the physical qubits
available at this node, would this be a real physical implementation of the quantum network node. By connecting to the virtual quantum node server, a
client program that depends on using quantum hardware, may manipulate these qubits as if they were local physical qubit and also 
instruct to send them to remote nodes. 
The virtual quantum node servers are identifies
by their common names (eg Alice, Bob, Charlie), and amongst themselves connect classically to form a virtual simulation
network as a backend.

An important internal element in SimulaQron is the distinction between virtual qubits and simulated qubits. Virtual qubits
are the qubits as they would be present in real quantum hardware. A virtual qubit is local to each virtual quantum node server
and may be manipulated there. Each virtual qubit is simulated somewhere, by a simulated qubit. Importantly, this simulated qubit
may be located at a different simulating node than the node holding the corresponding virtual qubit.
To see why this is necessary, note that 
entangled qubits cannot be locally represented by any form of classical information (hence
the quantum advantage of entanglement in the first place!). As such, if two (or more) virtual nodes share
qubits which are somehow entangled with each other, then these qubits will actually need to be simulated
at just one of these nodes. That is, they appear to be virtually local (as if they were real physical
qubits), yet they are actually simulated at just one of the network nodes. As you might imagine, 
this also means that if we want to perform an entangling gate to two qubits which are virtually
local, but actually simulated in two different backend quantum registers, then a merge of these
registers is required before the entangling gate can be exectuted. This is all handled transparently 
by the backend provided here. For programming network applications using SimulaQron you will not need to 
deal with this backend simulation. 

Nevertheless, as a guide to the backend, it consists of three essential components:

* quantumEngine - the one used here is implemented as simpleEngine in crudeSimulator.py which uses quTip as a backend. This corresponds to one quantum register full of qubits across which gates can be performed. Should you wish to use a different backend, you may wish to add a different engine.

* simulatedQubit - for each qubit simulated in that register, there is a simQubit object. This is local to each node. It exports remote method calls. These methods are only called by the virtual node network itself: when a virtual node discovers the qubit is actually simulated remotely, it passes on this call by calling the relevant method on the remote qubit object.

* virtualQubit - this is the object representing a virtually local qubit. This carries information about the remote simulating qubit. These virtualQubit objects can in turn be accessed by the clients who can access these virtual qubits as if they were real local physical qubits without having to know where they are actually simulated. That is, the client obtains a pointer to the relevant virtual qubit object on which it can perform operations directly.

* virtualNode - this is the local virtual node which accepts requests to get a virtual qubit object, send qubits to other nodes, or (for convenience sake), read out the state of qubits.

* backEnd - starts up the virtual node backend

^^^^^^^^^^^^^^^^^^^^^^^
The local client engine
^^^^^^^^^^^^^^^^^^^^^^^

The second part is a framework for writing applications that use the virtually simulated quantum 
network. Such an application needs to connect locally to the virtual quantum node server simulating the underlying hardware (for programming
in native mode), or to the CQC interface. It is up to these applications to exchange any classical communication required to execute the protocol.


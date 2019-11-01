Overview
========

----------------------
Programming SimulaQron
----------------------

There are two ways to program SimulaQron to run applications. The first is to use SimulaQron's native interface via `Twisted <https://twistedmatrix.com/>`_ Perspective Broker. This interface is specific to Python, and not (easily) accessible from other languages. We will call this interface SimulaQron's native interface throughout. While you may play with simple applications this way, the main purpose of this interface is to allow the development of higher protocol layers and abstractions which will ultimately be used to program quantum networks. 
In the light of the alternate interface below it may appear inefficient to export an intermediary interface. However, the purpose of SimulaQron is precisely to explore and play with higher layer abstractions on top of any hardware, or its simulated version, SimulaQron. As such it is best to think of SimulaQron as a piece of simulated hardware with its own native interface, which we may first abstract into a higher level command language for programming. Examples of how to program SimulaQron in native mode can be found in :doc:`Examples`.

The second way to run applications is via a higher level interface bundled with SimulaQron, called the classical-quantum combiner (CQC) interface. This interface is universally accessible from any language. It comes with a C and Python library, where the Python CQC is definitely the best place to get started if you have never programmed SimulaQron before. An evolved version of a C library and interface is targeted to be available on the planned 2020 quantum internet demonstrator connecting several Dutch cities. If you want your applications to later use real quantum hardware more easily instead of SimulaQron, then this is the interface to use. Internally, the CQC included in this package, uses SimulaQron's native interface from above in place of real quantum hardware. Examples of how to program using the CQC can be found in :doc:`CQC`.

.. note:: The CQC packages and libraries have been moved to seperate repos at `pythonLib <https://github.com/SoftwareQuTech/CQC-Python>`_ and `cLib <https://github.com/SoftwareQuTech/CQC-C>`_. The python library can be installed using pip by the command :code:`pip3 install cqc`.

.. image:: figs/CQC_schematic_v3.png
    :width: 400px
    :align: center
    :alt: Programming SimulaQrons Interfaces

Practically, SimulaQron's Backend is a server process running on each local classical computer (or on a single classical computer), emulating quantum hardware. The backend can be programmed directly using Twisted PB aka native mode. For clarity, not efficiency, the CQC Backend is a separate server process, which connects to the SimulaQron backend using Twisted PB. It accepts incoming connections, and using a general packet format can be programmed using any programming language. Libraries for C and Python are provided. If you are starting out, programming in the Python CQC library is by far the easiest way to get going! Further information about the Python library can be found in https://softwarequtech.github.io/CQC-Python/index.html and explicit examples using this library in https://softwarequtech.github.io/CQC-Python/examples.html.

-------------------------------
How SimulaQron works internally
-------------------------------

Let us here briefly sketch how the SimulaQron backend works internally. Further details can be found in our `paper <http://iopscience.iop.org/article/10.1088/2058-9565/aad56e>`_.
The simulator consists of two parts and has a relatively modular design:


^^^^^^^^^^^^^^^^^^^^^
Virtual quantum nodes
^^^^^^^^^^^^^^^^^^^^^

A virtual quantum node is a server program running on a particular computer that pretends to be quantum hardware, simulating qubits and quantum communication.
That is, you may think of these nodes as fake hardware programmable directly via SimulaQron's native interface. Each node presents
a number of virtual qubits for you to use. These virtual qubits would correspond to the physical qubits
available at this node, would this be a real physical implementation of the quantum network node. By connecting to the virtual quantum node server, a
client program that depends on using quantum hardware, may manipulate these qubits as if they were local physical qubit and also 
instruct to send them to remote nodes. 
The virtual quantum node servers are identified
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
this also means that if we want to perform an entangling gate between two qubits which are virtually
local, but actually simulated in two different backend quantum registers, then a merge of these
registers is required before the entangling gate can be executed. This is all handled transparently
by the backend provided here. For programming network applications using SimulaQron you will not need to 
deal with this backend simulation. 

Nevertheless, as a guide to the backend, it consists of three essential components:

* quantumEngine - There are currenlty three different quantumEngines implemented: Using `QuTip <http://qutip.org/>`_ and mixed state, using `Project Q <https://projectq.ch/>`_ and pure states and finally using stabilizer formalism.
    This corresponds to one quantum register full of qubits across which gates can be performed. Should you wish to use a different backend, you may wish to add a different engine.
    The three current backends give different runtimes due to how quantum states are stored and manipulated.
    In the stabilizer formalism, only Clifford operations can be performed and the simulation is in fact efficient in the number of qubits.
    See the figure below for a comparison of runtimes to create a GHZ-state on a number of qubits using the three different backends.

.. image:: figs/runtime_qutip_vs_projectq_vs_stabilizer.png
    :width: 700px
    :align: center
    :alt: Runtime of creating a GHZ-state using the three different backends currently implemented in SimulaQron.

* simulatedQubit - for each qubit simulated in that register, there is a simQubit object. This is local to each node. It exports remote method calls. These methods are only called by the virtual node network itself: when a virtual node discovers the qubit is actually simulated remotely, it passes on this call by calling the relevant method on the remote qubit object.

* virtualQubit - this is the object representing a virtually local qubit. This carries information about the remote simulating qubit. These virtualQubit objects can in turn be accessed by the clients who can access these virtual qubits as if they were real local physical qubits without having to know where they are actually simulated. That is, the client obtains a pointer to the relevant virtual qubit object on which it can perform operations directly.

* virtualNode - this is the local virtual node which accepts requests to get a virtual qubit object, send qubits to other nodes, read out the state of qubits, perform gates etc.

* backEnd - starts up the virtual node backend

.. image:: figs/simulated_virtualQubits_v7.png
    :width: 550px
    :align: center
    :alt: Virtual and simulated qubit

^^^^^^^^^^^^^^^^^^^^^^^
The local client engine
^^^^^^^^^^^^^^^^^^^^^^^

The second part is a framework for writing applications that use the virtually simulated quantum 
network. Such an application needs to connect locally to the virtual quantum node server simulating the underlying hardware (for programming
in native mode), or to the CQC interface. It is up to these applications to exchange any classical communication required to execute the protocol.


--------------------------
Report bugs and contribute
--------------------------

^^^^^^^^^^^^^^^^^^^^^^^^^^
Bugs and feature requests
^^^^^^^^^^^^^^^^^^^^^^^^^^

For bugs, feature requests, suggestions or other general questions please use GitHubs issue tracker in the repository (located under ‘Issues’ on the main page of the repository).
Please start your message with specifying one of the four labels below for easier handling of issues, for example::

    Type: bug

    There is a bug when applying the gate...

Always provide enough information to assess the issue and separate different issues into different messages.

* *bug*: This is for bugs that are encountered. Please provide a way to reproduce the bug, preferably with a minimal example, and explain what goes wrong.

* *feature request*: Is there a feature that you think should be provided? Explain the details of the feature and why you think this should be implemented.

* *help wanted*: If there is something you having trouble with but which is not necessarily a bug. Also use this for other general questions.

* *suggestions*: If you have suggestions on how to improve the features already existing. Be clear on what exactly you think should be improved and explain why.

^^^^^^^^^^
Contribute
^^^^^^^^^^

If you would like to contribute with your own code to fix a bug or add an additional feature, this is most welcomed.
Please then make a pull request on GitHub, which will be reviewed before approval.
For contributing use the *Develop*-branch.
Please make sure you run the automated tests below before submitting any code.
The easiest way to proceed is to:

#. Fork the repository at the *Develop*-branch.
#. Make the changes and commit these to your forked branch.
#. Make a pull request between your branch and the *Develop*-branch. Also provide a message which explains the changes and/or additions you have made.

^^^^^^^^^^^^^^^
Automated tests
^^^^^^^^^^^^^^^

There are number of automated tests that test many (but not all) of the features of SimulaQron and the CQC interface.
See :doc:`GettingStarted` for how to run these.
Some of the automated tests use quantum tomography and are thus inherently probabilistic.
Therefore if you see that one of these fails, you can try to run the test again and see if it is consistent.
If the tests are to slow on your computer you can also run the short version, which skips the quantum tomography tests.

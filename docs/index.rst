.. SimulaQron documentation master file, created by
   sphinx-quickstart on Fri May 26 13:25:00 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SimulaQron Documentation
========================

Welcome to the Quantum Internet simulator SimulaQron!

SimulaQron is a distributed simulation of the end nodes in a future quantum internet with the specific goal to explore application development. 
The end nodes in a quantum internet are few qubit processors, which may exchange qubits using
a quantum internet. 
Specifically, SimulaQron
allows the installation of a local simulation program on each computer in the network that provides the illusion of having a local quantum processor to potential applications.
The local simulation programs on each classical computer connect to each other classically, forming a simulated quantum internet allowing the exchange of simulated qubits between the different
network nodes, as well as the creation of simulated entanglement.

SimulaQron is written in `Python <http://www.python.org/>`_ and uses the `Twisted <https://twistedmatrix.com/>`_ Perspective Broker.
To perform the local qubit simulation, three different backends have so far been implemented: Using `QuTip <http://qutip.org/>`_ and mixed state, using `Project Q <https://projectq.ch/>`_ and pure states and finally using stabilizer formalism.
However, any other quantum simulator with a python interface can easily be used as a local backend.
The main challenge of SimulaQron is to allow the simulation of virtual qubits at different network nodes: since these may be entangled they cannot be simulated on one network node, which is solved by a transparent distributed simulation on top of in principle any local simulation engine.

We also have a  `paper <http://iopscience.iop.org/article/10.1088/2058-9565/aad56e>`_ that describe the design of SimulaQron, which is also freely available on `arxiv <https://arxiv.org/abs/1712.08032>`_.

The documentation below assumes familiarity with classical network programming concepts, Python, Twisted, as well as an elementary understanding of quantum information. More information on a competition at `Our website <http://www.simulaqron.org/>`_ 

SimulaQron can be installed from pip by the command :code:`pip3 install simulaqron` on MacOS and Linux.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Overview
   GettingStarted
   ConfNodes
   CQC
   Examples
   simulaqron


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

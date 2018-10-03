Useful commands
========================

Here we list some useful methods that can be applied to a ``CQCConnection`` object or a ``qubit`` object below.

``CQCConnection``
"""""""""""""""""
The ``CQCConnection`` is initialized with the name of the node (``string``) as an argument.

* ``sendQubit(q,name)`` Sends the qubit q (``qubit``) to the node name (``string``).

  Return: ``None``.
* ``recvQubit()`` Receives a qubit that has been sent to this node. 

  Return: ``qubit``.
* ``createEPR(name)`` Creates an EPR-pair :math:`\frac{1}{\sqrt{2}}(|00\rangle+|11\rangle)` with the node name (``string``). 

  Return: ``qubit``.
* ``recvEPR()`` Receives qubit from an EPR-pair created with another node (that called ``createEPR``). 

  Return: ``qubit``.
* ``sendClassical(name,msg)`` Sends a classical message msg (``int`` in range(0,256) or list of such ``int``s) to the node name (``string``). Opens a socket connection if not already opened. 

  Return: ``None``.
* ``startClassicalServer()`` Starts a server that can receive classical messages sent by ``sendClassical``. 

  Return ``None``.
* ``recvClassical()`` Receives a classical message sent by another node by ``sendClassical``. 

  Return ``bytes``.

``qubit``
"""""""""""""""""
Here are some useful commands that can be applied to a ``qubit`` object.
A ``qubit`` object is initialized with the corresponding ``CQCConnection`` as input and will be in the state :math:`|0\rangle`.

* ``X()``, ``Y()``, ``Z()``, ``H()``, ``K()``, ``T()`` Single-qubit gates. 

  Return ``None``.
* ``rot_X(step)``, ``rot_Y(step)``, ``rot_Z(step)`` Single-qubit rotations with the angle :math:`\left(\mathrm{step}\cdot\frac{2\pi}{256}\right)`. 

  Return ``None``.
* ``CNOT(q)``, ``CPHASE(q)`` Two-qubit gates with q (``qubit``) as target. 

  Return ``None``.
* ``measure(inplace=False)`` Measures the qubit and returns outcome. If inplace (``bool``) then the post-measurement state is kept afterwards, otherwise the qubit is removed (default). 

  Return ``int``.

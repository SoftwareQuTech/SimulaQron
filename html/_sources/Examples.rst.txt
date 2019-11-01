Programming via SimulaQron's native Python Twisted Interface (specific to SimulaQron)
=====================================================================================

One way to program SimulaQron is directly via its 'native interface' using Twisted. 
This means writing a client program connecting directly to the local virtual quantum node, and issuing instructions
to such simulated quantum hardware. Programming SimulaQron in its native interface is evidently Python specific, and
meant primarily as an internal interface allowing one to explore higher level abstractions built on top of it.
One such abstraction is the classical-quantum combiner (CQC) interface, which we aim to make available on the 2020 quantum 
internet demonstrator. For programming in a universal, i.e., not Python specific interface see :doc:`CQC`. 

The examples below assume that you have already made your way through :doc:`GettingStarted`: you have the virtual node servers
up and running, and ran the simple example of generating correlated randomness. Further examples can also be found in examples/nativeMode.

.. note:: The 'native' mode is not the recommended way to program applications for SimulaQron, instead use either the `Python <https://softwarequtech.github.io/CQC-Python/index.html>`_ (recommended if you are gettings started), `C <https://softwarequtech.github.io/CQC-C/index.html>`_, or the `Rust <https://docs.rs/cqc>`_ Library.

.. toctree::
	:maxdepth: 2
	:caption: Native mode examples:

	NativeModeCorrRng
	NativeModeTemplate
	NativeModeTeleport
	NativeModeGraphState




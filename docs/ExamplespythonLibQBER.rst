Estimating QBER
===============

In this example the two nodes Alice and Bob will estimate the QBER (qubit error rate) of their produced entangled pairs.
To make the below example more interesting you should try to turn on the probabilistic noise option in SimulaQron.
You can do this be setting the entry :code:`noisy_qubits` to :code:`True` in the settings-file `config/settings.ini`.
You can also tune the coherence time :code:`t1` of the qubits.

.. note:: This probabilistic noise in SimulaQron is not intended and should not be used to benchmark the performence of protocols in noisy settings, since noise is applied in a rate related to the wall clock time of your computer. Thus, if your computer or network is slower, more noise will be applied to the qubits!


------------
The protocol
------------

-----------
Setting up
-----------

We will run everything locally (localhost) using two nodes, Alice and Bob. Start up the backend of the simulation by running::

    sh run/startAll.sh --nodes "Alice Bob"

The below example can then be executed when in the folder `examples/cqc/pythonLib/teleport` typing::

    sh doNew.sh

which will execute the Python scripts `aliceTest.py` and `bobTest.py` containing the code below.

-----------------
Programming Alice
-----------------

Here we program what Alice should do using the python library::

        from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit

        #####################################################################################################
        #
        # main
        #
        def main():


        ##################################################################################################
        main()

-----------------
Programming Bob
-----------------

Here we program what Bob should do using the python library::

        from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit

        #####################################################################################################
        #
        # main
        #
        def main():

        ##################################################################################################
        main()


In this example the two nodes Alice and Bob will estimate the QBER (qubit error rate) of their produced entangled pairs.
To make the below example more interesting you should try to turn on the probabilistic noise option in SimulaQron.
You can do this be setting the entry :code:`noisy_qubits` to :code:`True` in the settings-file `config/settings.ini`.
You can also tune the coherence time :code:`t1` of the qubits.

NOTE: This probabilistic noise in SimulaQron is not intended and should not be used to benchmark the performence of protocols in noisy settings, since noise is applied in a rate related to the wall clock time of your computer. Thus, if your computer or network is slower, more noise will be applied to the qubits!


In this example, we have only two nodes: Alice and Bob.

Alice and Bob will locally connect to their virtual nodes. The classical control communication is done by
letting Alice run a client and Bob a server. Alice generates the EPR pair, and sends half to Bob. She subsequently
performs the teleportation operation. She informs Bob of the outcome of the teleportation measurement, as well as the
identity of the virtual qubit he received (assumed to be unknown to Bob here).

Bob proceeds to recover the teleported qubit.

In this example, we simply print out the initial state to be teleported, as well as the final state received by
Bob to check whether the teleportation worked correctly.

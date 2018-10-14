# W State Leader Election

## How to run

```
sh $NETSIM/run/startAll.sh --nrnodes 7
./run.sh
```

Note that you need to give the nodes a few seconds to start up after running
the first command.

## Explanation

A conceptually simple way to elect a leader of N nodes is to prepare a W state
of N qubits and distribute one qubit to each node.  Each node measures their
qubit and the node that measures `1` becomes the leader.  The idea comes from
[this presentation](https://ww2.chemistry.gatech.edu/pradeep/talks/qle.pdf).

In order to run this protocol, it is necessary to prepare a W state.  The W
state preparation is based on [this paper](https://arxiv.org/abs/1807.05572).

# Coin Flip Leader Election

## How to run

```
sh $NETSIM/run/startAll.sh
./run.sh
```

Note that you need to give the nodes a few seconds to start up after running
the first command.

## Explanation

It is possible to elect a leader from a collection of N nodes by performing a
series of coin flips as explained in [this
paper](https://arxiv.org/abs/0910.4952v2).

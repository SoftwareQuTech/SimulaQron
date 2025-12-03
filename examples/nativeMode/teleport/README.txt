# Description

In this example, we have only two nodes: Alice and Bob.

Alice and Bob will locally connect to their virtual nodes. The classical control communication is done by
letting Alice run a client and Bob a server. Alice generates the EPR pair, and sends half to Bob. She subsequently
performs the teleportation operation. She informs Bob of the outcome of the teleportation measurement, as well as the
identity of the virtual qubit he received (assumed to be unknown to Bob here).

Bob proceeds to recover the teleported qubit.

In this example, we simply print out the initial state to be teleported, as well as the final state received by
Bob to check whether the teleportation worked correctly.


# How to run

To run this example, first make sure that the python virtual environment is activated. You can easily check this
with the terminal command prompt, which shows the active python virtual environment in parentheses:
```
(simulaqron) user@machine_name:~$
```
If you don't see the name of the virtual environment, please check the SimulaQron README file to know how to
create and activate it.

Once the environment is active, we need to start the simulaqron network:
```bash
siumulaqron start --nodes Alice,Bob
```

This will read the JSON configuration files and start the SimulaQron virtual nodes for nodes `Alice` and `Bob`.

After this, you can simply run the example by using the `run` script:
```bash
./run.sh
```

# How to stop the execution in case the test execution stalls.

To fully stop the execution, you can use the `doNew` script. This will stop the current execution and run the
example once again:
```bash
./doNew.sh
```


# Troubleshooting

## Trying to start the network gives "Network with name <name> is already running" message

This usually happens when you stopped the network "manually" by killing processes (`kill -9`). If this happens,
please make sure that you kill all related processes (use `ps aux | grep python` to search) and then delete the
PID file for the running network. This file is located in `~/simulaqron_pids` and it is called
`simulaqron_network_<network_name>.pid`:
```bash
rm ~/simulaqron_pids/simulaqron_network_<network_name>.pid
```

After this, you can try to start the network again

# Distributed Graph States

In this example Alice, Bob, Charlie and David generate a graph state and transform this into a
GHZ-like state and measure their qubits to achieve correlated outcomes. For a complete description
of this example, see the description in the documentation under:
    * Examples
        * Programming via SimulaQron's native Python Twisted Interface (specific to SimulaQron)
            * Distributing a graph state

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
simulaqron start --nodes=Alice,Bob,Charlie,David --network-config-file classicalNet.json --simulaqron-config-file simulaqron_settings.json
```

This will read the JSON configuration files and start the SimulaQron virtual nodes for nodes `Alice`, `Bob`,
`Charlie` and `David`.

After this, you can simply run the example by using the `run` script:
```bash
./run.sh
```

# How to stop the execution in case the test execution stalls.

To fully stop the execution, you can use the `terninate` script:
```bash
./terminate.sh
```

Us you want to terminate the current execution and start a new one, you can use the `doNew` script. This will stop
the current execution and run the example once again:
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

After this, you can try to start the network again.


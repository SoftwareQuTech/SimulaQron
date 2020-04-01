CHANGELOG
=========

For more details refer to the [documentation](https://softwarequtech.github.io/SimulaQron/html/index.html).

Upcoming
--------

2020-04-01 (v3.0.15)
-------------------
- Security patch: require twisted 20.3 or higher

2020-02-23 (v3.0.14)
-------------------
- Fixed some old tests and improved how a network checks if it's running or not.

2020-02-23 (v3.0.13)
-------------------
- Fixed bug in the Boolean Gaussian elimination in stabilizer formalism.

2020-01-27 (v3.0.12)
-------------------
- Boolean Gaussian elimination in stabilizer formalism is now even faster.

2020-01-27 (v3.0.11)
-------------------
- Boolean Gaussian elimination in stabilizer formalism is now faster.

2019-10-30 (v3.0.10)
-------------------
- SimulaQron compatible with `cqc` version 3.1.0.

2019-10-24 (v3.0.9)
-------------------
- Fixed bug in the stabilizer formalism which can occur when measuring a qubit in an eigenstate of Z.

2019-10-16 (v3.0.8)
-------------------
- Now requiring cqc 3.0.4 after bug-fix.

2019-10-09 (v3.0.7)
-------------------
- Now requiring twisted 19.7 due to security vulnerabilities with earlier versions.

2019-10-09 (v3.0.6)
-------------------
- Now requiring cqc 3.0.3 after bug-fix.

2019-10-08 (v3.0.5)
-------------------
- Fixed bug that mixes up return messages for different application IDs.

2019-05-29 (v3.0.4)
-------------------
- Removed dependency for black, now supporting python >=3.5.

2019-05-23 (v3.0.3)
-------------------
- Fixed bug with keeping the folder `.simulaqron_pids` when installing from wheel.

2019-05-23 (v3.0.2)
-------------------
- Fixed bug with the command `simulaqron get noisy-qubits`

2019-04-30 (v3.0.1)
-------------------
 - The packages Cython, service_identity, matplotlib and bitstring are no longer direct requirements of simulaqron.

2019-04-27 (v3.0.0)
-------------------
 - The way settings and network configurations is handled from files is completely changes. Settings can still be set in the usual way through the CLI, for example as `simulaqron set backend projectq`. One can now also add a file in the users home folder (i.e. `~`) called `.simulaqron.json` where one can set settings or subsets of these. For example this file could look like
 ```
 {
    "backend": "projectq",
    "log_level": 10
 }
 ```
 which would set the backend to be use ProjectQ and the log-level to be debug (10). Any setting in this file will override the settings set in the CLI.
The old way of configuring networks (i.e. using the four .cfg files for socket addresses and one .json for topology) is still supported but the new one using a single .json file is now the recommended way. The new way uses a single .json file for all the processes for multiple networks, including the topology. An example of such a file can be seen below which contains two networks ("default" and "small_network") which the nodes "Alice", "Bob" and "Test" respectively.
```
{
    "default": {
        "nodes": {
            "Alice": {
                "app_socket": [
                    "localhost",
                    8000
                ],
                "cqc_socket": [
                    "localhost",
                    8001
                ],
                "vnode_socket": [
                    "localhost",
                    8004
                ]
            },
            "Bob": {
                "app_socket": [
                    "localhost",
                    8007
                ],
                "cqc_socket": [
                    "localhost",
                    8008
                ],
                "vnode_socket": [
                    "localhost",
                    8010
                ]
            }
        },
        "topology": null
    }
    "small_network": {
        "nodes": {
            "Test": {
                "app_socket": [
                    "localhost",
                    8031
                ],
                "cqc_socket": [
                    "localhost",
                    8043
                ],
                "vnode_socket": [
                    "localhost",
                    8089
                ]
            }
        },
        "topology": null
    }
}
```
If you want simulaqron to use your custom network.json file simply set this in the settings by `simulaqron set network-config-file your/path/my_network.json` or add the following line to a file `~/.simulaqron.json`: `network_config_file: your/path/my_network.json`, where `your/path/my_network.json` is the path to your custom network config file.

2019-04-08 (v2.2.0)
-------------------
 - The classes `simulaqron.cqc_backend.cqcProtocol.CQCProtocol` and `simulaqron.cqc_backend.cqcMessageHandler.CQCMessageHandler` move to `cqc.Protocol.CQCProtocol` and `cqc.MessageHandler.CQCMessageHandler` respectively in the repo https://github.com/SoftwareQuTech/CQC-Python.


2019-04-05 (v2.1.2)
-------------------
 - Moved new_ent_id up from simulaqronCQCHandler to CQCMessageHandler
 

2019-03-29 (v2.1.1)
-------------------

Tests can now be run from python from the method `simulaqron.tests`.


2019-03-28 (v2.1.0)
-------------------
These are changes in Develop will be merged to master.

 - The CQC specification and libraries will move to it's own repos.

 - SimulaQron can now be installed using `pip3 install simulaqron`.

 - If SimulaQron is installed using pip, the command in the terminal will be called `simulaqron` and not `SimulaQron`.

 - There is a new command in the which is useful if something crashed when a simulated network was running. Simply to `simulaqron reset`.

 - All settings can be accessed through the command line interface by the commands `simulaqron set` and `simulaqron get`.


2019-03-15 (v1.3)
-----------------

These are changes in Develop was merged to master.

- (Breaking change) The folders `general`, `local`, `toolbox` and `virtNode` and the files `configFiles.py` and `settings.py` will be moved to a folder `simulaqron`, such that imports should be done as `simulaqron.xxx`. Accordingly the PYTHONPATH should now be set to `/your/path/SimulaQron`. Imports of cqc should now instead be `from cqc.pythonLib import CQCConnection`.

- The packages `qutip` and `projectq` will be optional and the stabilizer backend default.

- The environment variable does not need to be set anymore.

- All calls to python will be done as `python` such that no virtual environment is needed.

- The method of starting a network in SimulaQron will change. Instead of calling the shell scripts `run/startAll.sh` etc
  one can now call the new command line interface as `./cli/SimulaQron start`. The same command line interface can also be used to set settings, start multiple networks etc. For more information see the docs or use the flag --help (-h) on any of the commands.
  New is also the class `simulaqron.network.Network` which makes is easy to start a network within Python, see docs.
  
- All test are now unittests and can be started as `make tests` or `make tests_full` for a longer test.

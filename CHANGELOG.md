CHANGELOG
=========

For more details refer to the [documentation](https://softwarequtech.github.io/SimulaQron/html/index.html).

Upcoming
--------


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

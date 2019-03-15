CHANGELOG
=========

For more details refer to the [documentation](https://softwarequtech.github.io/SimulaQron/html/index.html).


Upcoming
--------

These are changes in Develop which will be merged to master.

- (Breaking change) The folders `general`, `local`, `toolbox` and `virtNode` and the files `configFiles.py` and `settings.py` will be moved to a folder `simulaqron`, such that imports should be done as `simulaqron.xxx`. Accordingly the PYTHONPATH should now be set to `/your/path/SimulaQron`. Imports of cqc should now instead be `from cqc.pythonLib import CQCConnection`.

- The packages `qutip` and `projectq` will be optional and the stabilizer backend default.

- The environment variable does not need to be set anymore.

- All calls to python will be done as `python` such that no virtual environment is needed.

- The method of starting a network in SimulaQron will change. Instead of calling the shell scripts `run/startAll.sh` etc
  one can now call the new command line interface as `./cli/SimulaQron start`. The same command line interface can also be used to set settings, start multiple networks etc. For more information see the docs or use the flag --help (-h) on any of the commands.
  New is also the class `simulaqron.network.Network` which makes is easy to start a network within Python, see docs.
  
- All test are now unittests and can be started as `make tests` or `make tests_full` for a longer test.

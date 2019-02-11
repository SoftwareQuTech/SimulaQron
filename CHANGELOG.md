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
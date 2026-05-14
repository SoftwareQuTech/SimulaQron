Troubleshooting SimulaQron
==========================

This document aims to help you troubleshooting some situations that can arise while running simulaqron applications.
This documents assumes that you have read the :doc:`SimulaQron Overview <Overview>` and
:doc:`SimulaQron Application Architecture <AppsArch>` before you proceed.

.. _logs-where:

Where do I find the logs?
-------------------------

SimulaQron is capable of logging activity under the ``/tmp/simulaqron`` folder. For the moment, this base folder
cannot be changed.

Under this folder you will find:

* *Driver log file*: Each time that you invoke que driver (``simulaqron start``), the driver will create a general log.
  This file will be called ``simulaqron-driver-<pid>.log``, where "``<pid>``" is a number corresponding to the process
  ID as reported by the OS.
* *SimulaQron's QNodeOS and Virtual Node log files*: Once that the backend is running, the spawned QNodeOS and Virtual
  Node processes will create a logs file named ``simulaqron-<qnos/vnode>-<node_name>-<pid>.log``. From the file name
  you'll be able to identify if the log file corresponds to QNodeOS or Virtual Node process, the node name, and the
  process ID as reported by the OS.

Since the applications are run manually from a terminal (or by invoking the ``run.sh`` script), they do not generate
a log file, but their output can be seen in the terminal where you are running the application.


How can I increase/decrease the verbosity of the log files?
-----------------------------------------------------------

By default, the log verbosity level is set to "warning". This means that the information shown in the logs only
contains lines that are logged with severity "warning" or higher. YOu can increase the verbosity to see more debugging
messages. To do so, edit your ``simulaqron_config.json`` file and change the "log_level" line from::

    "log_level": 30,

to::

    "log_level": 10,

to change the verbosity to "debug" level. You can also change the log level to other levels. Please check the
`Python Logging Level documentation <https://docs.python.org/3.12/library/logging.html#logging-levels>`_ to find the
valid values of the log level that you can use in this field.

.. warning:: **Do not forget** to change the log level back to the default value (30) **before** submitting your solution.

After changing the log configuration, stop your application, stop SimulaQron backend, start SimulaQron backend and then
start your application again.


How can I "follow" the log files on real time?
----------------------------------------------

Unix systems (Linux and macOS) embed the ``tail`` tool that allows you to follow a file as it grows. This is useful to
print a log file on the terminal, and keep "listening to" new updates as they are written on the file. To do so, run
the following command on a separate terminal::

    tail -f /my/log/file.log

Adjust the ``/my/log/file.log`` path to match the file you want to follow on real time. This command will print on the
terminal the last 10 lines of the file, and the will keep waiting for new lines to arrive. As soon as they arrive, they
will also be printed don the terminal.


I run my application, and nothing happens; it seems SimulaQron is stuck
-----------------------------------------------------------------------

This can happen for multiple reasons. We will try to address a few of them here.


Another instance of the backend is still running
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The most common scenario arises when you are trying to run the application layer using a backend from "another version".
This can happen when you update the port numbers in the ``simulaqron_networks.json`` file and you did not restart the
backend after that.

In this case try restarting simulaqron backend by running::

    simulaqron stop

and then running the ``simulaqron start`` command as per the example or step of the lab you are currently following.

If after this the error persist, check the code of the application (usually alice and/or bob) and make sure that these
file load the same ``simulaqron_settings.json`` and ``simulaqron_config.json`` files as the ```simulaqron start``
command.

.. _exception-in-backend:

Exceptions on the backend
^^^^^^^^^^^^^^^^^^^^^^^^^

When running the backend, the spawned processes are daemonized, meaning that if an exception happens there, it is not
possible to see that on the terminal. When an exception happened in the backend, some of the TCP ports used to execute
quantum operations are not properly open, and your application might be waiting for a connection or message that will
never arrive.

To check the state of the backend, you can check the log files. Check the section about
:ref:`how to check the logs <logs-where>` and search for ``Exception``, ``Error``, or ``Traceback`` to look for
more clues about what is happening.


.. _not-proper-proto-impl:

Protocol not implemented properly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another usual scenario where your application looks stalled is because of error when implementing classical messages
interchange. In some cases, your client or server side application is waiting for the arrival of a message. Once it
arrived, it reads the characters from the classical socket, and check if it the expected message or not.

In this case, make sure that you properly check the expected string, and raise and exception or fail the execution if
something unexpected happen. To this last end, you can use python asserts to aid you in that::

    assert message == "expected"

The line above will make whole program fail if ``message`` is not exactly the string ``expected``.

.. caution:: Killing a single process might leave some other processes (application nodes) still running in the
   background. This might lead to scenarios where subsequent execution might fail with connection errors. To fully
   stop any application nodes running in the background, check :ref:`how to kill leftover processes <process-leftovers>`
   in the following sections.


Log files say "Connection was closed cleanly"
---------------------------------------------

This is a rather tricky error. You can check for 3 scenarios:

* *Protocol errors*: When sending messages to other nodes using classical sockets, make sure that you are sending the
  right messages at the right time. If this doesn't happen, a node can be waiting for a message that will never arrive
  and the connection will timeout or simply be closed by the server. This is the same case as
  :ref:`protocol not implemented properly <not-proper-proto-impl>` from last section.
* *Using a port taken by another service*. In some instances, port numbers can already be taken by system processes.
  This makes the SimulaQron backend to not start correctly (but remember that you won't know about this unless you
  check the logs), which later leads to issues when running the application layer. If the port is taken by a system
  process, it is usually expecting to follow a specific protocol with the communications. SimulaQron will connect to
  the port, and send a message that *does not follow* the expected protocol. In this case, and for security reasons,
  the system will simply close the connection to the client, leading to the error.
* *Limited resources on the host machine*: In some rare instances, a lack of system resources will lead to the
  communications to timeout, hence triggering a close of the connection by the OS. This is reported as a "clean close"
  of the connection.


.. _process-leftovers:

How can I check if there are "leftover" processes from old executions?
----------------------------------------------------------------------

The simplest way to do this in Unix platforms (Linux and macOS) is by using the ``ps`` and ``awk`` commands::

    $ ps aux | awk 'NR==1 || /python/'
    USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
    root        1723  0.0  0.0 114868 23364 ?        Ssl  08:15   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
    user       12551  0.1  0.1 933284 61996 ?        S    11:25   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12552  0.0  0.1 1000028 63040 ?       Sl   11:25   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12553  0.0  0.1 1000028 63040 ?       Sl   11:25   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12556  0.0  0.1 1000028 62968 ?       Sl   11:26   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12557  0.0  0.1 1000028 62968 ?       Sl   11:26   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12929 13.2  0.2 1153540 83836 pts/1   Sl+  11:30   0:01 python bobTest.py
    user       12561  0.0  0.0  11764  2360 pts/1    S+   11:26   0:00 awk NR==1 || /python/

The command ``ps aux`` returns a list of *all* the running processes on the system, which is then filtered by the
``awk`` command. After this pipeline, the system shows you a list of all commands that contain the string "python"
in their command line.

In the example above, it is important to identify some information. The ``PID`` and ``COMMAND`` columns are the most
important ones. We will use them to identify which processes can be terminated:

* Processes that contain ``simulaqron start`` in their commandline, they are *SimulaQron backend-related processes*.
* Processes that are simply ``python myTest.py`` *are usually SimulaQron application processes*. Try to remember
  if you manually started these processes (or via the ``run.sh`` script) to correctly identify it.
* All other processes on the list *are usually system processes*. **These processes need to left untouched**.

Once that you have identified that you have some leftover processes from old executions, you can try two ways to stop
these processes:

* Run ``simulaqron reset processes``. As explained in the :ref:`starting backend section <starting-backend>`, this
  command can be used to forcefully stop any backend-related processes. If you run this command and run get the list
  of python processes, you'll see that some of them are not there anymore::

    $ simulaqron reset processes
    Are you sure you want to forcefully stop all the `simulaqron` processes? [y/N]: y
    $ ps aux | awk 'NR==1 || /python/'
    USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
    root        1723  0.0  0.0 114868 23364 ?        Ssl  08:15   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
    user       12929 13.2  0.2 1153540 83836 pts/1   Sl+  11:30   0:01 python bobTest.py
    user       12561  0.0  0.0  11764  2360 pts/1    S+   11:26   0:00 awk NR==1 || /python/

  You can see that all the SimulaQron backend processes are not in the list anymore.
* Run ``kill -9`` with specific PIDs. Another alternative is to manually send the *SIGKILL* signal (signal #9) to
  all the processes that you can identify as part of the SimulaQron execution. To do this, you need to get the list of
  processes as mentioned above, identify the processes that you want to terminate, and make note of their PID number.
  Once that you have the list of PID numbers, you can simply use the ``kill`` command to send the signal to those
  processes::

    $ ps aux | awk 'NR==1 || /python/'
    USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
    root        1723  0.0  0.0 114868 23364 ?        Ssl  08:15   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
    user       12551  0.1  0.1 933284 61996 ?        S    11:25   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12552  0.0  0.1 1000028 63040 ?       Sl   11:25   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12553  0.0  0.1 1000028 63040 ?       Sl   11:25   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12556  0.0  0.1 1000028 62968 ?       Sl   11:26   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12557  0.0  0.1 1000028 62968 ?       Sl   11:26   0:00 /path/to/venvs/simulaqron/bin/python /path/to/venvs/simulaqron/bin/simulaqron start --nodes=Alice,Bob --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    user       12929 13.2  0.2 1153540 83836 pts/1   Sl+  11:30   0:01 python bobTest.py
    user       12561  0.0  0.0  11764  2360 pts/1    S+   11:26   0:00 awk NR==1 || /python/
    $ kill -9 12551 12552 12553 12556 12557 12929
    $ ps aux | awk 'NR==1 || /python/'
    USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
    root        1723  0.0  0.0 114868 23364 ?        Ssl  08:15   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
    user       12561  0.0  0.0  11764  2360 pts/1    S+   11:26   0:00 awk NR==1 || /python/

  You can see that we were able to kill the leftover SimulaQron application process (``python bobTest.py``).

.. note:: When running ``kill``, if you get errors like "kill: (<PID>) - No such process", you can safely ignore them.
   This error means that you specified a PID that was not valid. Recheck the process list ans try again.

.. _check-port:

How can I check if a port is taken or not?
------------------------------------------

First of all, a running system is dynamic, so there's no guarantee that a port available now will still be available
in 5 minutes more. Despite this, if you pick a port number (ranging from :math:`1` to :math:`65535`) cleverly enough,
it will most likely be available whenever you need it.

In Linux, port numbers under :math:`1000` need sudo permissions to be used, so we highly recommend *not* to use them.
Apart from this, any other port is pretty much free to use. In our case, we *prefer* to use port numbers between
:math:`8000` and :math:`9000`, which are usually not used by any normal system service.

Being this said, choose any port that you want, but before using it, check if it is available on your system. On Linux
platform, you can use the command ``netstat -tlpn``::

    $ netstat -tlpn
    (Not all processes could be identified, non-owned process info
     will not be shown, you would have to be root to see it all.)
    Active Internet connections (only servers)
    Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
    tcp        0      0 192.168.122.1:53        0.0.0.0:*               LISTEN      -
    tcp        0      0 127.0.0.1:34623         0.0.0.0:*               LISTEN      -
    tcp        0      0 127.0.0.54:53           0.0.0.0:*               LISTEN      -
    tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      -
    tcp        0      0 127.0.0.1:35539         0.0.0.0:*               LISTEN      32651/some_prog
    tcp        0      0 192.168.20.249:443      0.0.0.0:*               LISTEN      -
    tcp        0      0 192.168.20.249:80       0.0.0.0:*               LISTEN      -
    tcp        0      0 192.168.20.249:8080     0.0.0.0:*               LISTEN      -
    tcp        0      0 0.0.0.0:445             0.0.0.0:*               LISTEN      -
    tcp        0      0 0.0.0.0:139             0.0.0.0:*               LISTEN      -
    tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -
    tcp        0      0 127.0.0.1:32600         0.0.0.0:*               LISTEN      -
    tcp        0      0 127.0.0.1:32401         0.0.0.0:*               LISTEN      -
    tcp6       0      0 127.0.0.1:50293         :::*                    LISTEN      32825/some_prog_b
    tcp6       0      0 127.0.0.1:37235         :::*                    LISTEN      32825/some_prog_b
    tcp6       0      0 127.0.0.1:5990          :::*                    LISTEN      32825/some_prog_b
    tcp6       0      0 :::32400                :::*                    LISTEN      -
    tcp6       0      0 :::445                  :::*                    LISTEN      -
    tcp6       0      0 :::139                  :::*                    LISTEN      -
    tcp6       0      0 :::22                   :::*                    LISTEN      -
    tcp6       0      0 127.0.0.1:42391         :::*                    LISTEN      50115/some_prog_c
    tcp6       0      0 127.0.0.1:63342         :::*                    LISTEN      32825/some_prog_b

On macOS, you can use the command ``netstat -anvp tcp | awk 'NR<3 || /LISTEN/'``::

    % netstat -anp tcp | awk 'NR<3 || /LISTEN/'
    Active Internet connections (including servers)
    Proto Recv-Q Send-Q  Local Address                                 Foreign Address                               (state)
    tcp4       0      0  127.0.0.1.6189         *.*                    LISTEN
    tcp4       0      0  127.0.0.1.6188         *.*                    LISTEN
    tcp4       0      0  127.0.0.1.50293        *.*                    LISTEN
    tcp4       0      0  127.0.0.1.5990         *.*                    LISTEN
    tcp4       0      0  127.0.0.1.63342        *.*                    LISTEN
    tcp4       0      0  127.0.0.1.49152        *.*                    LISTEN
    tcp6       0      0  ::1.49152              *.*                    LISTEN
    tcp4       0      0  127.0.0.1.9010         *.*                    LISTEN
    tcp6       0      0  *.50168                *.*                    LISTEN
    tcp4       0      0  *.50168                *.*                    LISTEN
    tcp4       0      0  127.0.0.1.52829        *.*                    LISTEN
    tcp4       0      0  127.0.0.1.65364        *.*                    LISTEN
    tcp4       0      0  127.0.0.1.49229        *.*                    LISTEN
    tcp6       0      0  *.5000                 *.*                    LISTEN
    tcp4       0      0  *.5000                 *.*                    LISTEN
    tcp6       0      0  *.7000                 *.*                    LISTEN
    tcp4       0      0  *.7000                 *.*                    LISTEN
    tcp4       0      0  127.0.0.1.9180         *.*                    LISTEN
    tcp4       0      0  127.0.0.1.8021         *.*                    LISTEN
    tcp6       0      0  ::1.8021               *.*                    LISTEN

On both systems, the column "Local Address" will give you information about the IP and port numbers already taken. That
column has the format ``<IP>:<port>``, where ``IP`` follows the format ``AAA.BBB.CCC.DDD``, which is the followed by
the port number. If your chosen port number is not on the list, it's free to use!


Installation Issues
-------------------

This section is intended to provide a way to solve the most common problems when installing SimulaQron. Please note
that **this list is not exhaustive**, and it is provided in a best-effort basis.


Windows
^^^^^^^

Installation in Windows environments *is only supported using a VM or WSL*. To install WSL on your Windows environment,
please refer to the `official microsoft documentation <https://learn.microsoft.com/en-us/windows/wsl/install>`_.

After you installed WSL, you can follow the Linux installation instructions.


Linux-specific errors
^^^^^^^^^^^^^^^^^^^^^

The instructions assume that you are running a Debian-based linux distribution (like Ubuntu).


Cannot find the ``python3.12`` package
""""""""""""""""""""""""""""""""""""""

Python 3.12 is a rather old python version. For this reason, this python version *is not available* in most of the
recent distribution versions. To have access to this version, you need to add the "Deadsnakes" repository by running::

    $ sudo add-apt-repository -y "ppa:deadsnakes/ppa"
    $ sudo apt-get update

After running that, try installing Python 3.12 again.


``python3.12 -m ensurepip --upgrade --default-pip`` returned non-zero exit status 1
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

This usually happens when creating a python virtual environment. The main reason for this error is that you are
missing the ``python3.12-venv`` package. For SimulaQron to run, we need the full installation of Python 3.12,
including the development package::

    $ sudo apt-get install python3.12-full python3.12-dev

After installing this, try creating your virtual environment again.


error: command 'x86_64-linux-gnu-g++' failed: No such file or directory
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

This usually happens when installing simulaqron using pip *with the optional dependencies* (i.e.
``pip install "simulaqron[opt]"``), on a machine that does not have a C++ compiler. Please make sure that you install
all the requirements by running::

    $ sudo apt-get install build-essential cmake vim git linux-headers-generic

Then try to install simulaqron with the optional dependencies again.


macOS-specific errors
^^^^^^^^^^^^^^^^^^^^^


error: command 'x86_64-linux-gnu-g++' failed: No such file or directory
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

This usually happens when installing simulaqron using pip *with the optional dependencies* (i.e.
``pip install "simulaqron[opt]"``), on a machine that does not have a C++ compiler. Please make sure that you install
all the requirements by running::

    % xcode-select --install

And follow the options for installing XCode build tools.


General installation errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^


fatal error: Python.h: No such file or directory
""""""""""""""""""""""""""""""""""""""""""""""""

This happens when you are missing the ``python3.12-dev`` package. On Linux, run::

    $ sudo apt-get install python3.12-dev

On macOS, brew should install the development dependencies. You can always try to install python again::

    % brew reinstall python@3.12

After this, try installing simulaqron again.


'Compiler' object has no attribute 'dry_run'
""""""""""""""""""""""""""""""""""""""""""""

This error arises when trying to install simulaqron with the optional dependencies. One of them is
`ProjectQ <https://projectq.ch/>`_, which is a rather old software, written in C++. Considering this, ProjectQ
*needs to be compiled by pip* before installing it. Since ProjectQ is an old software, it relies on compilation
tools that nowadays are not part of the pip compilation toolchain.

*On Linux systems* we can fix this by installing the older versions of the pip toolchain, and instruct pip to
not create an isolated environment for compiling ProjectQ::

    $ pip install "setuptools<81" pybind11
    $ pip install "git+https://github.com/ProjectQ-Framework/ProjectQ.git@v0.8.0" --no-build-isolation

*On macOS systems*, we have also observed this error when compiling `QuTip <http://qutip.org/>`_. In this case, you
can also instruct pip to compile Qutip with the older toolchain::

    % pip install "setuptools<81" pybind11 Cython
    % pip install "git+https://github.com/ProjectQ-Framework/ProjectQ.git@v0.8.0" --no-build-isolation
    % pip install "qutip<5.0.0" --no-build-isolation

.. warning:: Please note that compiling the packages might take more than a few minutes. As an alternative, we provide
   **unofficial packages already compiled** for the platforms supported by SimulaQron. To use these **unofficial
   distributions**, add an option to ``pip`` to look for ``qutip`` and ``projectq`` packages on an 3rd party repository::

       $ pip install projectq qutip --index-url https://gitlab.tudelft.nl/api/v4/projects/28442/packages/pypi/simple

Then you can try to install simulaqron with optional dependencies again.

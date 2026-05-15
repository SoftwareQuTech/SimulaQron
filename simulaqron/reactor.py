import sys

if sys.platform == "linux":
    # "pollreactor" performs better than "asyncioreactor", but at the cost of
    # not having interoperability with python's asyncio library.
    # This is fine, since the backend of SimulaQron (the part using twisted
    # library) does not make use of python asyncio functions.
    # Since the written applications (which do use asyncio) will run in separate
    # (heavy) processes, this change in the backend does not conflict with the
    # writing of SimulaQron applications.
    from twisted.internet import pollreactor

    pollreactor.install()

if sys.platform == "darwin":
    # On macOS platforms, "pollreactor" enable to run SimulaQron without any problems.
    from twisted.internet import pollreactor

    pollreactor.install()

if sys.platform == "win32":
    # TODO - Find out which is the right twisted reactor for Win
    #  Hint: Claude says that "selectreactor"  and "IOCPReactor" are supported on Windows
    from twisted.internet import selectreactor
    selectreactor.install()

from twisted.internet import reactor  # noqa: E402

__all__ = [
    "reactor"
]

"""
The reactor module helps installing the correct twisted reactor.
In SimulaQron, it is *highly encouraged* to use the rector offered by this module
rather than the one available in the ``twisted.internet`` package::

from simulaqron.reactor import reactor
...
reactor.run()
...
reactor.stop()
"""

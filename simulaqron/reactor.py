import sys

if sys.platform == "darwin":
    from twisted.internet import pollreactor

    pollreactor.install()

if sys.platform == "linux":
    # TODO - Find out which is the right twisted reactor for Linux
    #  Currently "asyncioreactor" works, and allow interoperability with asyncio primitives.
    #  However, this reactor is slow, and asyncio support is not needed on the background
    #  processes that run the simulaqron backend.
    from twisted.internet import asyncioreactor

    asyncioreactor.install()

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

from twisted.internet import asyncioreactor

asyncioreactor.install()

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
reactor.start()
...
reactor.stop()
"""
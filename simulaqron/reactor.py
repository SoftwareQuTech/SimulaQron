from twisted.internet import asyncioreactor

asyncioreactor.install()

from twisted.internet import reactor  # noqa: E402

__all__ = [
    "reactor"
]

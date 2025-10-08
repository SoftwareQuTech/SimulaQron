from twisted.internet import epollreactor
epollreactor.install()

from twisted.internet import reactor  # noqa: E402

__all__ = [
    "reactor"
]

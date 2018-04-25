import sys

from SimulaQron.settings import Settings

Settings.set_setting("BACKEND", "BackendHandler", sys.argv[1])

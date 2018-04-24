import sys
from settings import Settings

Settings.set_setting("BACKEND", "BackendHandler", sys.argv[1])

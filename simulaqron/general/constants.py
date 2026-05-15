from pathlib import Path


SIMULAQRON_LOGS_FOLDER = Path("/tmp/simulaqron")

# If the logs folder does not exist, create it
if not SIMULAQRON_LOGS_FOLDER.exists():
    Path.mkdir(SIMULAQRON_LOGS_FOLDER)

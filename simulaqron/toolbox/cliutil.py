import psutil
from typing import List


def find_processes_by_cmdline(process_name: str) -> List[psutil.Process]:
    """Find all processes matching the given name."""
    matching_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if the process name matches
            if proc.info['cmdline'] and process_name in ' '.join(proc.info['cmdline']):
                matching_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return matching_processes

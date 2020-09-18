import os
import sys

from simulaqron.run.simulate import simulate_apps


def main(log_level):
    app_dir = os.path.dirname(os.path.abspath(__file__))
    simulate_apps(
        app_dir=app_dir,
        log_level=log_level,
    )


if __name__ == "__main__":
    if len(sys.argv) == 2:
        log_level = sys.argv[1]
    else:
        log_level = "WARNING"
    main(log_level=log_level)
    print("main finished")

import sys

from simulaqron.run.simulate import simulate_apps


def main(app_dir):
    simulate_apps(
        app_dir=app_dir,
        formalism="DM",
        log_level="DEBUG",
    )


if __name__ == "__main__":
    main(sys.argv[1])

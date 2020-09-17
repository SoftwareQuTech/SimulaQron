import os

from simulaqron.run.simulate import simulate_apps


def main():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    simulate_apps(
        app_dir=app_dir,
    )


if __name__ == "__main__":
    main()

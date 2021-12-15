import os

from simulaqron.settings import simulaqron_settings
from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor


def check_config_files():
    if not os.path.exists(simulaqron_settings.network_config_file):
        _create_default_network_config()


def _create_default_network_config():
    networks_config = NetworksConfigConstructor()
    networks_config.reset()
    networks_config.write_to_file(simulaqron_settings.network_config_file)


def main():
    simulaqron_settings.default_settings()
    _create_default_network_config()


if __name__ == '__main__':
    main()

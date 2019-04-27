from simulaqron.settings import simulaqron_settings
from simulaqron.toolbox.manage_nodes import NetworksConfigConstructor


def main():
    simulaqron_settings.default_settings()
    networks_config = NetworksConfigConstructor()
    networks_config.reset()
    networks_config.write_to_file(simulaqron_settings.network_config_file)


if __name__ == '__main__':
    main()

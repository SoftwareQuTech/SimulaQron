from .network_config import NetworkConfigBuilder, DEFAULT_SIMULAQRON_NETWORK_FILENAME
from .simulaqron_config import SimulaqronConfig, DEFAULT_SIMULAQRON_SETTINGS_FILENAME
from ._serialization import init_serialization

init_serialization()

# Centralized way to store the config. It reads the local configuration
# if exists, otherwise, it simply populates the in-memory configs object
# with the default values
simulaqron_settings = SimulaqronConfig.load_from_known_sources()

# Centralized way to store the config of the network. It reads the local
# configuration if exists, otherwise, it simply populates the in-memory
# configs object with the default values
network_config = NetworkConfigBuilder.load_from_known_sources()

# We follow a similar approach with the network config builder: read the
# file pointed by the simulaqron_settings (if exists) or initialize a new
# builder that contains only the default network.
# network_configs = NetworkConfigBuilder()
# network_configs.read_from_file(simulaqron_settings.network_config_file)

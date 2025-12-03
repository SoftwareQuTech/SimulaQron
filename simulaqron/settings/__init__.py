from .network_config import NetworkConfigBuilder, DEFAULT_SIMULAQRON_NETWORK_FILENAME, LOCAL_NETWORK_SETTINGS, HOME_NETWORK_SETTINGS
from .simulaqron_config import SimulaqronConfig, DEFAULT_SIMULAQRON_SETTINGS_FILENAME, LOCAL_SIMULAQRON_SETTINGS, HOME_SIMULAQRON_SETTINGS
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
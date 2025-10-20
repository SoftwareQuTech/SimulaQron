from .network_config import NetworkConfigBuilder
from .simulaqron_config import Config


# Centralized way to store the config. It reads the local configuration
# if exists, otherwise, it simply populates the in-memory configs object
# with the default values
simulaqron_settings = Config()

# We follow a similar approach with the network config builder: read the
# file pointed by the simulaqron_settings (if exists) or initialize a new
# builder that contains only the default network.
network_configs = NetworkConfigBuilder()

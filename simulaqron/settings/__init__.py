from enum import Enum
from pathlib import Path
from typing import Type

from dataclasses_serialization.json import JSONSerializer
from dataclasses_serialization.serializer_base import DeserializationError

from .network_config import NetworkConfigBuilder
from .simulaqron_config import SimulaqronConfig, SIMULAQRON_SETTINGS_FILENAME


# Registration of Serializer for python enums
@JSONSerializer.register_serializer(Enum)
def enum_serializer(obj: Enum) -> str:
    return obj.name


# Registration of Deserializer for python enums
@JSONSerializer.register_deserializer(Enum)
def enum_deserializer(cls: Type[Enum], name: str) -> Enum:
    try:
        fixed_name = name.replace("-", "_").upper()
        return cls[fixed_name]
    except KeyError as ex:
        raise DeserializationError(
            f"String '{name}' could not be deserialized to a valid "
            f"value of type '{cls.__name__}'."
        ) from ex


# Registration of Serializer for python enums
@JSONSerializer.register_serializer(Path)
def path_serializer(obj: Path) -> str:
    return str(obj.resolve())


# Registration of Deserializer for python enums
@JSONSerializer.register_deserializer(Path)
def path_deserializer(cls: Type[Path], path: str) -> Path:
    if path == "$DEFAULT_NETWORK":
        return (cls.home() / ".simulaqron" / SIMULAQRON_SETTINGS_FILENAME).resolve()
    return cls(path).resolve()


# Centralized way to store the config. It reads the local configuration
# if exists, otherwise, it simply populates the in-memory configs object
# with the default values
simulaqron_settings = SimulaqronConfig.load_from_known_sources()

# We follow a similar approach with the network config builder: read the
# file pointed by the simulaqron_settings (if exists) or initialize a new
# builder that contains only the default network.
# network_configs = NetworkConfigBuilder()
# network_configs.read_from_file(simulaqron_settings.network_config_file)

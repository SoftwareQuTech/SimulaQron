from enum import Enum
from pathlib import Path
from typing import Type

from dataclasses_serialization.json import JSONSerializer
from dataclasses_serialization.serializer_base import DeserializationError

from ..settings.simulaqron_config import SIMULAQRON_SETTINGS_FILENAME

def init_serialization():
    # Nothing to do here; we just need to execute this file
    # to register the serializers
    pass


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

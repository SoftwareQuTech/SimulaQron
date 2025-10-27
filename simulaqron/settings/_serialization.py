from enum import Enum
from pathlib import Path
from typing import Type, Dict, Any

from dataclasses_serialization.json import JSONSerializer
from dataclasses_serialization.serializer_base import DeserializationError, dict_serialization

from ..settings.simulaqron_config import SIMULAQRON_SETTINGS_FILENAME, SimulaqronConfig, SimBackend


def init_serialization():
    # Nothing to do here; we just need to execute this file
    # to register the serializers
    pass


# Registration of Serializer for python enums
@JSONSerializer.register_serializer(Enum)
def enum_serializer(obj: Enum) -> str:
    return str(obj)


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


@JSONSerializer.register_serializer(SimulaqronConfig)
def simulaqron_config_serializer(obj: SimulaqronConfig) -> str:
    object_dict = dict(obj.__dict__)
    net_cfg_path = str(obj.network_config_file)
    del object_dict["_builder"]
    del object_dict["_net_cfg_file"]
    object_dict["network_config_file"] = net_cfg_path
    serialized = JSONSerializer.serialize(dict_serialization(object_dict))
    return serialized


@JSONSerializer.register_deserializer(SimulaqronConfig)
def simulaqron_config_deserializer(cls: Type[SimulaqronConfig], obj: Dict[str, Any]) -> SimulaqronConfig:
    new_obj = cls(network_config_file=obj["network_config_file"])
    new_obj.max_qubits = obj["max_qubits"]
    new_obj.max_registers = obj["max_registers"]
    new_obj.conn_retry_time = obj["conn_retry_time"]
    if "conn_max_retries" in obj:
        new_obj.conn_max_retries = obj["conn_max_retries"]
    new_obj.recv_timeout = obj["recv_timeout"]
    new_obj.recv_retry_time = obj["recv_retry_time"]
    if "recv_max_retries" in obj:
        new_obj.recv_max_retries = obj["recv_max_retries"]
    new_obj.log_level = obj["log_level"]
    new_obj.sim_backend = JSONSerializer.deserialize(SimBackend, obj["sim_backend"])
    new_obj.noisy_qubits = obj["noisy_qubits"]
    new_obj.t1 = obj["t1"]
    return new_obj

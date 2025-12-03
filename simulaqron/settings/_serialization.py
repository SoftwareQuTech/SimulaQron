from enum import Enum
from pathlib import Path
from typing import Type, Dict, Any, List

from dataclasses_serialization.json import JSONSerializer
from dataclasses_serialization.serializer_base import DeserializationError

from .network_config import NodeConfig, NetworkConfig, NetworkConfigBuilder
from ..settings import HOME_SIMULAQRON_SETTINGS
from ..settings.simulaqron_config import SimulaqronConfig, SimBackend


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
    match path:
        case "$DEFAULT_NETWORK":
            return HOME_SIMULAQRON_SETTINGS
        case _:
            return cls(path)


@JSONSerializer.register_deserializer(SimulaqronConfig)
def simulaqron_config_deserializer(cls: Type[SimulaqronConfig], obj: Dict[str, Any]) -> SimulaqronConfig:
    new_obj = cls()
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
    if "max_app_waiting_time" in obj:
        new_obj.max_app_waiting_time = obj["max_app_waiting_time"]
    new_obj.t1 = obj["t1"]
    return new_obj


@JSONSerializer.register_serializer(NodeConfig)
def node_config_serializer(obj: NodeConfig) -> Dict[str, List[str | int]]:
    node_config_dict = {
        "app_socket": [obj.app_hostname, obj.app_port],
        "qnodeos_socket": [obj.qnodeos_hostname, obj.qnodeos_port],
        "vnode_socket": [obj.vnode_hostname, obj.vnode_port]
    }
    return JSONSerializer.serialize(node_config_dict)


@JSONSerializer.register_deserializer(NodeConfig)
def node_config_deserializer(cls: Type[NodeConfig], obj: Dict[str, Any]) -> NodeConfig:
    node_name = list(obj.keys())[0]
    app_socket_host = obj[node_name]["app_socket"][0]
    app_socket_port: int = obj[node_name]["app_socket"][1]
    qnodeos_socket_host = obj[node_name]["qnodeos_socket"][0]
    qnodeos_socket_port: int = obj[node_name]["qnodeos_socket"][1]
    vnode_socket_host = obj[node_name]["vnode_socket"][0]
    vnode_socket_port: int = obj[node_name]["vnode_socket"][1]
    return cls(
        name=node_name,
        app_hostname=app_socket_host,
        qnodeos_hostname=qnodeos_socket_host,
        vnode_hostname=vnode_socket_host,
        app_port=app_socket_port,
        qnodeos_port=qnodeos_socket_port,
        vnode_port=vnode_socket_port
    )


@JSONSerializer.register_serializer(NetworkConfig)
def network_config_serializer(obj: NetworkConfig) -> Dict[str, Any]:
    nodes_dict = {
        "name" : obj.name,
        "nodes": [
            {node_cfg.name: JSONSerializer.serialize(node_cfg)}
            for node_cfg in obj.nodes.values()
        ],
        "topology": JSONSerializer.serialize(obj.topology)
    }
    return JSONSerializer.serialize(nodes_dict)


@JSONSerializer.register_deserializer(NetworkConfig)
def network_config_deserializer(cls: Type[NetworkConfig], obj: Dict[str, Any]) -> NetworkConfig:
    net_cfg = cls(obj["name"])
    for raw_node in obj["nodes"]:
        node_cfg = JSONSerializer.deserialize(NodeConfig, raw_node)
        net_cfg.add_node_config(node_cfg)
    net_cfg.topology = obj["topology"]
    return net_cfg


@JSONSerializer.register_serializer(NetworkConfigBuilder)
def network_config_builder_serializer(obj: NetworkConfigBuilder) -> List[Dict[str, Any]]:
    return [JSONSerializer.serialize(network) for network in obj.networks.values()]


@JSONSerializer.register_deserializer(NetworkConfigBuilder)
def network_config_builder_deserializer(cls: Type[NetworkConfigBuilder], obj: List[Dict]) -> NetworkConfigBuilder:
    new_obj = cls()
    for raw_network in obj:
        network_spec: NetworkConfig = JSONSerializer.deserialize(NetworkConfig, raw_network)
        new_obj.add_network_config(network_spec)
    return new_obj

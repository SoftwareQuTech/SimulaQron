#
# Copyright (c) 2017, Stephanie Wehner and Axel Dahlberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES
# LOSS OF USE, DATA, OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#########################
# SETTINGS FOR SIMULAQRON
#########################
import json
import logging
from dataclasses import dataclass, fields, InitVar
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Self

from dataclasses_serialization.json import JSONSerializer
from dataclasses_serialization.json import JSONSerializerMixin

from ..settings.network_config import NetworkConfigBuilder

# This is the name of the "local" simulaqron settings.
# If a file named like this is found in the CWD, it will be
# automatically loaded when creating the config file
DEFAULT_SIMULAQRON_SETTINGS_FILENAME = "simulaqron_settings.json"
DEFAULT_SIMULAQRON_NETWORK_FILENAME = "simulaqron_network.json"


class SimBackend(JSONSerializerMixin, Enum):
    STABILIZER = "stabilizer"
    PROJECTQ = "projectq"
    QUTIP = "qutip"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


@dataclass
class SimulaqronConfig(JSONSerializerMixin):
    network_config_file: InitVar[Path] = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()
    # Default config
    max_qubits: int = 20
    max_registers: int = 1000
    conn_retry_time: float = 0.5
    conn_max_retries: int = 10
    recv_timeout: int = 100
    recv_retry_time: float = 0.1
    recv_max_retries: int = 10
    log_level: int = logging.WARNING
    sim_backend: SimBackend = SimBackend.STABILIZER
    noisy_qubits: bool = False
    max_app_waiting_time: float = -1.0  # In seconds, negative means unlimited waiting
    t1: float = 1.0

    def __post_init__(self, network_config_file: Path):
        if isinstance(network_config_file, Path) and network_config_file.exists() and network_config_file.is_file():
            self._builder = NetworkConfigBuilder()
            net_cfg_file = network_config_file
        else:
            # Given network config file is invalid or does not exist. Use the default one
            # and write it to the expected location
            net_cfg_file = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_NETWORK_FILENAME).resolve()
            self._builder = NetworkConfigBuilder.using_default_network()
            self._builder.write_to_file(net_cfg_file)
        self.network_config_file = net_cfg_file

    @property
    def network_builder(self) -> NetworkConfigBuilder:
        return self._builder

    @property
    def network_config_file(self) -> Path:
        return self._net_cfg_file

    @network_config_file.setter
    def network_config_file(self, value: Path | str):
        if isinstance(value, str):
            value = Path(value).resolve()
        # If we set the network config file, update the NetworkConfigBuilder
        if value.exists() and value.is_file():
            self._builder.read_from_file(value)
        self._net_cfg_file = value

    @classmethod
    def _create_home_settings_folder(cls):
        home_setting_folder = (Path.home() / ".simulaqron").resolve()
        home_setting_folder.mkdir(parents=True, exist_ok=True)

    def load_from_file(self, file_path: Path | str):
        if isinstance(file_path, str):
            file_path = Path(file_path).resolve()
        new_config = self._deserialize_from_file(file_path)
        cls_fields = fields(self.__class__)

        for field in cls_fields:
            new_val = getattr(new_config, field.name)
            setattr(self, field.name, new_val)

        self.network_config_file = new_config.network_config_file

    @classmethod
    def _deserialize_from_file(cls, file_path: Path) -> Self:
        with file_path.resolve().open("rt") as file:
            config_content = json.load(file)
            return JSONSerializer.deserialize(cls, config_content)

    @classmethod
    def load_from_known_sources(cls) -> Self:
        cwd_settings_file = (Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME).resolve()
        home_settings_file = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_SETTINGS_FILENAME).resolve()

        files_to_load = [cwd_settings_file, home_settings_file]

        for file in files_to_load:
            try:
                if file.exists() and file.is_file():
                    return cls._deserialize_from_file(file)
            except json.JSONDecodeError:
                # Nothing to do; try next one
                pass

        # Ultimate case; we create a new config file in the ohme and load it
        new_default_config = cls()
        new_default_config.save_to_file(home_settings_file)
        return new_default_config

    def default_settings(self):
        default_config = SimulaqronConfig()
        cls_fields = fields(self.__class__)

        for field in cls_fields:
            new_val = getattr(default_config, field.name)
            setattr(self, field.name, new_val)

    def save_to_file(self, path: PathLike):
        file_path = Path(str(path)).resolve()

        # Create all the parent folder if they not exists
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)

        # Poke the file, so it exists before opening
        file_path.touch(exist_ok=True)

        with file_path.open("wt") as file:
            serialized = JSONSerializer.serialize(self)
            json.dump(serialized, file, indent=4)

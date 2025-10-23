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
from dataclasses import dataclass, fields
from enum import Enum

from dataclasses_serialization.json import JSONSerializer
from os import PathLike
from pathlib import Path
from typing import Self

from dataclasses_serialization.json import JSONSerializerMixin

# This is the name of the "local" simulaqron settings.
# If a file named like this is found in the CWD, it will be
# automatically loaded when creating the config file
SIMULAQRON_SETTINGS_FILENAME = "simulaqron_settings.json"


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
    network_config_file: Path = (Path.home() / ".simulaqron" / "default_network.json").resolve()
    noisy_qubits: bool = False
    t1: float = 1.0

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

    @classmethod
    def _deserialize_from_file(cls, file_path: Path) -> Self:
        with file_path.resolve().open("rt") as file:
            config_content = json.load(file)
            return JSONSerializer.deserialize(cls, config_content)

    @classmethod
    def load_from_known_sources(cls) -> Self:
        cwd_settings_file = (Path.cwd() / SIMULAQRON_SETTINGS_FILENAME).resolve()
        home_settings_file = (Path.home() / ".simulaqron" / SIMULAQRON_SETTINGS_FILENAME).resolve()
        if cwd_settings_file.exists() and cwd_settings_file.is_file():
            return cls._deserialize_from_file(cwd_settings_file)
        else:
            cls._create_home_settings_folder()
            if home_settings_file.exists() and cwd_settings_file.is_file():
                return cls._deserialize_from_file(home_settings_file)
            else:
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
        with file_path.open("wt") as file:
            serialized = JSONSerializer.serialize(self)
            json.dump(serialized, file)

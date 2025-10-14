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
from enum import Enum
from importlib import resources
from os import PathLike
from pathlib import Path
from typing import Dict, Any

import simulaqron._default_config

# This is the name of the "local" simulaqron settings.
# If a file named like this is found in the CWD, it will be
# automatically loaded when creating the config file
SIMULAQRON_SETTINGS_FILENAME = "simulaqron_settings.json"


class SimBackend(Enum):
    STABILIZER = "stabilizer"
    PROJECTQ = "projectq"
    QUTIP = "qutip"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


class Config:
    # Dictionary for settings
    _config: Dict[str, Any] = {}

    class Decorator:
        @classmethod
        def get_setting(cls, method):
            def updated_func(self):
                return self._get_setting(method.__name__)
            return updated_func

        @classmethod
        def set_setting(cls, method):
            def updated_func(self, value):
                return self._set_setting(method.__name__, value)
            return updated_func

    def __init__(self):
        self._loaded_file = ""  # Will be correctly setup when loading the config

        # We populate the object with the configuration
        local_settings_file = (Path.cwd() / SIMULAQRON_SETTINGS_FILENAME).resolve()
        if local_settings_file.exists() and local_settings_file.is_file():
            self._loaded_file = str(local_settings_file)
            self.load_from_file(local_settings_file)
        else:
            self.default_settings()

    def update_settings(self, config: Dict[str, Any]):
        # Update the config with the given data
        if "network_config_file" in config:
            # We need to resolve the path of the network config file
            given_network_config = Path(config["network_config_file"]).resolve()
            if given_network_config.exists() and given_network_config.is_file():
                config["network_config_file"] = str(given_network_config)
            else:
                # If it doesn't exist, we load the default
                resource = resources.files(simulaqron._default_config).joinpath("default_network.json")
                network_path = Path(str(resource)).resolve()
                assert network_path.exists() and network_path.is_file()
                config["network_config_file"] = str(network_path)
            config["sim_backend"] = SimBackend[config["sim_backend"].upper()]
        self._config.update(config)

    def default_settings(self):
        default_settings_path = resources.files(simulaqron._default_config).joinpath("default_settings.json")
        self._loaded_file = str(default_settings_path)
        self.load_from_file(Path(self._loaded_file))

    def load_from_file(self, path: PathLike):
        file_path = Path(str(path)).resolve()
        if file_path.exists() and file_path.is_file():
            self._loaded_file = str(file_path)
            with open(file_path, 'r') as file:
                config = json.load(file)
                self.update_settings(config)
        else:
            raise FileNotFoundError(f"File {file_path} does not exist or is not a file")

    def _get_setting(self, setting: str) -> Any:
        try:
            value = self._config[setting]
        except KeyError:
            raise KeyError(f"Cannot find the setting {setting} in the file {self._loaded_file}")
        return value

    def _set_setting(self, setting: str, value: Any):
        self._config[setting] = value

    # Below are the settings, note that _get_setting and _set_setting are automatically
    # called when a setting is set or get.

    @property
    @Decorator.get_setting
    def _read_user(self) -> bool:
        pass

    @_read_user.setter
    @Decorator.set_setting
    def _read_user(self, _read_user: bool):
        pass

    @property
    @Decorator.get_setting
    def sim_backend(self) -> SimBackend:
        pass

    @sim_backend.setter
    @Decorator.set_setting
    def sim_backend(self, sim_backend: SimBackend):
        pass

    @property
    @Decorator.get_setting
    def max_qubits(self) -> int:
        pass

    @max_qubits.setter
    @Decorator.set_setting
    def max_qubits(self, max_qubits: int):
        pass

    @property
    @Decorator.get_setting
    def max_registers(self) -> int:
        pass

    @max_registers.setter
    @Decorator.set_setting
    def max_registers(self, max_registers: int):
        pass

    @property
    @Decorator.get_setting
    def conn_retry_time(self: float):
        pass

    @conn_retry_time.setter
    @Decorator.set_setting
    def conn_retry_time(self, conn_retry_time: float):
        pass

    @property
    @Decorator.get_setting
    def recv_timeout(self) -> int:
        pass

    @recv_timeout.setter
    @Decorator.set_setting
    def recv_timeout(self, recv_timeout: int):
        pass

    @property
    @Decorator.get_setting
    def recv_retry_time(self) -> float:
        pass

    @recv_retry_time.setter
    @Decorator.set_setting
    def recv_retry_time(self, recv_retry_time: float):
        pass

    @property
    @Decorator.get_setting
    def log_level(self) -> int:
        pass

    @log_level.setter
    @Decorator.set_setting
    def log_level(self, log_level: int):
        pass

    @property
    @Decorator.get_setting
    def network_config_file(self) -> str:
        pass

    @network_config_file.setter
    @Decorator.set_setting
    def network_config_file(self, app_file: str):
        pass

    @property
    @Decorator.get_setting
    def noisy_qubits(self) -> bool:
        pass

    @noisy_qubits.setter
    @Decorator.set_setting
    def noisy_qubits(self, noisy_qubits_: bool):
        pass

    @property
    @Decorator.get_setting
    def t1(self) -> float:
        pass

    @t1.setter
    @Decorator.set_setting
    def t1(self, t1: float):
        pass


simulaqron_settings = Config()

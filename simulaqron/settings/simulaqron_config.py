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
from os import PathLike
from pathlib import Path
from typing import Self

from dataclasses_serialization.json import JSONSerializer
from dataclasses_serialization.json import JSONSerializerMixin

# Some helpers paths that point to the usual locations where the
# configurations can reside:
DEFAULT_SIMULAQRON_SETTINGS_FILENAME = "simulaqron_settings.json"
LOCAL_SIMULAQRON_SETTINGS = (Path.cwd() / DEFAULT_SIMULAQRON_SETTINGS_FILENAME).resolve()
HOME_SIMULAQRON_SETTINGS = (Path.home() / ".simulaqron" / DEFAULT_SIMULAQRON_SETTINGS_FILENAME).resolve()


class SimBackend(JSONSerializerMixin, Enum):
    """
    Enum used to list the supported SimulaQron backends.
    """
    STABILIZER = "stabilizer"
    PROJECTQ = "projectq"
    QUTIP = "qutip"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


@dataclass
class SimulaqronConfig(JSONSerializerMixin):
    """
    Holds the general SimulaQron config.
    """
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

    @classmethod
    def _create_home_settings_folder(cls):
        home_setting_folder = (Path.home() / ".simulaqron").resolve()
        home_setting_folder.mkdir(parents=True, exist_ok=True)

    def read_from_file(self, file_path: Path | str):
        """
        Reads the SimulaQron configuration from the given file path.
        :param file_path:  A `pathlib.Path` or `str` representing the file path to read the configurations from.
        :type file_path: Path | str
        """
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
    def read_from_known_sources(cls) -> Self:
        """
        Reads the SimulaQron configuration from usual locations.
        This method will try to load the configuration files *in the following order* from (1)
        the current folder (`./simulaqron_settings.json`) and, (2) simulaqron settings in the
        user's home folder (`~/.simulaqron/simulaqron_settings.json`).

        If none of these files exists, this method will create a SimulaQron configuration in
        user's home folder (`~/.simulaqron/simulaqron_settings.json`) containing the default
        SimulaQron configuration.

        To check the default configuration, check the documentation of `default_settings`.
        See Also: :py:meth:`default_settings`
        """
        cwd_settings_file = LOCAL_SIMULAQRON_SETTINGS.resolve()
        home_settings_file = HOME_SIMULAQRON_SETTINGS.resolve()

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
        new_default_config.write_to_file(home_settings_file)
        return new_default_config

    def default_settings(self):
        """
        Resets the current SimulaQron configuration object to its default configuration set.
        The default configuration is:
        * max_qubits = 20
        * max_registers = 1000
        * conn_retry_time = 0.5
        * conn_max_retries = 10
        * recv_timeout = 100
        * recv_retry_time = 0.1
        * recv_max_retries = 10
        * log_level = logging.WARNING
        * sim_backend = SimBackend.STABILIZER
        * noisy_qubits = False
        * max_app_waiting_time = -1.0  # In seconds, negative means unlimited waiting
        * t1: float = 1.0
        """
        default_config = SimulaqronConfig()
        cls_fields = fields(self.__class__)

        for field in cls_fields:
            new_val = getattr(default_config, field.name)
            setattr(self, field.name, new_val)

    def write_to_file(self, path: PathLike):
        """
        Writes the current in-memory configuration (`simulaqron_config`) to the given file path.
        :param path:A `PathLike` object (even a string) representing the path to write the configuration to.
        :type path: PathLike
        """
        file_path = Path(str(path)).resolve()

        # Create all the parent folder if they not exists
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)

        # Poke the file, so it exists before opening
        file_path.touch(exist_ok=True)

        with file_path.open("wt") as file:
            serialized = JSONSerializer.serialize(self)
            json.dump(serialized, file, indent=4)

def get_default_simulaqron_config_file():
    """
    Get the simulaqron config file path to use.
    
    :return: Path to the simulaqron config file.
    :rtype: Path
    """
    # Implements using the local directory setting as a priority
    if LOCAL_SIMULAQRON_SETTINGS.exists():
        return LOCAL_SIMULAQRON_SETTINGS
    if HOME_SIMULAQRON_SETTINGS.exists():
        return HOME_SIMULAQRON_SETTINGS

    from . import simulaqron_settings

    # Create default in HOME (matches load_from_known_sources behavior)
    # XXX I have mixed feelings we should do this, but I leave it for now
    simulaqron_settings.default_settings()
    HOME_SIMULAQRON_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    simulaqron_settings.write_to_file(HOME_SIMULAQRON_SETTINGS)
    return HOME_SIMULAQRON_SETTINGS


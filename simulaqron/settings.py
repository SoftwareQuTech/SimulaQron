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
import os
import json
import logging
from enum import Enum

from simulaqron.toolbox import get_simulaqron_path

simulaqron_path = get_simulaqron_path.main()
config_folder = os.path.join(simulaqron_path, "config")


class SimBackend(Enum):
    STABILIZER = "stabilizer"
    PROJECTQ = "projectq"
    QUTIP = "qutip"


class Config:
    simulaqron_path = get_simulaqron_path.main()
    config_folder = os.path.join(simulaqron_path, "config")

    _internal_settings_file = os.path.join(simulaqron_path, "config", "settings.json")
    _user_settings_file = os.path.join(os.path.expanduser("~"), ".simulaqron.json")

    # Dictionary for settings
    _config = {}

    _default_config = {
        "_read_user": True,
        "max_qubits": 20,
        "max_registers": 1000,
        "conn_retry_time": 0.5,
        "recv_timeout": 100,  # (x 100 ms)
        "recv_retry_time": 0.1,  # (seconds)
        "log_level": logging.WARNING,
        "sim_backend": SimBackend.STABILIZER.value,
        "network_config_file": os.path.join(config_folder, "network.json"),
        "noisy_qubits": False,
        "t1": 1.0
    }

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
        self.update_settings()

    def update_settings(self, default=False):
        # Update with default settings
        self._config.update(self._default_config)

        # Update with internal settings (if exists and default is False)
        if not default:
            if os.path.exists(self._internal_settings_file):
                with open(self._internal_settings_file, 'r') as f:
                    internal_config = json.load(f)
                    self._config.update(internal_config)
            else:
                self._write()

            # Update with internal settings (if exists and _read_user is True)
            if self._read_user:
                if os.path.exists(self._user_settings_file):
                    with open(self._user_settings_file, 'r') as f:
                        user_config = json.load(f)
                        self._config.update(user_config)

    def default_settings(self):
        self.update_settings(default=True)
        self._write()

    def _write(self):
        with open(self._internal_settings_file, 'w') as f:
            json.dump(self._config, f, indent=4)

    def _get_setting(self, setting):
        try:
            value = self._config[setting]
        except KeyError:
            raise KeyError("Cannot find the setting {} in the file {}".format(setting, self._internal_settings_file))
        return value

    def _set_setting(self, setting, value):
        self._config[setting] = value
        self._write()

    # Below are the settings, note that _get_setting and _set_setting are automaticaly
    # called when a setting is set or get. When a value is set the values is saved to the
    # settings (json) file using the name of the property as key.

    @property
    @Decorator.get_setting
    def _read_user(self):
        pass

    @_read_user.setter
    @Decorator.set_setting
    def _read_user(self, _read_user):
        pass

    @property
    @Decorator.get_setting
    def sim_backend(self):
        pass

    @sim_backend.setter
    @Decorator.set_setting
    def sim_backend(self, sim_backend):
        pass

    @property
    @Decorator.get_setting
    def max_qubits(self):
        pass

    @max_qubits.setter
    @Decorator.set_setting
    def max_qubits(self, max_qubits):
        pass

    @property
    @Decorator.get_setting
    def max_registers(self):
        pass

    @max_registers.setter
    @Decorator.set_setting
    def max_registers(self, max_registers):
        pass

    @property
    @Decorator.get_setting
    def conn_retry_time(self):
        pass

    @conn_retry_time.setter
    @Decorator.set_setting
    def conn_retry_time(self, conn_retry_time):
        pass

    @property
    @Decorator.get_setting
    def recv_timeout(self):
        pass

    @recv_timeout.setter
    @Decorator.set_setting
    def recv_timeout(self, recv_timeout):
        pass

    @property
    @Decorator.get_setting
    def recv_retry_time(self):
        pass

    @recv_retry_time.setter
    @Decorator.set_setting
    def recv_retry_time(self, recv_retry_time):
        pass

    @property
    @Decorator.get_setting
    def log_level(self):
        pass

    @log_level.setter
    @Decorator.set_setting
    def log_level(self, log_level):
        pass

    @property
    @Decorator.get_setting
    def network_config_file(self):
        pass

    @network_config_file.setter
    @Decorator.set_setting
    def network_config_file(self, app_file):
        pass

    @property
    @Decorator.get_setting
    def noisy_qubits(self):
        pass

    @noisy_qubits.setter
    @Decorator.set_setting
    def noisy_qubits(self, noisy_qubits):
        pass

    @property
    @Decorator.get_setting
    def t1(self):
        pass

    @t1.setter
    @Decorator.set_setting
    def t1(self, t1):
        pass


simulaqron_settings = Config()

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
import logging
import json

import os

from simulaqron.toolbox import get_simulaqron_path

simulaqron_path = get_simulaqron_path.main()
config_folder = os.path.join(simulaqron_path, "config")


# class _DefaultSettings:
#     CONF_MAXQUBITS = 20
#     CONF_MAXREGS = 1000
#     CONF_WAIT_TIME = 0.5
#     CONF_RECV_TIMEOUT = 100  # (x 100 ms)
#     CONF_RECV_EPR_TIMEOUT = 100  # (x 100 ms)
#     CONF_WAIT_TIME_RECV = 0.1  # (seconds)
#     CONF_LOGGING_LEVEL_BACKEND = logging.WARNING
#     CONF_LOGGING_LEVEL_FRONTEND = logging.WARNING
#     CONF_BACKEND = "stabilizer"
#     CONF_APP_FILE = os.path.join(config_folder, "appNodes.cfg")
#     CONF_CQC_FILE = os.path.join(config_folder, "cqcNodes.cfg")
#     CONF_VNODE_FILE = os.path.join(config_folder, "virtualNodes.cfg")
#     CONF_NODES_FILE = os.path.join(config_folder, "Nodes.cfg")
#     CONF_TOPOLOGY_FILE = ""
#     CONF_NOISY_QUBITS = False
#     CONF_T1 = 1


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
        "backend": "stabilizer",
        "app_file": os.path.join(config_folder, "appNodes.cfg"),
        "cqc_file": os.path.join(config_folder, "cqcNodes.cfg"),
        "vnode_file": os.path.join(config_folder, "virtualNodes.cfg"),
        "nodes_file": os.path.join(config_folder, "Nodes.cfg"),
        "topology_file": "",
        "noisy_qubits": False,
        "t1": 1
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
    def backend(self):
        pass

    @backend.setter
    @Decorator.set_setting
    def backend(self, backend):
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
    def topology_file(self):
        pass

    @topology_file.setter
    @Decorator.set_setting
    def topology_file(self, topology_file):
        pass

    @property
    @Decorator.get_setting
    def app_file(self):
        pass

    @app_file.setter
    @Decorator.set_setting
    def app_file(self, app_file):
        pass

    @property
    @Decorator.get_setting
    def cqc_file(self):
        pass

    @cqc_file.setter
    @Decorator.set_setting
    def cqc_file(self, cqc_file):
        pass

    @property
    @Decorator.get_setting
    def vnode_file(self):
        pass

    @vnode_file.setter
    @Decorator.set_setting
    def vnode_file(self, vnode_file):
        pass

    @property
    @Decorator.get_setting
    def nodes_file(self):
        pass

    @nodes_file.setter
    @Decorator.set_setting
    def nodes_file(self, nodes_file):
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

# class Settings:
#     # Get path to SimulaQron folder
#     simulaqron_path = get_simulaqron_path.main()
#
#     _settings_file = os.path.join(simulaqron_path, "config/settings.ini")
#     _config = ConfigParser()
#
#     # default settings for if file is not ready yet
#     max_qubits = _DefaultSettings.CONF_MAXQUBITS
#     max_registers = _DefaultSettings.CONF_MAXREGS
#     conn_retry_time = _DefaultSettings.CONF_WAIT_TIME
#     recv_timeout = _DefaultSettings.CONF_RECV_TIMEOUT
#     recv_retry_time = _DefaultSettings.CONF_WAIT_TIME_RECV
#     log_level = _DefaultSettings.CONF_LOGGING_LEVEL_BACKEND
#     backend = _DefaultSettings.CONF_BACKEND
#     topology_file = _DefaultSettings.CONF_TOPOLOGY_FILE
#     app_file = _DefaultSettings.CONF_APP_FILE
#     cqc_file = _DefaultSettings.CONF_CQC_FILE
#     vnode_file = _DefaultSettings.CONF_VNODE_FILE
#     nodes_file = _DefaultSettings.CONF_NODES_FILE
#     noisy_qubits = _DefaultSettings.CONF_NOISY_QUBITS
#     t1 = _DefaultSettings.CONF_T1
#
#     log_levels = {
#         "info": logging.INFO,
#         "debug": logging.DEBUG,
#         "warning": logging.WARNING,
#         "error": logging.ERROR,
#         "critical": logging.CRITICAL
#     }
#
#     @classmethod
#     def init_settings(cls):
#
#         _config = cls._config
#         _config.read(cls._settings_file)
#
#         config_changed = False
#
#         if "BACKEND" not in _config:
#             _config['BACKEND'] = {}
#         backend = _config['BACKEND']
#
#         if "MaxQubits_Per_Node" in backend:
#             cls.max_qubits = int(backend['MaxQubits_Per_Node'])
#         else:
#             _config['BACKEND']['MaxQubits_Per_Node'] = str(cls.max_qubits)
#             config_changed = True
#
#         if "MaxRegisters_Per_Node" in backend:
#             cls.max_registers = int(backend['MaxRegisters_Per_Node'])
#         else:
#             _config['BACKEND']['MaxRegisters_Per_Node'] = str(cls.max_registers)
#             config_changed = True
#
#         if "WaitTime" in backend:
#             cls.conn_retry_time = float(backend['WaitTime'])
#         else:
#             backend['WaitTime'] = str(cls.conn_retry_time)
#             config_changed = True
#
#         if "RecvTimeout" in backend:
#             cls.recv_timeout = float(backend['RecvTimeout'])
#         else:
#             backend['RecvTimeout'] = str(cls.recv_timeout)
#             config_changed = True
#
#         if "RecvEPRTimeout" in backend:
#             cls.CONF_RECV_EPR_TIMEOUT = float(backend['RecvEPRTimeout'])
#         else:
#             backend['RecvEPRTimeout'] = str(cls.CONF_RECV_EPR_TIMEOUT)
#             config_changed = True
#
#         if "WaitTimeRecv" in backend:
#             cls.recv_retry_time = float(backend['WaitTimeRecv'])
#         else:
#             backend['WaitTimeRecv'] = str(cls.recv_retry_time)
#             config_changed = True
#
#         if "LogLevel" in backend:
#             _log_level = backend['LogLevel'].lower()
#             if _log_level in cls.log_levels:
#                 cls.log_level = cls.log_levels[_log_level]
#             else:
#                 backend['LogLevel'] = list(cls.log_levels.keys())[
#                     list(cls.log_levels.values()).index(cls.log_level)]
#
#         else:
#             backend['LogLevel'] = list(cls.log_levels.keys())[
#                 list(cls.log_levels.values()).index(cls.log_level)]
#             config_changed = True
#
#         if "Backend" in backend:
#             cls.backend = backend["backend"]
#         else:
#             backend["backend"] = cls.backend
#             config_changed = True
#
#         if "Topology_File" in backend:
#             cls.topology_file = backend['Topology_File']
#         else:
#             backend['Topology_File'] = cls.topology_file
#             config_changed = True
#
#         if "App_File" in backend:
#             cls.app_file = backend['App_File']
#         else:
#             backend['App_File'] = cls.app_file
#             config_changed = True
#
#         if "Cqc_File" in backend:
#             cls.cqc_file = backend['Cqc_File']
#         else:
#             backend['Cqc_File'] = cls.cqc_file
#             config_changed = True
#
#         if "Vnode_File" in backend:
#             cls.vnode_file = backend['Vnode_File']
#         else:
#             backend['Vnode_File'] = cls.vnode_file
#             config_changed = True
#
#         if "Nodes_File" in backend:
#             cls.nodes_file = backend['Nodes_File']
#         else:
#             backend['Nodes_File'] = cls.nodes_file
#             config_changed = True
#
#         if "noisy_qubits" in backend:
#             cls.noisy_qubits = backend['noisy_qubits'] == 'True'
#         else:
#             backend['noisy_qubits'] = str(cls.noisy_qubits)
#             config_changed = True
#
#         if "T1" in backend:
#             cls.t1 = float(backend['T1'])
#         else:
#             backend['T1'] = str(cls.t1)
#             config_changed = True
#
#         if "FRONTEND" not in _config:
#             _config['FRONTEND'] = {}
#         frontend = _config['FRONTEND']
#
#         if "LogLevel" in frontend:
#             _log_level = frontend['LogLevel'].lower()
#             if _log_level in cls.log_levels:
#                 cls.CONF_LOGGING_LEVEL_FRONTEND = cls.log_levels[_log_level]
#             else:
#                 frontend['LogLevel'] = list(cls.log_levels.keys())[
#                     list(cls.log_levels.values()).index(cls.CONF_LOGGING_LEVEL_FRONTEND)]
#
#         else:
#             frontend['LogLevel'] = list(cls.log_levels.keys())[
#                 list(cls.log_levels.values()).index(cls.CONF_LOGGING_LEVEL_FRONTEND)]
#             config_changed = True
#
#         if config_changed:
#             cls.save_settings()
#
#     @classmethod
#     def save_settings(cls):
#         with open(cls._settings_file, 'w') as file:
#             cls._config.write(file)
#
#     @classmethod
#     def set_setting(cls, section, key, value):
#         cls._config[section][key] = value
#         cls.save_settings()
#
#     @classmethod
#     def default_settings(cls):
#         cls.max_qubits = _DefaultSettings.CONF_MAXQUBITS
#         cls.max_registers = _DefaultSettings.CONF_MAXREGS
#         cls.conn_retry_time = _DefaultSettings.CONF_WAIT_TIME
#         cls.log_level = _DefaultSettings.CONF_LOGGING_LEVEL_BACKEND
#         cls.CONF_LOGGING_LEVEL_FRONTEND = _DefaultSettings.CONF_LOGGING_LEVEL_FRONTEND
#         cls.backend = _DefaultSettings.CONF_BACKEND
#         cls.topology_file = _DefaultSettings.CONF_TOPOLOGY_FILE
#         cls.noisy_qubits = _DefaultSettings.CONF_NOISY_QUBITS
#         cls.t1 = _DefaultSettings.CONF_T1
#
#         if os.path.exists(cls._settings_file):
#             os.remove(cls._settings_file)
#
#         cls._config = ConfigParser()
#         cls.init_settings()
#         cls.save_settings()
#
#
#
# Settings.init_settings()

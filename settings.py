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
from configparser import ConfigParser

import os

from SimulaQron.cqc.backend.cqcLogMessageHandler import CQCLogMessageHandler
from SimulaQron.cqc.backend.cqcMessageHandler import SimulaqronCQCHandler


class Settings:
    _settings_file = os.environ["NETSIM"] + "/config/settings.ini"
    _config = ConfigParser()

    # default settings for if file is not ready yet
    CONF_MAXQUBITS = 20
    CONF_MAXREGS = 1000
    CONF_WAIT_TIME = 0.5
    CONF_LOGGING_LEVEL_BACKEND = logging.WARNING
    CONF_LOGGING_LEVEL_FRONTEND = logging.WARNING
    CONF_BACKEND_HANDLER = SimulaqronCQCHandler
    CONF_BACKEND = "projectq"
    CONF_TOPOLOGY_FILE = ""
    CONF_NOISY_QUBITS = False
    CONF_T1 = 1

    @classmethod
    def init_settings(cls):

        _log_levels = {
            "info": logging.INFO,
            "debug": logging.DEBUG,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        _config = cls._config
        _config.read(cls._settings_file)

        config_changed = False

        if "BACKEND" not in _config:
            _config["BACKEND"] = {}
        backend = _config["BACKEND"]

        if "MaxQubits_Per_Node" in backend:
            cls.CONF_MAXQUBITS = int(backend["MaxQubits_Per_Node"])
        else:
            _config["BACKEND"]["MaxQubits_Per_Node"] = str(cls.CONF_MAXQUBITS)
            config_changed = True

        if "MaxRegisters_Per_Node" in backend:
            cls.CONF_MAXREGS = int(backend["MaxRegisters_Per_Node"])
        else:
            _config["BACKEND"]["MaxRegisters_Per_Node"] = str(cls.CONF_MAXREGS)
            config_changed = True

        if "WaitTime" in backend:
            cls.CONF_WAIT_TIME = float(backend["WaitTime"])
        else:
            backend["WaitTime"] = str(cls.CONF_WAIT_TIME)
            config_changed = True

        if "LogLevel" in backend:
            _log_level = backend["LogLevel"].lower()
            if _log_level in _log_levels:
                cls.CONF_LOGGING_LEVEL_BACKEND = _log_levels[_log_level]
            else:
                backend["LogLevel"] = list(_log_levels.keys())[
                    list(_log_levels.values()).index(cls.CONF_LOGGING_LEVEL_BACKEND)
                ]

        else:
            backend["LogLevel"] = list(_log_levels.keys())[
                list(_log_levels.values()).index(cls.CONF_LOGGING_LEVEL_BACKEND)
            ]
            config_changed = True

        if "BackendHandler" in backend:
            _backend_handler = backend["BackendHandler"]
        else:
            backend["BackendHandler"] = "simulaqron"
            _backend_handler = backend["BackendHandler"]
            config_changed = True

        if _backend_handler.lower() == "log":
            cls.CONF_BACKEND_HANDLER = CQCLogMessageHandler
        else:  # default simulqron  (elif backend_handler.lower() == "simulqron")
            cls.CONF_BACKEND_HANDLER = SimulaqronCQCHandler

        if "Backend" in backend:
            cls.CONF_BACKEND = backend["backend"]
        else:
            backend["backend"] = cls.CONF_BACKEND
            config_changed = True

        if "Topology_File" in backend:
            cls.CONF_TOPOLOGY_FILE = backend["Topology_File"]
        else:
            backend["Topology_File"] = cls.CONF_TOPOLOGY_FILE
            config_changed = True

        if "noisy_qubits" in backend:
            cls.CONF_NOISY_QUBITS = backend["noisy_qubits"] == "True"
        else:
            backend["noisy_qubits"] = str(cls.CONF_NOISY_QUBITS)
            config_changed = True

        if "T1" in backend:
            cls.CONF_T1 = float(backend["T1"])
        else:
            backend["T1"] = str(cls.CONF_T1)
            config_changed = True

        if "FRONTEND" not in _config:
            _config["FRONTEND"] = {}
        frontend = _config["FRONTEND"]

        if "LogLevel" in frontend:
            _log_level = frontend["LogLevel"].lower()
            if _log_level in _log_levels:
                cls.CONF_LOGGING_LEVEL_FRONTEND = _log_levels[_log_level]
            else:
                frontend["LogLevel"] = list(_log_levels.keys())[
                    list(_log_levels.values()).index(cls.CONF_LOGGING_LEVEL_FRONTEND)
                ]

        else:
            frontend["LogLevel"] = list(_log_levels.keys())[
                list(_log_levels.values()).index(cls.CONF_LOGGING_LEVEL_FRONTEND)
            ]
            config_changed = True

        if config_changed:
            cls.save_settings()

    @classmethod
    def save_settings(cls):
        with open(cls._settings_file, "w") as file:
            cls._config.write(file)

    @classmethod
    def set_setting(cls, section, key, value):
        cls._config[section][key] = value
        cls.save_settings()


Settings.init_settings()

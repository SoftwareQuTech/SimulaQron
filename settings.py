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

from cqc.backend.cqcLogMessageHandler import CQCLogMessageHandler
from cqc.backend.cqcMessageHandler import SimulaqronCQCHandler


class Settings:
	_settings_file = os.environ["NETSIM"] + "/config/settings.ini"

	_log_levels = {
		"info": logging.INFO,
		"debug": logging.DEBUG,
		"warning": logging.WARNING,
		"error": logging.ERROR,
		"critical": logging.CRITICAL
	}
	_config = ConfigParser()
	_config.read(_settings_file)
	CONF_MAXQUBITS = int(_config['BACKEND']['MaxQubits'])
	CONF_MAXREGS = int(_config['BACKEND']['MaxRegisters'])
	CONF_WAIT_TIME = float(_config['BACKEND']['WaitTime'])
	_log_level = _config['BACKEND']['LogLevel'].lower()
	try:
		CONF_LOGGING_LEVEL_BACKEND = _log_levels[_log_level]
	except KeyError:
		CONF_LOGGING_LEVEL_BACKEND = logging.DEBUG
	_log_level = _config['FRONTEND']['LogLevel'].lower()
	try:
		CONF_LOGGING_LEVEL_FRONTEND = _log_levels[_log_level]
	except KeyError:
		CONF_LOGGING_LEVEL_FRONTEND = logging.DEBUG

	_backend_handler = _config['BACKEND']['BackendHandler']
	if _backend_handler.lower() == 'log':
		CONF_BACKEND_HANDLER = CQCLogMessageHandler
	else:  # default simulqron  (elif backend_handler.lower() == "simulqron")
		CONF_BACKEND_HANDLER = SimulaqronCQCHandler

	@classmethod
	def save_settings(cls):
		with open(cls._settings_file, 'w') as file:
			cls._config.write(file)

	@classmethod
	def set_setting(cls, section, key, value):
		cls._config[section][key] = value
		cls.save_settings()

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
	_config = ConfigParser()

	@classmethod
	def init_settings(cls):

		_log_levels = {
			"info": logging.INFO,
			"debug": logging.DEBUG,
			"warning": logging.WARNING,
			"error": logging.ERROR,
			"critical": logging.CRITICAL
		}
		_config = cls._config
		_config.read(cls._settings_file)

		if "BACKEND" not in _config:
			_config['BACKEND'] = {}
		if "FRONTEND" not in _config:
			_config['FRONTEND'] = {}

		try:
			cls.CONF_MAXQUBITS = int(_config['BACKEND']['MaxQubits'])
		except KeyError:
			_config['BACKEND']['MaxQubits'] = str(20)
			cls.CONF_MAXQUBITS = int(_config['BACKEND']['MaxQubits'])
		try:
			cls.CONF_MAXREGS = int(_config['BACKEND']['MaxRegisters'])
		except KeyError:
			_config['BACKEND']['MaxRegisters'] = str(1000)
			cls.CONF_MAXREGS = int(_config['BACKEND']['MaxRegisters'])

		try:
			cls.CONF_WAIT_TIME = float(_config['BACKEND']['WaitTime'])
		except KeyError:
			_config['BACKEND']['WaitTime'] = "0.5"
			cls.CONF_WAIT_TIME = float(_config['BACKEND']['WaitTime'])

		try:
			_log_level = _config['BACKEND']['LogLevel'].lower()
		except KeyError:
			_config['BACKEND']['LogLevel'] = "debug"
			_log_level = _config['BACKEND']['LogLevel'].lower()
		try:
			cls.CONF_LOGGING_LEVEL_BACKEND = _log_levels[_log_level]
		except KeyError:
			cls.CONF_LOGGING_LEVEL_BACKEND = logging.DEBUG

		try:
			_log_level = _config['FRONTEND']['LogLevel'].lower()
		except KeyError:
			_config['FRONTEND']['LogLevel'] = "debug"
			_log_level = _config['FRONTEND']['LogLevel'].lower()

		try:
			cls.CONF_LOGGING_LEVEL_FRONTEND = _log_levels[_log_level]
		except KeyError:
			cls.CONF_LOGGING_LEVEL_FRONTEND = logging.DEBUG
		try:
			_backend_handler = _config['BACKEND']['BackendHandler']
		except KeyError:
			_config['BACKEND']['BackendHandler'] = "simulaqron"
			_backend_handler = _config['BACKEND']['BackendHandler']

		if _backend_handler.lower() == 'log':
			cls.CONF_BACKEND_HANDLER = CQCLogMessageHandler
		else:  # default simulqron  (elif backend_handler.lower() == "simulqron")
			cls.CONF_BACKEND_HANDLER = SimulaqronCQCHandler

		cls.save_settings()

	@classmethod
	def save_settings(cls):
		with open(cls._settings_file, 'w') as file:
			cls._config.write(file)

	@classmethod
	def set_setting(cls, section, key, value):
		cls._config[section][key] = value
		cls.save_settings()


Settings.init_settings()

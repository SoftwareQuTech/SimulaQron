import tempfile
import json
import pytest
from dataclasses_serialization.json import JSONSerializer
from pathlib import Path

from simulaqron.settings import simulaqron_settings
from simulaqron.settings.simulaqron_config import SimulaqronConfig


class TestSettings:
    def test_default_settings(self):
        __expected_default_settings = """
        {
            "max_qubits": 20,
            "max_registers": 1000,
            "conn_retry_time": 0.5,
            "conn_max_retries": 10,
            "recv_timeout": 100,
            "recv_retry_time": 0.1,
            "recv_max_retries": 10,
            "log_level": 30,
            "sim_backend": "stabilizer",
            "network_config_file": "HOME_SETTINGS_PATH",
            "noisy_qubits": false,
            "t1": 1.0
        }
        """
        expected_settings_dict = json.loads(__expected_default_settings)
        path = (Path.home() / ".simulaqron" / "default_network.json").resolve()
        expected_settings_dict["network_config_file"] = str(path)
        expected_settings = JSONSerializer.deserialize(SimulaqronConfig, expected_settings_dict)

        assert simulaqron_settings == expected_settings

    def test_non_existent_network_config(self):
        _original_settings = """
        {
            "_read_user": false,
            "max_qubits": 10,
            "max_registers": 500,
            "conn_retry_time": 0.25,
            "recv_timeout": 10,
            "recv_retry_time": 0.05,
            "log_level": 30,
            "sim_backend": "projectq",
            "network_config_file": "/not/existing/network.json",
            "noisy_qubits": false,
            "t1": 2.0
        }
        """
        _expected_settings = """
        {
            "_read_user": false,
            "max_qubits": 10,
            "max_registers": 500,
            "conn_retry_time": 0.25,
            "recv_timeout": 10,
            "recv_retry_time": 0.05,
            "log_level": 30,
            "sim_backend": "projectq",
            "network_config_file": "/not/existing/network.json",
            "noisy_qubits": false,
            "t1": 2.0
        }
        """
        expected_settings_dict = json.loads(_expected_settings)
        expected_settings = JSONSerializer.deserialize(SimulaqronConfig, expected_settings_dict)

        _original_settings = json.loads(_original_settings)
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete_on_close=False) as file:
            json.dump(_original_settings, file)
            file.close()

            simulaqron_settings.load_from_file(Path(file.name))
            assert simulaqron_settings == expected_settings

    def test_load_non_existent_config_file(self):
        with pytest.raises(FileNotFoundError) as error:
            simulaqron_settings.load_from_file("/non/existent/file")
        assert "No such file or directory: '/non/existent/file'" in str(error.value)

import tempfile
import json
import pytest
from importlib import resources
from pathlib import Path

from simulaqron.settings import simulaqron_settings, SimBackend


class TestSettings:
    def test_default_settings(self):
        __expected_default_settings = """
        {
            "_read_user": true,
            "max_qubits": 20,
            "max_registers": 1000,
            "conn_retry_time": 0.5,
            "recv_timeout": 100,
            "recv_retry_time": 0.1,
            "log_level": 30,
            "sim_backend": "stabilizer",
            "network_config_file": "CHANGE_ME",
            "noisy_qubits": false,
            "t1": 1.0
        }
        """
        expected_settings = json.loads(__expected_default_settings)
        # For testing purposes, we need to "adjust" some of teh expected values:
        expected_settings["sim_backend"] =SimBackend[expected_settings["sim_backend"].upper()]
        with resources.path("simulaqron._default_config", "default_network.json") as path:
            expected_settings["network_config_file"] = str(path)

        simulaqron_settings.default_settings()
        for key, value in expected_settings.items():
            assert getattr(simulaqron_settings, key) == value

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
            "network_config_file": "CHANGE_ME",
            "noisy_qubits": false,
            "t1": 2.0
        }
        """
        expected_settings = json.loads(_expected_settings)
        # For testing purposes, we need to "adjust" some of teh expected values:
        expected_settings["sim_backend"] =SimBackend[expected_settings["sim_backend"].upper()]
        with resources.path("simulaqron._default_config", "default_network.json") as path:
            expected_settings["network_config_file"] = str(path)

        _original_settings = json.loads(_original_settings)
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete_on_close=False) as file:
            json.dump(_original_settings, file)
            file.close()

            simulaqron_settings.load_from_file(Path(file.name))
            for key, value in expected_settings.items():
                assert getattr(simulaqron_settings, key) == value

    def test_load_non_existent_config_file(self):
        with pytest.raises(FileNotFoundError) as error:
            simulaqron_settings.load_from_file("/non/existent/file")
        assert "File /non/existent/file does not exist" in str(error.value)
